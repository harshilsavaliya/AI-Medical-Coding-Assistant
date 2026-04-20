import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.schemas import PredictionRequest, PredictionResponse
from app.services.file_prediction_service import (
    FilePredictionServiceError,
    OcrDependencyError,
    OcrExtractionError,
    UnsupportedFileTypeError,
    get_file_prediction_service,
)
from app.services.prediction_service import (
    PredictionServiceError,
    get_prediction_service,
)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict(request: PredictionRequest) -> PredictionResponse:
    logger.info("Received /predict request with normalized_text_length=%s", len(request.text))
    service = get_prediction_service()

    try:
        response = service.predict(request.text)
        logger.info(
            "Prediction completed successfully with code_count=%s",
            len(response.codes),
        )
        return response
    except PredictionServiceError as exc:
        logger.exception("Prediction request failed in service layer.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/predict-from-file", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict_from_file(file: UploadFile = File(...)) -> PredictionResponse:
    logger.info(
        "Received /predict-from-file request with filename=%s content_type=%s",
        file.filename,
        file.content_type,
    )
    try:
        service = get_file_prediction_service()
        file_bytes = file.file.read()
        response = service.predict_from_file(
            filename=file.filename or "uploaded-file",
            content_type=file.content_type or "",
            file_bytes=file_bytes,
        )
        logger.info(
            "File prediction completed successfully with code_count=%s",
            len(response.codes),
        )
        return response
    except UnsupportedFileTypeError as exc:
        logger.info("Rejected unsupported upload type for filename=%s", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OcrDependencyError as exc:
        logger.exception("OCR dependencies or OCR model setup failed for filename=%s", file.filename)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OcrExtractionError as exc:
        logger.exception("OCR extraction failed for filename=%s", file.filename)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except FilePredictionServiceError as exc:
        logger.exception("File prediction request failed in service layer.")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
