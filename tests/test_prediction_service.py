from app.services.prediction_service import PredictionService
from ai.mapping.icd_mapper import IcdMapper
from ai.prompts.extractor import ExtractedCondition


class StubExtractor:
    def __init__(self, conditions):
        self.conditions = conditions

    def extract(self, clinical_text: str):
        return self.conditions


def build_mapper() -> IcdMapper:
    return IcdMapper(
        records=[
            {
                "code": "E11",
                "description": "Type 2 diabetes mellitus",
                "canonical_name": "diabetes mellitus",
                "aliases": "diabetes|type 2 diabetes|uncontrolled diabetes",
            },
            {
                "code": "I10",
                "description": "Essential hypertension",
                "canonical_name": "hypertension",
                "aliases": "hypertension|high blood pressure",
            },
            {
                "code": "J45",
                "description": "Asthma",
                "canonical_name": "asthma",
                "aliases": "asthma|bronchial asthma",
            },
            {
                "code": "R05",
                "description": "Chronic cough",
                "canonical_name": "chronic cough",
                "aliases": "chronic cough|persistent cough|cough",
            },
        ]
    )


def test_prediction_service_maps_known_conditions():
    extractor = StubExtractor(
        [
            ExtractedCondition(name="uncontrolled diabetes", confidence=0.92, evidence="diabetes"),
            ExtractedCondition(name="hypertension", confidence=0.88, evidence="hypertension"),
        ]
    )
    service = PredictionService(extractor=extractor, mapper=build_mapper())

    response = service.predict("Patient presents with uncontrolled diabetes and hypertension.")

    assert [code.code for code in response.codes] == ["E11", "I10"]
    assert "Type 2 diabetes mellitus" in response.explanation
    assert "Essential hypertension" in response.explanation


def test_prediction_service_deduplicates_codes():
    extractor = StubExtractor(
        [
            ExtractedCondition(name="diabetes", confidence=0.90, evidence="diabetes"),
            ExtractedCondition(name="uncontrolled diabetes", confidence=0.84, evidence="uncontrolled diabetes"),
        ]
    )
    service = PredictionService(extractor=extractor, mapper=build_mapper())

    response = service.predict("Patient has diabetes and uncontrolled diabetes.")

    assert len(response.codes) == 1
    assert response.codes[0].code == "E11"


def test_prediction_service_handles_unknown_terms():
    extractor = StubExtractor(
        [ExtractedCondition(name="fatigue", confidence=0.51, evidence="fatigue")]
    )
    service = PredictionService(extractor=extractor, mapper=build_mapper())

    response = service.predict("Patient reports fatigue.")

    assert response.codes == []
    assert "found no curated ICD-10 match" in response.explanation


def test_prediction_service_handles_no_conditions():
    extractor = StubExtractor([])
    service = PredictionService(extractor=extractor, mapper=build_mapper())

    response = service.predict("No significant findings.")

    assert response.codes == []
    assert response.explanation == "No clear ICD-10 mappable conditions were identified from the provided text."
