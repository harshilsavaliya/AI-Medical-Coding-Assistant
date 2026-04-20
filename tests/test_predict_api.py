from app.models.schemas import PredictionResponse
from app.services.prediction_service import PredictionServiceError, get_prediction_service


class StubService:
    def predict(self, text: str) -> PredictionResponse:
        return PredictionResponse(
            codes=[
                {
                    "code": "E11",
                    "description": "Type 2 diabetes mellitus",
                    "confidence": 0.92,
                }
            ],
            explanation=f"Processed: {text}",
            review_status="auto_suggested",
            extracted_conditions=[
                {
                    "name": "uncontrolled diabetes",
                    "confidence": 0.92,
                    "evidence": "uncontrolled diabetes",
                    "mapped_code": "E11",
                }
            ],
            unmatched_conditions=[],
        )


class FailingService:
    def predict(self, text: str) -> PredictionResponse:
        raise PredictionServiceError("Failed to extract diagnoses from the LLM pipeline.")


def test_predict_success(client, monkeypatch):
    app_dependency = StubService()
    get_prediction_service.cache_clear()

    from app.routes import predict as predict_route

    monkeypatch.setattr(predict_route, "get_prediction_service", lambda: app_dependency)
    response = client.post("/predict", json={"text": "Patient has uncontrolled diabetes"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["codes"][0]["code"] == "E11"
    assert payload["explanation"] == "Processed: Patient has uncontrolled diabetes"
    assert payload["review_status"] == "auto_suggested"
    assert payload["extracted_conditions"][0]["mapped_code"] == "E11"
    assert payload["unmatched_conditions"] == []


def test_predict_rejects_empty_text(client):
    response = client.post("/predict", json={"text": "   "})

    assert response.status_code == 422


def test_predict_rejects_malformed_payload(client):
    response = client.post("/predict", json={})

    assert response.status_code == 422


def test_predict_handles_service_failure(client, monkeypatch):
    get_prediction_service.cache_clear()

    from app.routes import predict as predict_route

    monkeypatch.setattr(predict_route, "get_prediction_service", lambda: FailingService())
    response = client.post("/predict", json={"text": "Patient has asthma"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to extract diagnoses from the LLM pipeline."
