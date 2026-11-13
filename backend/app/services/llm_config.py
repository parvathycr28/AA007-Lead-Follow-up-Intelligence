
import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


class LLMConfig:
    PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    ).strip()

    API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    TIMEOUT = float(os.getenv("LLM_TIMEOUT", "15"))

    @classmethod
    def is_configured(cls) -> bool:
        return (
            cls.PROVIDER == "gemini"
            and bool(cls.API_KEY)
            and bool(cls.MODEL)
        )