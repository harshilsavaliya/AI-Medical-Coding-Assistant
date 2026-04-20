from __future__ import annotations

import csv
import logging
from functools import lru_cache

from app.utils.config import Settings
from ai.prompts.extractor import ExtractedCondition


logger = logging.getLogger(__name__)


class MappingResult:
    def __init__(
        self,
        codes: list[dict[str, str | float]],
        condition_mappings: list[dict[str, str | float | None]],
        unmatched_conditions: list[str],
    ) -> None:
        self.codes = codes
        self.condition_mappings = condition_mappings
        self.unmatched_conditions = unmatched_conditions


class IcdMapper:
    def __init__(self, records: list[dict[str, str]]) -> None:
        self.records = records

    def map_conditions(self, conditions: list[ExtractedCondition]) -> MappingResult:
        logger.info("Starting ICD mapping for condition_count=%s", len(conditions))
        results: list[dict[str, str | float]] = []
        condition_mappings: list[dict[str, str | float | None]] = []
        unmatched_conditions: list[str] = []
        seen_codes: set[str] = set()

        for condition in conditions:
            logger.info(
                "Evaluating extracted condition for mapping: name=%s confidence=%s evidence=%s",
                condition.name,
                condition.confidence,
                condition.evidence,
            )
            record = self._find_record(condition.name)
            if not record:
                logger.info("No ICD match found for extracted_condition=%s", condition.name)
                unmatched_conditions.append(condition.name)
                condition_mappings.append(
                    {
                        "name": condition.name,
                        "confidence": condition.confidence,
                        "evidence": condition.evidence,
                        "mapped_code": None,
                    }
                )
                continue

            code = record["code"]
            logger.info(
                "Mapped extracted_condition=%s to code=%s description=%s",
                condition.name,
                code,
                record["description"],
            )
            condition_mappings.append(
                {
                    "name": condition.name,
                    "confidence": condition.confidence,
                    "evidence": condition.evidence,
                    "mapped_code": code,
                }
            )

            if code in seen_codes:
                logger.info("Skipping duplicate ICD code=%s for condition=%s", code, condition.name)
                continue

            seen_codes.add(code)
            results.append(
                {
                    "code": code,
                    "description": record["description"],
                    "confidence": condition.confidence,
                }
            )

        return MappingResult(
            codes=results,
            condition_mappings=condition_mappings,
            unmatched_conditions=unmatched_conditions,
        )

    def _find_record(self, condition_name: str) -> dict[str, str] | None:
        normalized_condition = condition_name.lower()

        for record in self.records:
            aliases = [alias.strip().lower() for alias in record["aliases"].split("|") if alias.strip()]
            logger.info(
                "Checking condition=%s against record_code=%s canonical_name=%s aliases=%s",
                normalized_condition,
                record["code"],
                record["canonical_name"],
                aliases,
            )
            if normalized_condition == record["canonical_name"].lower():
                logger.info(
                    "Matched by canonical name: condition=%s code=%s",
                    normalized_condition,
                    record["code"],
                )
                return record
            if normalized_condition in aliases:
                logger.info(
                    "Matched by alias equality: condition=%s code=%s matched_alias=%s",
                    normalized_condition,
                    record["code"],
                    normalized_condition,
                )
                return record
            partial_alias = next((alias for alias in aliases if alias in normalized_condition), None)
            if partial_alias:
                logger.info(
                    "Matched by partial alias containment: condition=%s code=%s matched_alias=%s",
                    normalized_condition,
                    record["code"],
                    partial_alias,
                )
                return record

        return None


def load_icd_records(dataset_path: str) -> list[dict[str, str]]:
    with open(dataset_path, newline="", encoding="utf-8") as csv_file:
        records = list(csv.DictReader(csv_file))
    logger.info("Loaded ICD dataset from path=%s with record_count=%s", dataset_path, len(records))
    return records


@lru_cache
def _build_icd_mapper(dataset_path: str) -> IcdMapper:
    logger.info("Initializing ICD mapper with dataset_path=%s", dataset_path)
    records = load_icd_records(dataset_path)
    return IcdMapper(records=records)


def get_icd_mapper(settings: Settings) -> IcdMapper:
    return _build_icd_mapper(str(settings.icd_dataset_path))
