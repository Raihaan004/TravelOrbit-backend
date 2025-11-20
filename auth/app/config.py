from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    APP_SECRET_KEY: str = "change-me"

    # OpenRouter (optional - use uppercase env names for consistency)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
