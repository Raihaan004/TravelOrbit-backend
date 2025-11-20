from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Date, DateTime,
    Numeric, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from auth.app.database import Base


# ---------- MAIN TRIP TABLE ----------
class Trip(Base):
    __tablename__ = "trips"

    id = Column(String, primary_key=True)  # uuid string
    register_id = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)

    # Basic details
    from_city = Column(String, nullable=True)
    to_city = Column(String, nullable=True)

    # Party details
    party_type = Column(String, nullable=True)  # solo, couple, friends, family
    adults_count = Column(Integer, nullable=True)
    children_count = Column(Integer, nullable=True)
    seniors_count = Column(Integer, nullable=True)

    # Budget + duration
    budget_level = Column(String, nullable=True)  # cheap, moderate, luxury
    duration_days = Column(Integer, nullable=True)

    # Trip dates
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Additional info
    interests = Column(JSONB, nullable=True)  # list of interests
    special_requirements = Column(Text, nullable=True)

    # AI summary output
    title = Column(String, nullable=True)
    ai_summary_text = Column(Text, nullable=True)
    ai_summary_json = Column(JSONB, nullable=True)

    # Calendar sync
    google_calendar_event_id = Column(String, nullable=True)

    status = Column(String, default="draft")  # draft, planned, paid, cancelled
    total_price = Column(Numeric, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    messages = relationship(
        "TripMessage",
        back_populates="trip",
        cascade="all, delete-orphan",
    )


# ---------- CHAT HISTORY ----------
class TripMessage(Base):
    __tablename__ = "trip_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String, ForeignKey("trips.id"), index=True, nullable=False)

    register_id = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)

    sender_role = Column(String, nullable=False)  # 'user' or 'ai'
    message_type = Column(String, nullable=True)  # 'question', 'answer', 'summary', etc.

    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, nullable=True)  # renamed from 'metadata'

    created_at = Column(DateTime, default=datetime.utcnow)

    trip = relationship("Trip", back_populates="messages")


# ---------- PAYMENT ----------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)  # uuid string
    trip_id = Column(String, ForeignKey("trips.id"), index=True, nullable=False)

    register_id = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)

    provider = Column(String, default="stripe")  # via Clerk Billing
    clerk_user_id = Column(String, nullable=True)
    provider_payment_id = Column(String, nullable=True)  # Stripe session/PI id

    status = Column(String, default="pending")  # pending, succeeded, failed
    amount = Column(Numeric, nullable=True)
    currency = Column(String, default="INR")

    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- FEEDBACK ----------
class Feedback(Base):
    __tablename__ = "trip_feedback"

    id = Column(String, primary_key=True)  # uuid string
    trip_id = Column(String, ForeignKey("trips.id"), index=True, nullable=False)

    register_id = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)

    rating = Column(Integer, nullable=False)  # 1–5
    comments = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

google_calendar_event_id = Column(String, nullable=True)
