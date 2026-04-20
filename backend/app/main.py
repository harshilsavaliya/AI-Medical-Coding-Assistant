import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.predict import router as predict_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Medical Coding Assistant",
    version="0.1.0",
    description="Phase 1 backend MVP for text-to-ICD-10 prediction.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)

logger.info("FastAPI application initialized.")
logger.warning(
    "Verbose medical-text logging is enabled. OCR output, LLM prompts/responses, and mapping details will be written to logs."
)


@app.get("/")
def read_root() -> dict[str, str]:
    logger.info("Root health endpoint accessed.")
    return {"message": "AI Medical Coding Assistant backend is running."}
