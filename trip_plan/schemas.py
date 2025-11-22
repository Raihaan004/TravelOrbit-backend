from datetime import date
from typing import List, Optional, Any

from pydantic import BaseModel, EmailStr


# ----- Session start -----
class TripSessionStartRequest(BaseModel):
    register_id: str
    email: EmailStr


class TripSessionStartResponse(BaseModel):
    trip_id: str


# ----- Chat message -----
class TripMessageRequest(BaseModel):
    trip_id: str
    register_id: str
    email: EmailStr
    message: str


class TripMessageResponse(BaseModel):
    trip_id: str
    ai_message: str
    is_final_itinerary: bool = False


# ----- Feedback -----
class FeedbackCreate(BaseModel):
    rating: int  # 1-5
    comments: Optional[str] = None


# ----- Itinerary JSON (for UI if you want to use it) -----
class Activity(BaseModel):
    name: str
    map_url: Optional[str] = None
    image_search: Optional[str] = None
    time: Optional[str] = None
    category: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    title: str
    activities: List[Activity]


class ItineraryJSON(BaseModel):
    title: str
    days: List[DayPlan]


class TripDetail(BaseModel):
    id: str
    register_id: str
    email: EmailStr
    title: Optional[str]
    from_city: Optional[str]
    to_city: Optional[str]
    party_type: Optional[str]
    budget_level: Optional[str]
    duration_days: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    interests: Optional[list]
    special_requirements: Optional[str]
    status: str
    ai_summary_text: Optional[str]
    ai_summary_json: Optional[Any]

    class Config:
        from_attributes = True


# ----- Packages -----
class Package(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    min_price: int
    max_price: int


class PackageListResponse(BaseModel):
    trip_id: str
    budget_level: Optional[str]
    packages: List[Package]


class PackageSelectRequest(BaseModel):
    register_id: str
    email: EmailStr


class PackageSelectResponse(BaseModel):
    message: str
    trip_id: str
    selected_package: Package
    next_step: Optional[str] = None
