from app.pdf_service import PDFService
from trip_plan.models import Trip, Payment
from datetime import datetime

# Mock objects
class MockTrip:
    to_city = "Paris"
    from_city = "New York"
    start_date = datetime.now()
    end_date = datetime.now()
    duration_days = 5
    passengers = [{"name": "John Doe", "age": 30}, {"name": "Jane Doe", "age": 28}]
    ai_summary_json = {
        "days": [
            {"day": "Day 1: Arrival", "activities": [{"time": "10:00", "name": "Check-in"}, {"time": "14:00", "name": "Eiffel Tower"}]},
            {"day": "Day 2: Museum", "activities": ["Louvre Museum", "Seine Cruise"]}
        ],
        "hotel": {
            "name": "Grand Hotel",
            "rating": "5 Star",
            "description": "Luxury stay near city center."
        }
    }

class MockPayment:
    amount = 52499
    currency = "INR"
    provider_payment_id = "pay_123456789"
    provider = "razorpay"
    created_at = datetime.now()
    status = "succeeded"

trip = MockTrip()
payment = MockPayment()
booking_number = "BK-12345"

pdf_bytes = PDFService.generate_itinerary_pdf(trip, payment, booking_number)

if pdf_bytes:
    with open("test_itinerary_v2.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF generated successfully: test_itinerary_v2.pdf")
else:
    print("PDF generation failed")
