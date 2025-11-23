"""
Email Data Helper - Utilities for structuring itinerary and passenger data
for optimal email rendering
"""

from typing import List, Dict, Optional, Any
import json
from datetime import date


class ItineraryLocation:
    """Represents a single location in the itinerary"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        photo_url: Optional[str] = None,
        map_url: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.photo_url = photo_url
        self.map_url = map_url
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "photo_url": self.photo_url or "",
            "map_url": self.map_url or "",
        }


class ItineraryDay:
    """Represents a single day in the itinerary"""
    
    def __init__(
        self,
        day_number: int,
        title: str = "",
        locations: Optional[List[ItineraryLocation]] = None,
        activities: str = "",
    ):
        self.day_number = day_number
        self.title = title or f"Day {day_number}"
        self.locations = locations or []
        self.activities = activities
    
    def add_location(
        self,
        name: str,
        description: str = "",
        photo_url: Optional[str] = None,
        map_url: Optional[str] = None,
    ) -> 'ItineraryDay':
        """Add a location to this day (fluent interface)"""
        location = ItineraryLocation(name, description, photo_url, map_url)
        self.locations.append(location)
        return self
    
    def set_activities(self, activities: str) -> 'ItineraryDay':
        """Set activities for this day (fluent interface)"""
        self.activities = activities
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "day": self.title,
            "locations": [loc.to_dict() for loc in self.locations],
            "activities": self.activities,
        }


class Itinerary:
    """Represents a complete multi-day itinerary"""
    
    def __init__(self):
        self.days: List[ItineraryDay] = []
    
    def add_day(
        self,
        day_number: int,
        title: str = "",
        locations: Optional[List[ItineraryLocation]] = None,
        activities: str = "",
    ) -> ItineraryDay:
        """Add a day to the itinerary and return the day object"""
        day = ItineraryDay(day_number, title, locations, activities)
        self.days.append(day)
        return day
    
    def to_json_string(self) -> str:
        """Convert to JSON string for storing in database"""
        data = {"days": [day.to_dict() for day in self.days]}
        return json.dumps(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {"days": [day.to_dict() for day in self.days]}


class Traveler:
    """Represents a single traveler/passenger"""
    
    # Standard roles
    ROLE_LEAD = "Lead Traveler"
    ROLE_CO_TRAVELER = "Co-Traveler"
    ROLE_CHILD = "Child"
    ROLE_SENIOR = "Senior"
    ROLE_GUEST = "Guest"
    
    def __init__(
        self,
        name: str,
        age: Optional[int] = None,
        role: str = ROLE_CO_TRAVELER,
        phone: str = "",
        email: str = "",
    ):
        self.name = name
        self.age = age
        self.role = role
        self.phone = phone
        self.email = email
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "age": self.age,
            "role": self.role,
            "phone": self.phone,
            "email": self.email,
        }


class TravelParty:
    """Represents a group of travelers"""
    
    def __init__(self):
        self.travelers: List[Traveler] = []
    
    def add_traveler(
        self,
        name: str,
        age: Optional[int] = None,
        role: str = Traveler.ROLE_CO_TRAVELER,
        phone: str = "",
        email: str = "",
    ) -> 'TravelParty':
        """Add a traveler to the party (fluent interface)"""
        traveler = Traveler(name, age, role, phone, email)
        self.travelers.append(traveler)
        return self
    
    def add_lead_traveler(
        self,
        name: str,
        age: Optional[int] = None,
        phone: str = "",
        email: str = "",
    ) -> 'TravelParty':
        """Add the lead traveler"""
        self.add_traveler(name, age, Traveler.ROLE_LEAD, phone, email)
        return self
    
    def add_child(
        self,
        name: str,
        age: int,
        phone: str = "",
    ) -> 'TravelParty':
        """Add a child"""
        self.add_traveler(name, age, Traveler.ROLE_CHILD, phone)
        return self
    
    def add_senior(
        self,
        name: str,
        age: Optional[int] = None,
        phone: str = "",
    ) -> 'TravelParty':
        """Add a senior traveler"""
        self.add_traveler(name, age, Traveler.ROLE_SENIOR, phone)
        return self
    
    def to_json_string(self) -> str:
        """Convert to JSON string for storing in database"""
        data = [traveler.to_dict() for traveler in self.travelers]
        return json.dumps(data)
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries"""
        return [traveler.to_dict() for traveler in self.travelers]


# ============================================================
# Example Usage Functions
# ============================================================

