from __future__ import annotations

import json
import logging
from functools import lru_cache

from openai import APIConnectionError, APIError, AuthenticationError

from app.models.schemas import CodePrediction, PredictionResponse
from app.utils.config import Settings, get_settings
from ai.mapping.icd_mapper import IcdMapper, get_icd_mapper
from ai.prompts.extractor import DiagnosisExtractor, ExtractedCondition, get_extractor


logger = logging.getLogger(__name__)


class PredictionServiceError(Exception):
    """Raised when the prediction workflow cannot complete successfully."""


class PredictionService:
    def __init__(
        self,
        extractor: DiagnosisExtractor,
        mapper: IcdMapper,
    ) -> None:
        self.extractor = extractor
        self.mapper = mapper

    def predict(self, raw_text: str) -> PredictionResponse:
        normalized_text = self._normalize_text(raw_text)
        logger.info(
            "Prediction workflow started with text_length=%s, preview=%r",
            len(normalized_text),
            self._preview_text(normalized_text),
        )
        logger.info("Full normalized text sent into prediction workflow: %s", normalized_text)

        try:
            extracted_conditions = self.extractor.extract(normalized_text)
        except AuthenticationError as exc:
            logger.exception("OpenAI authentication failed during diagnosis extraction.")
            raise PredictionServiceError(
                "OpenAI authentication failed. Check the OPENAI_API_KEY in backend/.env."
            ) from exc
        except APIConnectionError as exc:
            logger.exception("OpenAI connection failed during diagnosis extraction.")
            raise PredictionServiceError(
                "Could not connect to OpenAI. Check your internet connection, proxy, or firewall settings."
            ) from exc
        except APIError as exc:
            logger.exception("OpenAI API returned an error during diagnosis extraction.")
            raise PredictionServiceError(
                f"OpenAI returned an API error: {exc.__class__.__name__}."
            ) from exc
        except json.JSONDecodeError as exc:
            logger.exception("LLM response was not valid JSON.")
            raise PredictionServiceError(
                "The LLM response was not valid JSON. Try again or tighten the output formatting."
            ) from exc
        except Exception as exc:  # pragma: no cover - safety net around external service
            logger.exception("Diagnosis extraction step failed.")
            raise PredictionServiceError("Failed to extract diagnoses from the LLM pipeline.") from exc

        logger.info(
            "Diagnosis extraction completed with extracted_count=%s, extracted_names=%s",
            len(extracted_conditions),
            [condition.name for condition in extracted_conditions],
        )
        logger.info(
            "Detailed extracted conditions after normalization: %s",
            [
                {
                    "name": condition.name,
                    "confidence": condition.confidence,
                    "evidence": condition.evidence,
                }
                for condition in extracted_conditions
            ],
        )
        mapped_codes = self.mapper.map_conditions(extracted_conditions)
        logger.info(
            "ICD mapping completed with matched_code_count=%s, matched_codes=%s",
            len(mapped_codes),
            [item["code"] for item in mapped_codes],
        )
        logger.info("Detailed ICD mapping output: %s", mapped_codes)
        explanation = self._build_explanation(extracted_conditions, mapped_codes)
        logger.info("Response explanation generated.")
        logger.info("Final explanation text: %s", explanation)

        return PredictionResponse(
            codes=[
                CodePrediction(
                    code=item["code"],
                    description=item["description"],
                    confidence=item["confidence"],
                )
                for item in mapped_codes
            ],
            explanation=explanation,
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.split())

    @staticmethod
    def _preview_text(text: str, limit: int = 80) -> str:
        if len(text) <= limit:
            return text
        return f"{text[:limit]}..."

    @staticmethod
    def _build_explanation(
        extracted_conditions: list[ExtractedCondition],
        mapped_codes: list[dict[str, str | float]],
    ) -> str:
        if mapped_codes:
            diagnoses = ", ".join(item["description"] for item in mapped_codes)
            return f"Mapped extracted conditions to ICD-10 codes for: {diagnoses}."

        if extracted_conditions:
            conditions = ", ".join(condition.name for condition in extracted_conditions)
            return (
                "Extracted possible conditions from the note but found no curated ICD-10 match "
                f"for: {conditions}."
            )

        return "No clear ICD-10 mappable conditions were identified from the provided text."


@lru_cache
def get_prediction_service() -> PredictionService:
    settings: Settings = get_settings()
    logger.info("Building prediction service dependencies.")
    extractor = get_extractor(settings)
    mapper = get_icd_mapper(settings)
    logger.info("Prediction service dependencies initialized.")
    return PredictionService(extractor=extractor, mapper=mapper)
