import os

from dotenv import load_dotenv


load_dotenv()


def str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default

    return value.lower() in ["true", "1", "yes", "on"]


class Settings:
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_OUTPUT_TOKENS: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2500"))
    OPENAI_TIMEOUT_SECONDS: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
    AGENT_VALIDATION_RETRIES: int = int(os.getenv("AGENT_VALIDATION_RETRIES", "1"))

    SQL_ECHO: bool = str_to_bool(os.getenv("SQL_ECHO"), default=False)
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    GOOGLE_CLIENT_ID: str | None = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/auth/google/callback",
    )

    JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    GOOGLE_SERVER_METADATA_URL: str = os.getenv(
        "GOOGLE_SERVER_METADATA_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    )

    SESSION_SECRET_KEY: str | None = os.getenv("SESSION_SECRET_KEY")

    AUTH_COOKIE_NAME: str = os.getenv("AUTH_COOKIE_NAME", "access_token")
    AUTH_COOKIE_SECURE: bool = str_to_bool(os.getenv("AUTH_COOKIE_SECURE"), default=False)
    AUTH_COOKIE_SAMESITE: str = os.getenv("AUTH_COOKIE_SAMESITE", "lax")


settings = Settings()
