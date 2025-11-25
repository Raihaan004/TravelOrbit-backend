"""
Quick Start Templates for TravelOrbit PDF Generator
Copy and modify these templates for your use case
"""

# ======================== TEMPLATE 1: BASIC USAGE ========================

from travel_pdf_generator_v4 import TravelPDFGenerator

def template_basic_usage():
    """Simplest way to use the PDF generator"""
    
    trip_data = {
        'destination': 'Paris',
        'start_date': '2025-04-10',
        'end_date': '2025-04-17',
        'travelers': '2 Adults',
        'duration': '7 Days, 6 Nights',
        'package_type': 'City Break',
        'hotel_name': 'Le Meurice, Paris',
        'hotel_rating': '⭐⭐⭐⭐⭐',
        'total_cost': '₹2,85,000',
        'itinerary': [
            {
                'title': 'Arrival & City Exploration',
                'description': 'Arrive in Paris and settle into your luxury hotel. Enjoy dinner with Eiffel Tower views.',
                'activities': ['Arrival', 'Hotel check-in', 'Eiffel Tower', 'Seine cruise', 'Dinner'],
            },
            {
                'title': 'Louvre & Museums',
                'description': 'Explore the world-famous Louvre museum and other art galleries.',
                'activities': ['Louvre tour', 'Art gallery', 'Lunch', 'Shopping', 'Theatre'],
            },
            {
                'title': 'Versailles Palace',
                'description': 'Day trip to the magnificent Palace of Versailles and gardens.',
                'activities': ['Train travel', 'Palace tour', 'Gardens', 'Picnic', 'Return'],
            },
            {
                'title': 'Montmartre & Sacré-Cœur',
                'description': 'Visit the artistic neighborhood of Montmartre.',
                'activities': ['Montmartre walk', 'Street artists', 'Basilica', 'Cafe', 'Views'],
            },
            {
                'title': 'Champs-Élysées & Shopping',
                'description': 'Luxury shopping and sightseeing on the famous avenue.',
                'activities': ['Arc de Triomphe', 'Shopping', 'Lunch', 'Museum', 'Spa'],
            },
            {
                'title': 'Farewell Day',
                'description': 'Last-minute shopping and departure.',
                'activities': ['Breakfast', 'Shopping', 'Packing', 'Airport', 'Departure'],
            },
        ]
    }
    
    generator = TravelPDFGenerator()
    generator.create_pdf(trip_data, "paris_itinerary.pdf")
    print("✓ Paris itinerary PDF created: paris_itinerary.pdf")


# ======================== TEMPLATE 2: LUXURY RESORT ========================

def template_luxury_resort():
    """Template for luxury resort/beach vacation"""
    
    trip_data = {
        'destination': 'Bali',
        'start_date': '2025-05-15',
        'end_date': '2025-05-22',
        'travelers': '2 Adults, 1 Child',
        'duration': '7 Days, 6 Nights',
        'package_type': 'Luxury Resort',
        'hotel_name': 'The St. Regis Bali Resort',
        'hotel_rating': '⭐⭐⭐⭐⭐',
        'total_cost': '₹3,50,000',
        'itinerary': [
            {
                'title': 'Arrival & Pool Time',
                'description': 'Welcome to paradise! Check in and relax at the resort.',
                'activities': ['Flight arrival', 'Resort check-in', 'Pool time', 'Sunset view', 'Dinner'],
            },
            {
                'title': 'Beach & Water Sports',
                'description': 'Enjoy water activities and beach time.',
                'activities': ['Snorkeling', 'Jet ski', 'Beach volleyball', 'Spa', 'Dinner'],
            },
            {
                'title': 'Temple Tour',
                'description': 'Cultural exploration of ancient temples.',
                'activities': ['Tanah Lot Temple', 'Ubud walk', 'Local market', 'Massage', 'Dinner'],
            },
            {
                'title': 'Adventure Day',
                'description': 'Mountain biking and scenic views.',
                'activities': ['Mountain bike', 'Rice terrace', 'Volcano tour', 'Lunch', 'Rest'],
            },
            {
                'title': 'Yoga & Wellness',
                'description': 'Relax and rejuvenate with wellness activities.',
                'activities': ['Yoga class', 'Meditation', 'Spa day', 'Pool', 'Dinner'],
            },
            {
                'title': 'Last Day Leisure',
                'description': 'Final moments to enjoy the resort.',
                'activities': ['Breakfast', 'Beach walk', 'Shopping', 'Lunch', 'Rest'],
            },
            {
                'title': 'Departure',
                'description': 'Checkout and travel home with memories.',
                'activities': ['Breakfast', 'Packing', 'Checkout', 'Airport', 'Departure'],
            },
        ]
    }
    
    generator = TravelPDFGenerator()
    generator.create_pdf(trip_data, "bali_resort_itinerary.pdf")
    print("✓ Bali resort itinerary PDF created: bali_resort_itinerary.pdf")