def example_create_itinerary() -> str:
    """Example of building an itinerary for the email"""
    
    itinerary = Itinerary()
    
    # Day 1
    day1 = itinerary.add_day(1, "Day 1 - Arrival in Maldives")
    day1.add_location(
        name="Indira Gandhi International Airport",
        description="Arrive at airport and complete customs",
        photo_url="https://images.unsplash.com/photo-1571151682758-0a92c58e4ba3",
        map_url="https://maps.google.com/?q=Delhi+Airport"
    ).add_location(
        name="Seaplane Transfer",
        description="Scenic seaplane ride to resort",
        photo_url="https://images.unsplash.com/photo-1551632440-01b43f7e0667",
        map_url="https://maps.google.com/?q=Maldives"
    ).add_location(
        name="Resort Check-in",
        description="Check-in and evening at leisure",
        photo_url="https://images.pexels.com/photos/2507023/pexels-photo-2507023.jpeg",
        map_url="https://maps.google.com/?q=Maldives+Resort"
    )
    day1.set_activities("Arrival, relax, and beach walk")
    
    # Day 2
    day2 = itinerary.add_day(2, "Day 2 - Snorkeling & Diving")
    day2.add_location(
        name="House Reef",
        description="Guided snorkeling in clear waters",
        photo_url="https://images.unsplash.com/photo-1559827260-dc66d52bef19",
        map_url="https://maps.google.com/?q=Maldives+Reef"
    ).add_location(
        name="Sunset Dolphin Cruise",
        description="Evening cruise to spot dolphins",
        photo_url="https://images.unsplash.com/photo-1505142468610-359e7d316be0",
        map_url="https://maps.google.com/?q=Maldives+Cruise"
    )
    day2.set_activities("Snorkeling, diving, dolphin watching")
    
    # Day 3
    day3 = itinerary.add_day(3, "Day 3 - Water Sports & Spa")
    day3.add_location(
        name="Water Sports Center",
        description="Try windsurfing and parasailing",
        photo_url="https://images.unsplash.com/photo-1570804786720-7538a18a8cc0",
        map_url="https://maps.google.com/?q=Water+Sports"
    ).add_location(
        name="Spa Resort",
        description="Relaxing massage and spa treatment",
        photo_url="https://images.unsplash.com/photo-1544161515-b61d7f0d15b0",
        map_url="https://maps.google.com/?q=Spa+Resort"
    )
    day3.set_activities("Water sports, spa treatment, dinner")
    
    return itinerary.to_json_string()


def example_create_travel_party() -> str:
    """Example of building a travel party for the email"""
    
    party = TravelParty()
    
    party.add_lead_traveler(
        name="Rajesh Kumar",
        age=35,
        phone="+91-9999999999",
        email="rajesh@example.com"
    ).add_traveler(
        name="Priya Kumar",
        age=32,
        role=Traveler.ROLE_CO_TRAVELER,
        phone="+91-8888888888"
    ).add_child(
        name="Aryan Kumar",
        age=8,
        phone=""
    ).add_child(
        name="Isha Kumar",
        age=5,
        phone=""
    )
    
    return party.to_json_string()


# ============================================================
# Integration Example
# ============================================================

def example_integration(trip):
    """
    Example of how to use these helpers in your trip planning code
    
    Usage:
        # In your AI trip planner or chat flow
        trip.ai_summary_json = example_create_itinerary()
        trip.passengers = example_create_travel_party()
        db.add(trip)
        db.commit()
    """
    
    # Build itinerary
    itinerary = Itinerary()
    
    for day_num in range(1, trip.duration_days + 1):
        day = itinerary.add_day(day_num, f"Day {day_num}")
        
        # Add locations (fetched from AI or database)
        # This is pseudocode - adapt to your actual data source
        locations = get_locations_for_day(trip.to_city, day_num)  # Your function
        
        for location in locations:
            photo_url = fetch_photo_url(location.name)  # Use Pexels/Unsplash API
            map_url = f"https://maps.google.com/?q={location.name}"
            
            day.add_location(
                name=location.name,
                description=location.description,
                photo_url=photo_url,
                map_url=map_url
            )
        
        day.set_activities(generate_activities_text(locations))  # Your function
    
    # Build travel party
    party = TravelParty()
    
    if trip.passengers:
        for passenger in trip.passengers:
            if passenger.get("role") == Traveler.ROLE_LEAD:
                party.add_lead_traveler(
                    name=passenger.get("name"),
                    age=passenger.get("age"),
                    phone=passenger.get("phone")
                )
            else:
                party.add_traveler(
                    name=passenger.get("name"),
                    age=passenger.get("age"),
                    role=passenger.get("role", Traveler.ROLE_CO_TRAVELER),
                    phone=passenger.get("phone")
                )
    
    # Save to trip
    trip.ai_summary_json = itinerary.to_json_string()
    trip.passengers = party.to_json_string()
    
    return trip
