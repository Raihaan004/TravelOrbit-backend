from datetime import date
from typing import List, Optional, Any

from pydantic import BaseModel, EmailStr


# ----- Session start -----
class TripSessionStartRequest(BaseModel):
    register_id: str
    email: EmailStr
    members_count: Optional[int] = 1
    # Optional structured passenger list and contact phone to allow direct submission
    passengers: Optional[List[dict]] = None  # e.g., [{"name":"Alice","age":30,"role":"adult"}]
    contact_phone: Optional[str] = None
    # Optional freeform user reply when continuing the conversational flow
    message: Optional[str] = None
    is_mystery_trip: Optional[bool] = False


# ----- Deal Start Request (simplified, collected via form) -----
class DealStartRequest(BaseModel):
    """Request to start a deal booking with passenger and contact details."""
    register_id: str
    email: EmailStr
    passenger_name: Optional[str] = None  # First passenger name
    passenger_age: Optional[int] = None   # First passenger age
    contact_phone: Optional[str] = None   # Contact phone for booking
    from_city: Optional[str] = None       # Departure city
    passengers: Optional[List[dict]] = None  # All passengers: [{"name": "...", "age": ..., "phone": "..."}]
    message: Optional[str] = None         # Optional freeform message


# ----- Deal Auth Flow Request -----
class DealAuthFlowRequest(BaseModel):
    """Authenticated deal booking flow - with built-in auth verification."""
    deal_id: str
    # User identification (required for auth)
    register_id: str
    email: EmailStr
    phone: Optional[str] = None  # Phone for auth verification
    # Passenger details
    passenger_name: Optional[str] = None
    passenger_age: Optional[int] = None
    # Additional travelers
    companions: Optional[List[dict]] = None  # [{"name": "...", "age": ..., "role": "..."}]
    # Optional message for chat flow
    message: Optional[str] = None


class DealBookingFlowResponse(BaseModel):
    """Response for deal booking flow with auth status."""
    trip_id: str
    step: str  # auth_required, passenger_details, phone_verification, payment_ready, completed
    message: str  # AI message to show user
    auth_verified: bool = False
    payment_url: Optional[str] = None
    booking_number: Optional[str] = None
    requires_action: str  # verify_auth, collect_passenger, collect_phone, proceed_payment


class TripSessionStartResponse(BaseModel):
    trip_id: str


# ----- Chat message -----
class TripMessageRequest(BaseModel):
    trip_id: str
    register_id: str
    email: Optional[str] = None  # Make email optional to handle undefined
    message: str


class TripMessageResponse(BaseModel):
    trip_id: str
    ai_message: str
    is_final_itinerary: bool = False


# ----- Passenger Update -----
class TripPassengersUpdate(BaseModel):
    register_id: str
    email: EmailStr
    passengers: List[dict]  # [{"name": "...", "age": ..., "phone": "..."}]
    contact_phone: Optional[str] = None


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


class Hotel(BaseModel):
    name: str
    rating: Optional[str] = None
    price_range: Optional[str] = None
    description: Optional[str] = None
    map_url: Optional[str] = None
    image_search: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    title: str
    activities: List[Activity]


class ItineraryJSON(BaseModel):
    title: str
    hotel: Optional[Hotel] = None
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
    passengers: Optional[Any]
    contact_phone: Optional[str]
    is_mystery_trip: Optional[int] = 0
    mystery_preferences: Optional[Any] = None

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


# ----- Deal of the Day -----
class DealOfDayBase(BaseModel):
    destination: str
    title: Optional[str] = None
    description: Optional[str] = None
    original_price: float
    discounted_price: float
    currency: str = "INR"
    image_url: Optional[str] = None
    # Package fields
    min_persons: Optional[int] = None
    max_persons: Optional[int] = None
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    inclusions: Optional[list] = None
    itinerary: Optional[Any] = None
    is_international: Optional[bool] = False


class DealOfDayResponse(DealOfDayBase):
    id: str
    discount_percentage: Optional[float] = None
    price_per_person: Optional[float] = None
    generated_date: date
    ai_generated: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True


class DealOfDayListResponse(BaseModel):
    deals: List[DealOfDayResponse]
    count: int
    message: str


# ----- Group Planning -----
class GroupCreateRequest(BaseModel):
    leader_id: str
    leader_email: EmailStr
    group_name: str
    members: Optional[List[EmailStr]] = []  # Made optional
    from_city: Optional[str] = None
    expected_count: Optional[int] = None
    destination_options: Optional[List[str]] = None  # The 4 poll options


class GroupCreateResponse(BaseModel):
    group_id: str
    shareable_link: str
    message: str


class GroupVoteRequest(BaseModel):
    voter_email: EmailStr
    voter_name: Optional[str] = None
    voter_phone: Optional[str] = None
    destination: Optional[str] = None
    budget: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    activities: Optional[List[str]] = None


class GroupVoteResponse(BaseModel):
    message: str
    vote_id: str


class GroupResultResponse(BaseModel):
    group_id: str
    group_name: str
    most_voted_destination: Optional[str]
    most_voted_budget: Optional[str]
    most_voted_dates: Optional[str]  # e.g. "2023-12-15 to 2023-12-20"
    most_voted_activities: List[str]
    total_votes: int
    message: str


class GroupDetailResponse(BaseModel):
    group_id: str
    name: str
    leader_id: str
    members: List[dict]  # {email, status}
    votes: List[dict]  # simplified vote info
    destination_options: Optional[List[str]] = None