# ======================== TEMPLATE 3: ADVENTURE TRIP ========================

def template_adventure():
    """Template for adventure/hiking trip"""
    
    trip_data = {
        'destination': 'Himalayas',
        'start_date': '2025-06-01',
        'end_date': '2025-06-10',
        'travelers': '4 Adults',
        'duration': '10 Days, 9 Nights',
        'package_type': 'Adventure Trekking',
        'hotel_name': 'Himalayan Adventure Lodge',
        'hotel_rating': '⭐⭐⭐⭐',
        'total_cost': '₹1,80,000',
        'itinerary': [
            {
                'title': 'Arrival & Acclimatization',
                'description': 'Arrive and acclimatize to the altitude.',
                'activities': ['Flight arrival', 'Hotel check-in', 'Rest', 'Dinner', 'Early sleep'],
            },
            {
                'title': 'Day Hike & Training',
                'description': 'Warm-up day hike to build endurance.',
                'activities': ['Easy hike', 'Training', 'Stretching', 'Dinner', 'Sleep'],
            },
            {
                'title': 'Base Camp Trek Start',
                'description': 'Begin the main trek to base camp.',
                'activities': ['Trek start', 'Mountain views', 'Camp setup', 'Dinner', 'Campfire'],
            },
            {
                'title': 'High Altitude Trek',
                'description': 'Push higher with stunning views.',
                'activities': ['Early start', 'High trek', 'Peak views', 'Camping', 'Rest'],
            },
            {
                'title': 'Base Camp Arrival',
                'description': 'Reach the base camp location.',
                'activities': ['Final climb', 'Base camp', 'Celebration', 'Photos', 'Recovery'],
            },
            {
                'title': 'Summit Day Attempt',
                'description': 'Early morning attempt to summit.',
                'activities': ['Early start', 'Summit climb', 'Photos', 'Descent', 'Rest'],
            },
            {
                'title': 'Descent Day 1',
                'description': 'Begin descent from base camp.',
                'activities': ['Trek down', 'Lower camp', 'Recovery', 'Dinner', 'Sleep'],
            },
            {
                'title': 'Descent Day 2',
                'description': 'Continue descent to base lodge.',
                'activities': ['Trek down', 'Celebration', 'Lodge arrival', 'Shower', 'Dinner'],
            },
            {
                'title': 'Recovery & Culture',
                'description': 'Rest and explore local culture.',
                'activities': ['Rest day', 'Local market', 'Monastery', 'Meditation', 'Dinner'],
            },
            {
                'title': 'Departure',
                'description': 'Travel back home.',
                'activities': ['Breakfast', 'Packing', 'Checkout', 'Airport', 'Departure'],
            },
        ]
    }
    
    generator = TravelPDFGenerator()
    generator.create_pdf(trip_data, "himalayan_adventure.pdf")
    print("✓ Himalayan adventure itinerary PDF created: himalayan_adventure.pdf")


# ======================== TEMPLATE 4: ROMANTIC HONEYMOON ========================

