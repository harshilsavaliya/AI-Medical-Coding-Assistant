from __future__ import annotations

import io
import logging
from functools import lru_cache

from app.services.prediction_service import PredictionResponse, PredictionService, get_prediction_service
from app.utils.config import Settings, get_settings


logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
}


class FilePredictionServiceError(Exception):
    """Raised when file-based prediction cannot be completed."""


class OcrDependencyError(FilePredictionServiceError):
    """Raised when OCR dependencies are not installed."""


class OcrExtractionError(FilePredictionServiceError):
    """Raised when OCR extraction fails for an uploaded file."""


class UnsupportedFileTypeError(FilePredictionServiceError):
    """Raised when the uploaded file type is not supported."""


class FilePredictionService:
    def __init__(self, prediction_service: PredictionService, ocr_reader: "easyocr.Reader") -> None:
        self.prediction_service = prediction_service
        self.ocr_reader = ocr_reader

    def predict_from_file(self, filename: str, content_type: str, file_bytes: bytes) -> PredictionResponse:
        logger.info(
            "File prediction workflow started with filename=%s content_type=%s byte_count=%s",
            filename,
            content_type,
            len(file_bytes),
        )
        self._validate_upload(content_type, file_bytes)
        extracted_text = self._extract_text(file_bytes)
        logger.info(
            "OCR extraction completed with text_length=%s preview=%r",
            len(extracted_text),
            PredictionService._preview_text(extracted_text),
        )
        logger.info("Full OCR extracted text: %s", extracted_text)
        return self.prediction_service.predict(extracted_text)

    @staticmethod
    def _validate_upload(content_type: str, file_bytes: bytes) -> None:
        if not file_bytes:
            raise FilePredictionServiceError("Uploaded file is empty.")
        if content_type.lower() not in SUPPORTED_IMAGE_TYPES:
            raise UnsupportedFileTypeError("Unsupported file type. Please upload a JPG or PNG image.")

    def _extract_text(self, file_bytes: bytes) -> str:
        try:
            import numpy as np
            from PIL import Image, UnidentifiedImageError
        except ImportError as exc:
            raise OcrDependencyError(
                "OCR dependencies are missing. Install backend requirements before using file upload."
            ) from exc

        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except UnidentifiedImageError as exc:
            raise OcrExtractionError("Could not read the uploaded image.") from exc

        try:
            segments = self.ocr_reader.readtext(np.array(image), detail=0, paragraph=True)
        except Exception as exc:  # pragma: no cover - third-party OCR safeguard
            logger.exception("EasyOCR failed while processing upload.")
            raise OcrExtractionError("OCR extraction failed for the uploaded image.") from exc

        logger.info("Raw OCR segments: %s", segments)
        extracted_text = " ".join(segment.strip() for segment in segments if str(segment).strip())
        if not extracted_text:
            raise OcrExtractionError("No readable text was found in the uploaded image.")
        return extracted_text


@lru_cache
def _build_easyocr_reader(model_storage_directory: str, user_network_directory: str) -> "easyocr.Reader":
    import easyocr

    logger.info(
        "Initializing EasyOCR reader with model_storage_directory=%s user_network_directory=%s",
        model_storage_directory,
        user_network_directory,
    )
    return easyocr.Reader(
        ["en"],
        gpu=False,
        model_storage_directory=model_storage_directory,
        user_network_directory=user_network_directory,
    )


@lru_cache
def get_file_prediction_service() -> FilePredictionService:
    settings: Settings = get_settings()
    logger.info("Building file prediction service dependencies.")
    prediction_service = get_prediction_service()
    settings.easyocr_model_dir.mkdir(parents=True, exist_ok=True)
    settings.easyocr_network_dir.mkdir(parents=True, exist_ok=True)
    ocr_reader = _build_easyocr_reader(
        str(settings.easyocr_model_dir),
        str(settings.easyocr_network_dir),
    )
    logger.info("File prediction service dependencies initialized for model=%s", settings.openai_model)
    return FilePredictionService(prediction_service=prediction_service, ocr_reader=ocr_reader)
