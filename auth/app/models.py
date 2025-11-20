from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timedelta
from .database import Base

class GoogleTokens(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expiry = Column(DateTime)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    register_id = Column(String, unique=True, index=True)

    email = Column(String, unique=True, nullable=True, index=True)
    google_id = Column(String, unique=True, nullable=True, index=True)

    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    location = Column(String, nullable=True)

    phone = Column(String, unique=True, nullable=False, index=True)
    auth_provider = Column(String, nullable=False)  # "phone" or "google"
    created_at = Column(DateTime, default=datetime.utcnow)

class OtpCode(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True)
    code = Column(String)
    purpose = Column(String)  # e.g., "phone_register", "google_phone_verify"
    expires_at = Column(DateTime)
    verified = Column(Boolean, default=False)
    # For normal signup
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # For Google flow
    google_id = Column(String, nullable=True)
    google_email = Column(String, nullable=True)
    google_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def default_expiry(minutes: int = 5):
        return datetime.utcnow() + timedelta(minutes=minutes)