def template_honeymoon():
    """Template for romantic honeymoon"""
    
    trip_data = {
        'destination': 'Maldives',
        'start_date': '2025-07-01',
        'end_date': '2025-07-08',
        'travelers': '2 Adults',
        'duration': '7 Days, 6 Nights',
        'package_type': 'Romantic Honeymoon',
        'hotel_name': 'Soneva Jani, Maldives',
        'hotel_rating': '⭐⭐⭐⭐⭐',
        'total_cost': '₹5,50,000',
        'itinerary': [
            {
                'title': 'Romantic Welcome',
                'description': 'Begin your honeymoon with champagne welcome.',
                'activities': ['Arrival', 'Resort welcome', 'Check-in', 'Sunset cocktail', 'Dinner for two'],
            },
            {
                'title': 'Overwater Villa Bliss',
                'description': 'Enjoy time at your private overwater villa.',
                'activities': ['Villa experience', 'Private beach', 'Massage', 'Dinner on beach', 'Stargazing'],
            },
            {
                'title': 'Water Activities',
                'description': 'Adventure on the crystal-clear waters.',
                'activities': ['Snorkeling', 'Diving', 'Sunset cruise', 'Romantic dinner', 'Night swim'],
            },
            {
                'title': 'Spa & Wellness',
                'description': 'Couples spa day for relaxation.',
                'activities': ['Couple massage', 'Wellness', 'Yoga', 'Pool time', 'Dinner'],
            },
            {
                'title': 'Island Hopping',
                'description': 'Explore nearby islands together.',
                'activities': ['Island tour', 'Fishing', 'Picnic', 'Photography', 'Dinner'],
            },
            {
                'title': 'Private Beach Dinner',
                'description': 'Special evening on your private beach.',
                'activities': ['Beach setup', 'Candlelight dinner', 'Wine tasting', 'Walk', 'Romance'],
            },
            {
                'title': 'Departure Farewell',
                'description': 'Say goodbye to paradise.',
                'activities': ['Breakfast', 'Beach walk', 'Shopping', 'Checkout', 'Departure'],
            },
        ]
    }
    
    generator = TravelPDFGenerator()
    generator.create_pdf(trip_data, "honeymoon_itinerary.pdf")
    print("✓ Honeymoon itinerary PDF created: honeymoon_itinerary.pdf")


# ======================== TEMPLATE 5: FAMILY VACATION ========================

def template_family_vacation():
    """Template for family trip with kids"""
    
    trip_data = {
        'destination': 'Goa',
        'start_date': '2025-08-01',
        'end_date': '2025-08-08',
        'travelers': '4 Adults, 2 Children',
        'duration': '7 Days, 6 Nights',
        'package_type': 'Family Vacation',
        'hotel_name': 'Taj Exotica Resort, Goa',
        'hotel_rating': '⭐⭐⭐⭐',
        'total_cost': '₹2,40,000',
        'itinerary': [
            {
                'title': 'Beach Arrival',
                'description': 'Welcome to Goa! Settle in and hit the beach.',
                'activities': ['Arrival', 'Check-in', 'Beach time', 'Kids play', 'Dinner'],
            },
            {
                'title': 'Water Sports Fun',
                'description': 'Family water activities and games.',
                'activities': ['Jet ski', 'Parasailing', 'Beach volleyball', 'Swim', 'Dinner'],
            },
            {
                'title': 'River Cruise',
                'description': 'Relaxing backwater cruise.',
                'activities': ['River cruise', 'Bird watching', 'Lunch', 'Shopping', 'Dinner'],
            },
            {
                'title': 'Adventure Park',
                'description': 'Kids adventure activities.',
                'activities': ['Adventure park', 'Games', 'Zip line', 'Lunch', 'Rest'],
            },
            {
                'title': 'Cultural Day',
                'description': 'Explore local culture and heritage.',
                'activities': ['Temple visit', 'Market tour', 'Local food', 'Art gallery', 'Dinner'],
            },
            {
                'title': 'Beach Relaxation',
                'description': 'Chill day at the beach.',
                'activities': ['Beach time', 'Sandcastle', 'Pool', 'Kids activities', 'Dinner'],
            },
            {
                'title': 'Departure Day',
                'description': 'Pack memories and head home.',
                'activities': ['Breakfast', 'Beach walk', 'Shopping', 'Checkout', 'Departure'],
            },
        ]
    }
    
    generator = TravelPDFGenerator()
    generator.create_pdf(trip_data, "goa_family_vacation.pdf")
    print("✓ Goa family vacation itinerary PDF created: goa_family_vacation.pdf")


