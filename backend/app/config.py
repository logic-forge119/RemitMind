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
    APP_ENV: str = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./remitmind.db")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    ANALYST_API_KEY: str = os.getenv("ANALYST_API_KEY", "dev-analyst")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-remitmind-jwt-secret-key-32-bytes")
    DEV_AUTH_ENABLED: bool = os.getenv("DEV_AUTH_ENABLED", "true").lower() in ("true", "1")
    RISK_REVIEW_THRESHOLD: float = float(os.getenv("RISK_REVIEW_THRESHOLD", "40.0"))
    RISK_HIGH_THRESHOLD: float = float(os.getenv("RISK_HIGH_THRESHOLD", "70.0"))
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "risk-v2.0-lgbm")
    
    # Restrictive CORS defaults (never wildcard in production)
    ALLOWED_ORIGINS: list[str] = [
        origin.strip() for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
        ).split(",") if origin.strip()
    ]

    def validate_production_secrets(self):
        """Enforces mandatory environment secrets and fails on startup if unset in production."""
        if self.APP_ENV == "production":
            missing = []
            sec = os.getenv("JWT_SECRET", "")
            if not sec or sec == "dev-remitmind-jwt-secret-key-32-bytes":
                missing.append("JWT_SECRET")
            key = os.getenv("ANALYST_API_KEY", "")
            if not key or key == "dev-analyst":
                missing.append("ANALYST_API_KEY")
            if missing:
                raise RuntimeError(
                    f"FATAL CONFIGURATION ERROR: Missing or default mandatory secrets in production: {', '.join(missing)}. "
                    f"You must set secure, non-default environment variables before starting in production mode."
                )
            if "*" in self.ALLOWED_ORIGINS:
                raise RuntimeError(
                    "FATAL SECURITY CONFIGURATION: Wildcard '*' in ALLOWED_ORIGINS is prohibited in production mode."
                )

settings = Settings()
