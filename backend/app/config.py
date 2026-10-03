import os
from pathlib import Path

# Load .env manually or via dotenv
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./remitmind.db")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "mock-llm-key")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    ANALYST_API_KEY: str = os.getenv("ANALYST_API_KEY", "upay-risk-secret")
    RISK_REVIEW_THRESHOLD: float = float(os.getenv("RISK_REVIEW_THRESHOLD", "40.0"))
    RISK_HIGH_THRESHOLD: float = float(os.getenv("RISK_HIGH_THRESHOLD", "70.0"))
    ALLOWED_ORIGINS: list[str] = [
        origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    ]

settings = Settings()
