from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    # Twilio
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM_NUMBER: str | None = None
    TWILIO_WHATSAPP_NUMBER: str | None = None

    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    # App key
    APP_SECRET_KEY: str | None = None

    # OpenRouter
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str | None = None

    # Image provider keys (optional)
    PEXELS_API_KEY: str | None = None
    UNSPLASH_ACCESS_KEY: str | None = None

    # Email (NEW)
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SENDER_EMAIL: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
