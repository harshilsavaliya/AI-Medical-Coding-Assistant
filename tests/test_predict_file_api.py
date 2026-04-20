from app.models.schemas import PredictionResponse


class StubFileService:
    def predict_from_file(self, filename: str, content_type: str, file_bytes: bytes) -> PredictionResponse:
        return PredictionResponse(
            codes=[
                {
                    "code": "E11",
                    "description": "Type 2 diabetes mellitus",
                    "confidence": 0.91,
                }
            ],
            explanation=f"Processed upload: {filename}",
        )


class UnsupportedTypeService:
    def predict_from_file(self, filename: str, content_type: str, file_bytes: bytes) -> PredictionResponse:
        from app.services.file_prediction_service import UnsupportedFileTypeError

        raise UnsupportedFileTypeError("Unsupported file type. Please upload a JPG or PNG image.")


class OcrFailureService:
    def predict_from_file(self, filename: str, content_type: str, file_bytes: bytes) -> PredictionResponse:
        from app.services.file_prediction_service import OcrExtractionError

        raise OcrExtractionError("No readable text was found in the uploaded image.")


def test_predict_from_file_success(client, monkeypatch):
    from app.routes import predict as predict_route

    monkeypatch.setattr(predict_route, "get_file_prediction_service", lambda: StubFileService())
    response = client.post(
        "/predict-from-file",
        files={"file": ("note.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["codes"][0]["code"] == "E11"
    assert payload["explanation"] == "Processed upload: note.png"


def test_predict_from_file_rejects_unsupported_type(client, monkeypatch):
    from app.routes import predict as predict_route

    monkeypatch.setattr(predict_route, "get_file_prediction_service", lambda: UnsupportedTypeService())
    response = client.post(
        "/predict-from-file",
        files={"file": ("note.pdf", b"pdf-bytes", "application/pdf")},
    )

    assert response.status_code == 400


def test_predict_from_file_handles_ocr_failure(client, monkeypatch):
    from app.routes import predict as predict_route

    monkeypatch.setattr(predict_route, "get_file_prediction_service", lambda: OcrFailureService())
    response = client.post(
        "/predict-from-file",
        files={"file": ("note.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 422


def test_predict_from_file_requires_file(client):
    response = client.post("/predict-from-file")

    assert response.status_code == 422
