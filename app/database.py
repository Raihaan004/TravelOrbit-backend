from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Postgres URL from .env
DATABASE_URL = settings.DATABASE_URL

# SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# Session Local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Class for all models
Base = declarative_base()


# Dependency used in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
