from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.utils.config import Settings


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are a medical coding assistant focused on identifying diagnosis-like conditions from clinical text.
Return valid JSON only with this exact shape:
{
  "conditions": [
    {
      "name": "condition name",
      "confidence": 0.0,
      "evidence": "short phrase from the note"
    }
  ]
}

Rules:
- Extract only diagnosis or symptom conditions relevant for ICD-10 style coding.
- Confidence must be between 0 and 1.
- Keep names concise and normalized.
- If nothing meaningful is found, return {"conditions": []}.
""".strip()


@dataclass
class ExtractedCondition:
    name: str
    confidence: float
    evidence: str


class DiagnosisExtractor:
    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm

    def extract(self, clinical_text: str) -> list[ExtractedCondition]:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Clinical text:\n{clinical_text}"),
        ]
        logger.info(
            "Sending request to LLM extractor with text_length=%s",
            len(clinical_text),
        )
        logger.info("LLM system prompt: %s", SYSTEM_PROMPT)
        logger.info("LLM user message: %s", messages[1].content)
        response = self.llm.invoke(messages)
        logger.info("Received response from LLM extractor.")
        logger.info("Raw LLM response content: %s", response.content)

        payload = json.loads(response.content)
        logger.info("Parsed raw LLM JSON payload: %s", payload)
        conditions = payload.get("conditions", [])
        extracted: list[ExtractedCondition] = []

        for item in conditions:
            logger.info("Raw extracted condition item from LLM: %s", item)
            name = " ".join(str(item.get("name", "")).split()).lower()
            if not name:
                logger.info("Skipping extracted condition because normalized name is empty.")
                continue

            confidence_raw = item.get("confidence", 0.0)
            try:
                confidence = float(confidence_raw)
            except (TypeError, ValueError):
                logger.info(
                    "Could not parse confidence=%r for condition=%s, defaulting to 0.0",
                    confidence_raw,
                    name,
                )
                confidence = 0.0

            confidence = max(0.0, min(1.0, confidence))
            evidence = " ".join(str(item.get("evidence", "")).split())

            normalized_condition = ExtractedCondition(
                name=name,
                confidence=confidence,
                evidence=evidence,
            )
            logger.info(
                "Normalized extracted condition: name=%s confidence=%s evidence=%s",
                normalized_condition.name,
                normalized_condition.confidence,
                normalized_condition.evidence,
            )
            extracted.append(normalized_condition)

        logger.info(
            "Parsed LLM response with condition_count=%s, condition_names=%s",
            len(extracted),
            [condition.name for condition in extracted],
        )
        return extracted


@lru_cache
def _build_extractor(api_key: str, model: str) -> DiagnosisExtractor:
    logger.info("Initializing ChatOpenAI extractor with model=%s", model)
    llm = ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=0,
    )
    return DiagnosisExtractor(llm=llm)


def get_extractor(settings: Settings) -> DiagnosisExtractor:
    return _build_extractor(settings.openai_api_key, settings.openai_model)
