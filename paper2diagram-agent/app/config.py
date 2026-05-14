from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    gemini_api_key: str
    gemini_model: str = "gemini-3-pro"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout_seconds: int = 180
    gemini_connect_timeout_seconds: int = 60
    gemini_use_query_key: bool = False

    banana_api_key: str
    banana_base_url: str = "https://api.banana.dev"
    banana_model: str = "nano-banana"
    banana_timeout_seconds: int = 120
    enable_banana: bool = True



def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3-pro"),
        gemini_base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        gemini_timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "180")),
        gemini_connect_timeout_seconds=int(os.getenv("GEMINI_CONNECT_TIMEOUT_SECONDS", "60")),
        gemini_use_query_key=os.getenv("GEMINI_USE_QUERY_KEY", "").strip().lower() in {"1", "true", "yes", "on"},
        banana_api_key=os.getenv("BANANA_PRO_API_KEY", ""),
        banana_base_url=os.getenv("BANANA_PRO_BASE_URL", "https://api.banana.dev"),
        banana_model=os.getenv("BANANA_MODEL", "nano-banana"),
        banana_timeout_seconds=int(os.getenv("BANANA_TIMEOUT_SECONDS", "120")),
        enable_banana=os.getenv("ENABLE_BANANA", "true").strip().lower() in {"1", "true", "yes", "on"},
    )
