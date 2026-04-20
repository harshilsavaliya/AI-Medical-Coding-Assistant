from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    icd_dataset_path: Path = BACKEND_DIR / "data" / "icd_codes.csv"
    easyocr_model_dir: Path = BACKEND_DIR / ".cache" / "easyocr"
    easyocr_network_dir: Path = BACKEND_DIR / ".cache" / "easyocr-user-network"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
