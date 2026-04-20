from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    text: str = Field(..., description="Raw clinical text to analyze.")

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("text must not be empty")
        return normalized


class CodePrediction(BaseModel):
    code: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExtractedConditionReview(BaseModel):
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str
    mapped_code: str | None = None


class PredictionResponse(BaseModel):
    codes: list[CodePrediction]
    explanation: str
    review_status: str
    extracted_conditions: list[ExtractedConditionReview]
    unmatched_conditions: list[str]
