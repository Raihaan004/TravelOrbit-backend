from datetime import datetime
import uuid

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
    # Passenger details and contact
    passengers = Column(JSONB, nullable=True)  # list of passenger objects: {name, age, role}
    contact_phone = Column(String, nullable=True)

    # Deal booking flag
    is_deal_booking = Column(Integer, default=0)  # 1 = from deal, 0 = regular planning

    # Mystery Trip
    is_mystery_trip = Column(Integer, default=0) # 1 = mystery trip
    mystery_preferences = Column(JSONB, nullable=True) # { "location_type": "india", "theme": "adventure" }

    # Calendar sync
    google_calendar_event_id = Column(String, nullable=True)

    # Feedback
    feedback_email_sent = Column(Integer, default=0)  # 0 = not sent, 1 = sent

    status = Column(String, default="draft")  # draft, planned, paid, cancelled
    total_price = Column(Numeric, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    messages = relationship(
        "TripMessage",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    payments = relationship("Payment", back_populates="trip")


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

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    trip_id = Column(String, ForeignKey("trips.id"), index=True, nullable=False)

    register_id = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)

    provider = Column(String, default="mock")  # 'mock' payment gateway
    provider_payment_id = Column(String, nullable=True)  # fake txn id

    status = Column(String, default="pending")  # pending, succeeded, failed
    amount = Column(Numeric, nullable=True)  # major units (e.g. 4500.00)
    currency = Column(String, default="INR")

    created_at = Column(DateTime, default=datetime.utcnow)

    trip = relationship("Trip", back_populates="payments")


# ---------- FEEDBACK ----------
class Feedback(Base):
    __tablename__ = "trip_feedback"

    id = Column(String, primary_key=True)  # uuid string
    trip_id = Column(String, ForeignKey("trips.id"), index=True, nullable=False)

    register_id = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)

    rating = Column(Integer, nullable=False)  # 1–5
    comments = Column(Text, nullable=True)

# ---------- DEAL OF THE DAY ----------
class DealOfDay(Base):
    __tablename__ = "deals_of_day"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    destination = Column(String, nullable=False)  # e.g., "Maldives"
    description = Column(Text, nullable=True)  # Brief description of the destination
    original_price = Column(Numeric, nullable=False)  # e.g., 13000
    discounted_price = Column(Numeric, nullable=False)  # e.g., 10000
    currency = Column(String, default="INR")  # Currency of prices
    ai_generated = Column(String, nullable=True)  # AI model used to generate
    generated_date = Column(Date, nullable=False, default=datetime.utcnow)  # Date deal was generated
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    image_url = Column(String, nullable=True)  # URL to destination image
    title = Column(String, nullable=True)  # short marketing title for the deal
    # Package details
    min_persons = Column(Integer, nullable=True, default=2)
    max_persons = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    inclusions = Column(JSONB, nullable=True)
    itinerary_json = Column(JSONB, nullable=True)
    is_international = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ---------- GROUP PLANNING ----------
class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    short_code = Column(String, unique=True, index=True, nullable=True) # For shareable links
    leader_id = Column(String, nullable=False)  # register_id of the leader
    name = Column(String, nullable=False)
    
    # New fields for poll-based planning
    from_city = Column(String, nullable=True)
    expected_count = Column(Integer, nullable=True)
    destination_options = Column(JSONB, nullable=True)  # List of strings e.g. ["Bali", "Paris", "Goa", "Dubai"]
    
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    votes = relationship("GroupVote", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, default="invited")  # invited, joined

    group = relationship("Group", back_populates="members")


class GroupVote(Base):
    __tablename__ = "group_votes"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    voter_email = Column(String, nullable=False)
    voter_name = Column(String, nullable=True)
    voter_phone = Column(String, nullable=True)
    
    destination = Column(String, nullable=True)
    budget = Column(String, nullable=True)
    
    # Dates can be stored as strings or dates. Storing as strings for flexibility in voting or dates if strict.
    # User prompt says "Preferred dates".
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    activities = Column(JSONB, nullable=True)  # list of strings
    
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="votes")
