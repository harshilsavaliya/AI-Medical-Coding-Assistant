from app.models.schemas import PredictionResponse
from app.services.file_prediction_service import (
    FilePredictionService,
    OcrExtractionError,
    UnsupportedFileTypeError,
)


class StubPredictionService:
    def __init__(self):
        self.last_text = None

    def predict(self, text: str) -> PredictionResponse:
        self.last_text = text
        return PredictionResponse(
            codes=[
                {
                    "code": "I10",
                    "description": "Essential hypertension",
                    "confidence": 0.88,
                }
            ],
            explanation="Mapped extracted conditions to ICD-10 codes for: Essential hypertension.",
            review_status="auto_suggested",
            extracted_conditions=[
                {
                    "name": "hypertension",
                    "confidence": 0.88,
                    "evidence": "hypertension",
                    "mapped_code": "I10",
                }
            ],
            unmatched_conditions=[],
        )


class StubReader:
    def __init__(self, result=None, should_fail: bool = False):
        self.result = ["hypertension"] if result is None else result
        self.should_fail = should_fail

    def readtext(self, image, detail=0, paragraph=True):
        if self.should_fail:
            raise RuntimeError("ocr failed")
        return self.result


def test_file_prediction_service_forwards_ocr_text():
    prediction_service = StubPredictionService()
    service = FilePredictionService(prediction_service=prediction_service, ocr_reader=StubReader())

    response = service.predict_from_file(
        filename="note.png",
        content_type="image/png",
        file_bytes=(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
            b"\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
    )

    assert prediction_service.last_text == "hypertension"
    assert response.codes[0].code == "I10"


def test_file_prediction_service_rejects_unsupported_file_types():
    service = FilePredictionService(prediction_service=StubPredictionService(), ocr_reader=StubReader())

    try:
        service.predict_from_file("note.pdf", "application/pdf", b"pdf")
    except UnsupportedFileTypeError as exc:
        assert "Unsupported file type" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected UnsupportedFileTypeError")


def test_file_prediction_service_handles_empty_ocr_output():
    service = FilePredictionService(
        prediction_service=StubPredictionService(),
        ocr_reader=StubReader(result=[]),
    )

    try:
        service.predict_from_file(
            "note.png",
            "image/png",
            (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
                b"\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
        )
    except OcrExtractionError as exc:
        assert "No readable text" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected OcrExtractionError")