# ======================== TEMPLATE 6: CULTURAL TOUR ========================

def template_cultural_tour():
    """Template for cultural and historical tour"""
    
    trip_data = {
        'destination': 'India',
        'start_date': '2025-09-01',
        'end_date': '2025-09-14',
        'travelers': '2 Adults',
        'duration': '14 Days, 13 Nights',
        'package_type': 'Cultural Heritage Tour',
        'hotel_name': 'Golden Triangle Hotels',
        'hotel_rating': '⭐⭐⭐⭐',
        'total_cost': '₹1,80,000',
        'itinerary': [
            {
                'title': 'Delhi Arrival',
                'description': 'Arrive in Delhi and explore the capital.',
                'activities': ['Arrival', 'Old Delhi walk', 'Red Fort', 'New Delhi', 'Dinner'],
            },
            {
                'title': 'Delhi Heritage',
                'description': 'Continue exploring Delhi monuments.',
                'activities': ['India Gate', 'Qutb Minar', 'Museums', 'Market', 'Dinner'],
            },
            {
                'title': 'Agra - Taj Mahal',
                'description': 'Travel to Agra and see the Taj Mahal.',
                'activities': ['Train travel', 'Taj Mahal', 'Sunrise view', 'Dinner', 'Rest'],
            },
            {
                'title': 'Agra Forts',
                'description': 'Explore Agra Fort and local markets.',
                'activities': ['Agra Fort', 'River cruise', 'Local market', 'Shopping', 'Dinner'],
            },
            {
                'title': 'Jaipur - City Palace',
                'description': 'Journey to the Pink City Jaipur.',
                'activities': ['Travel', 'City Palace', 'Jantar Mantar', 'Dinner', 'Rest'],
            },
            {
                'title': 'Amber Fort',
                'description': 'Visit the majestic Amber Fort.',
                'activities': ['Amber Fort', 'Elephant ride', 'Views', 'Lunch', 'Market'],
            },
            {
                'title': 'Jaipur Culture',
                'description': 'Explore Jaipur culture and crafts.',
                'activities': ['Hawa Mahal', 'Art gallery', 'Textile shop', 'Workshop', 'Dinner'],
            },
            {
                'title': 'Return to Delhi',
                'description': 'Final night in Delhi.',
                'activities': ['Travel', 'Last-minute shopping', 'Lunch', 'Dinner', 'Rest'],
            },
            {
                'title': 'Departure',
                'description': 'Head to airport.',
                'activities': ['Breakfast', 'Packing', 'Checkout', 'Airport', 'Departure'],
            },
        ]
    }
    
    generator = TravelPDFGenerator()
    generator.create_pdf(trip_data, "india_cultural_tour.pdf")
    print("✓ India cultural tour itinerary PDF created: india_cultural_tour.pdf")


# ======================== RUN ALL TEMPLATES ========================

if __name__ == "__main__":
    print("Generating all template PDFs...\n")
    
    template_basic_usage()
    template_luxury_resort()
    template_adventure()
    template_honeymoon()
    template_family_vacation()
    template_cultural_tour()
    
    print("\n✓ All template PDFs generated successfully!")
    print("\nGenerated files:")
    print("  - paris_itinerary.pdf")
    print("  - bali_resort_itinerary.pdf")
    print("  - himalayan_adventure.pdf")
    print("  - honeymoon_itinerary.pdf")
    print("  - goa_family_vacation.pdf")
    print("  - india_cultural_tour.pdf")
