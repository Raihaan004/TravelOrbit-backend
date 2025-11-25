"""
Optimized Email Service for TravelOrbit
Handles invoice, itinerary, and passenger details in professional HTML format
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, Dict, List, Any
from datetime import datetime

from app.config import settings
from trip_plan.models import Trip, Payment


class EmailService:
    """Centralized email service with optimization and caching"""
    
    # CSS styles for email templates (cached)
    EMAIL_STYLES = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 8px 8px 0 0;
            margin: -20px -20px 20px -20px;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
        }
        .header p {
            margin: 5px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }
        h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        h3 {
            color: #764ba2;
            margin-top: 15px;
            margin-bottom: 10px;
        }
        .booking-info {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .booking-number {
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        table td {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        table td:first-child {
            font-weight: 600;
            width: 35%;
            color: #667eea;
        }
        .day-itinerary {
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
        }
        .day-header {
            background: #667eea;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .location-item {
            margin: 12px 0;
            padding: 10px;
            background: white;
            border-left: 3px solid #764ba2;
        }
        .location-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .location-description {
            font-size: 14px;
            color: #666;
            margin: 5px 0;
        }
        .media-container {
            display: inline-block;
            margin: 8px 5px 8px 0;
            text-align: center;
        }
        .media-link {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            margin: 5px 5px 5px 0;
            transition: background 0.3s ease;
            text-align: center;
            min-width: 140px;
        }
        .media-link:hover {
            background: #764ba2;
        }
        .activity-image {
            max-width: 100%;
            height: auto;
            max-height: 250px;
            border-radius: 6px;
            margin: 10px 0;
            display: block;
        }
        .traveler {
            background: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 12px;
            margin: 10px 0;
        }
        .traveler-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .traveler-detail {
            font-size: 13px;
            color: #666;
            margin: 3px 0;
        }
        .travelers-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 15px 0;
        }
        .payment-section {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .amount-highlight {
            font-size: 24px;
            font-weight: bold;
            color: #2e7d32;
        }
        .footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 8px 8px;
            font-size: 12px;
            color: #999;
            margin: 20px -20px -20px -20px;
        }
        .highlight {
            background: #fffbea;
            border-left: 3px solid #ffa500;
            padding: 10px;
            margin: 10px 0;
            border-radius: 3px;
        }
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .travelers-grid {
                grid-template-columns: 1fr;
            }
            table td {
                padding: 8px 5px;
                font-size: 13px;
            }
        }
    </style>
    """

    @staticmethod
    def _format_price(amount: Any, currency: str) -> str:
        """Format price with currency symbol"""
        currency_symbols = {
            "INR": "₹",
            "USD": "$",
            "EUR": "€",
            "GBP": "£"
        }
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol} {amount:,.2f}"

    @staticmethod
    def _build_trip_summary_html(trip: Trip, payment: Payment, booking_number: str) -> str:
        """Build trip summary section"""
        start_date = trip.start_date.strftime("%d %b %Y") if trip.start_date else "TBD"
        end_date = trip.end_date.strftime("%d %b %Y") if trip.end_date else "TBD"
        
        trip_summary = f"""
        <div class="container">
            <h2>📋 Trip Summary</h2>
            <div class="booking-info">
                <div>Booking Number: <span class="booking-number">{booking_number}</span></div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">Booking Date: {datetime.utcnow().strftime("%d %b %Y at %H:%M")}</div>
            </div>
            
            <table>
                <tr>
                    <td>Destination</td>
                    <td>{trip.to_city or 'Not specified'} ({trip.from_city or 'From: Not specified'})</td>
                </tr>
                <tr>
                    <td>Travel Dates</td>
                    <td>{start_date} to {end_date}</td>
                </tr>
                <tr>
                    <td>Duration</td>
                    <td>{trip.duration_days} days</td>
                </tr>
                <tr>
                    <td>Party Type</td>
                    <td>{trip.party_type or 'Not specified'}</td>
                </tr>
                <tr>
                    <td>Budget Level</td>
                    <td>{trip.budget_level or 'Not specified'}</td>
                </tr>
            </table>
        </div>
        """
        return trip_summary

    @staticmethod
    def _build_daily_itinerary_html(trip: Trip) -> str:
        """Build detailed daily itinerary with locations, one picture and map per activity"""
        
        if not trip.ai_summary_json:
            return ""
        
        itinerary_html = '<div class="container"><h2>📍 Daily Itinerary</h2>'
        
        try:
            itinerary_data = trip.ai_summary_json
            if isinstance(itinerary_data, str):
                import json
                itinerary_data = json.loads(itinerary_data)
            
            if isinstance(itinerary_data, dict):
                days = itinerary_data.get("days", [])
                if isinstance(days, dict):
                    days = [days]
            else:
                days = itinerary_data if isinstance(itinerary_data, list) else []
            
            for day_num, day_info in enumerate(days, 1):
                if isinstance(day_info, dict):
                    day_title = day_info.get("day", f"Day {day_num}")
                    activities = day_info.get("activities", [])
                    
                    itinerary_html += f"""
                    <div class="day-itinerary">
                        <div class="day-header">🗓️ {day_title}</div>
                    """
                    
                    # Add activities
                    if activities:
                        if isinstance(activities, str):
                            activities = [activities]
                        
                        for act_idx, activity in enumerate(activities, 1):
                            if isinstance(activity, dict):
                                activity_name = activity.get("name", "Activity")
                                activity_time = activity.get("time", "")
                                activity_category = activity.get("category", "")
                                image_search = activity.get("image_search", "")
                                map_url = activity.get("map_url", "")
                                
                                itinerary_html += f'<div class="location-item">'
                                
                                # Time and name
                                if activity_time:
                                    itinerary_html += f'<div class="location-name">⏰ {activity_time} - {activity_name}</div>'
                                else:
                                    itinerary_html += f'<div class="location-name">📌 {activity_name}</div>'
                                
                                # Category
                                if activity_category:
                                    itinerary_html += f'<div class="location-description" style="color: #667eea; font-weight: 500; margin: 5px 0;">Category: {activity_category}</div>'
                                
                                # Picture and Map Links side by side
                                itinerary_html += f'<div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">'
                                
                                if image_search:
                                    # Create a clickable image thumbnail if we have a URL that looks like an image
                                    if image_search.startswith("http") and any(ext in image_search.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                                        itinerary_html += f'<a href="{image_search}" style="display: inline-block;"><img src="{image_search}" alt="{activity_name}" class="activity-image" style="max-width: 250px; max-height: 200px;"></a>'
                                    else:
                                        # Fallback to text link for search URLs
                                        itinerary_html += f'<a href="{image_search}" class="media-link" style="flex: 1; min-width: 120px;">📸 View Pictures</a>'
                                
                                if map_url:
                                    itinerary_html += f'<a href="{map_url}" class="media-link" style="flex: 1; min-width: 120px;">🗺️ View Location</a>'
                                
                                itinerary_html += '</div>'
                                itinerary_html += '</div>'
                            else:
                                # Fallback for string activities
                                itinerary_html += f'<div class="location-item"><div class="location-name">📌 {activity}</div></div>'
                    
                    itinerary_html += '</div>'
        
        except Exception as e:
            itinerary_html += f'<div class="highlight"><p>Itinerary details: {trip.ai_summary_text or "See detailed summary below"}</p></div>'
        
        itinerary_html += '</div>'
        return itinerary_html

    @staticmethod
    def _build_travelers_html(trip: Trip) -> str:
        """Build traveler details section"""
        if not trip.passengers:
            return ""
        
        travelers_html = '<div class="container"><h2>👥 Travel Party</h2><div class="travelers-grid">'
        
        try:
            passengers = trip.passengers
            if isinstance(passengers, str):
                import json
                passengers = json.loads(passengers)
            
            if not isinstance(passengers, list):
                passengers = [passengers] if isinstance(passengers, dict) else []
            
            for idx, passenger in enumerate(passengers, 1):
                if isinstance(passenger, dict):
                    name = passenger.get("name", f"Traveler {idx}")
                    age = passenger.get("age", "")
                    role = passenger.get("role", "Passenger")
                    phone = passenger.get("phone", "")
                    
                    travelers_html += f"""
                    <div class="traveler">
                        <div class="traveler-name">👤 {name}</div>
                        <div class="traveler-detail">Role: {role}</div>
                    """
                    
                    if age:
                        travelers_html += f'<div class="traveler-detail">Age: {age} years</div>'
                    
                    if phone:
                        travelers_html += f'<div class="traveler-detail">Phone: {phone}</div>'
                    
                    travelers_html += '</div>'
        
        except Exception as e:
            pass
        
        travelers_html += '</div></div>'
        
        if len(travelers_html.split('<div class="traveler">')) <= 1:
            return ""
        
        return travelers_html

    @staticmethod
    def _build_invoice_html(trip: Trip, payment: Payment, booking_number: str) -> str:
        """Build payment/invoice section"""
        amount_formatted = EmailService._format_price(payment.amount, payment.currency)
        
        invoice_html = f"""
        <div class="container">
            <h2>💳 Payment Summary</h2>
            <div class="payment-section">
                <table style="border: none;">
                    <tr>
                        <td style="border: none;">Amount</td>
                        <td style="border: none;"><span class="amount-highlight">{amount_formatted}</span></td>
                    </tr>
                    <tr>
                        <td style="border: none;">Status</td>
                        <td style="border: none; color: #2e7d32; font-weight: bold;">✓ {payment.status.upper()}</td>
                    </tr>
                    <tr>
                        <td style="border: none;">Payment Method</td>
                        <td style="border: none;">{payment.provider.replace('_', ' ').title()}</td>
                    </tr>
                    <tr>
                        <td style="border: none;">Transaction ID</td>
                        <td style="border: none; font-family: monospace; font-size: 12px;">{payment.provider_payment_id}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
        return invoice_html

    @staticmethod
    def _build_footer_html() -> str:
        """Build email footer"""
        footer_html = """
        <div class="footer">
            <p style="margin: 10px 0;">Thank you for booking with <strong>TravelOrbit</strong> ✈️🌍</p>
            <p style="margin: 5px 0; color: #aaa;">
                For support, reply to this email or visit our website.
            </p>
            <p style="margin: 10px 0 0 0; border-top: 1px solid #ddd; padding-top: 10px;">
                © 2025 TravelOrbit. All rights reserved.
            </p>
        </div>
        """
        return footer_html

    @staticmethod
    def generate_ticket_html(trip: Trip, booking_number: str) -> str:
        """Public method to generate ticket HTML for use in frontend/email"""
        return EmailService._build_ticket_html(trip, booking_number)

    @staticmethod
    def _build_ticket_html(trip: Trip, booking_number: str) -> str:
        """Build a realistic-looking fake ticket"""
        import random
        
        # Determine Transport Mode
        is_international = False
        
        # Check Mystery Preferences
        if trip.is_mystery_trip and trip.mystery_preferences:
            prefs = trip.mystery_preferences
            if isinstance(prefs, dict):
                loc_type = prefs.get("location_type", "").lower()
                if "international" in loc_type or "outside" in loc_type:
                    is_international = True
        
        # Check Destination (Heuristic)
        if not is_international and trip.to_city:
            # Common Indian cities to treat as Domestic
            indian_cities = [
                "goa", "mumbai", "delhi", "bangalore", "chennai", "kolkata", "jaipur", "udaipur", 
                "agra", "varanasi", "pune", "hyderabad", "kochi", "munnar", "manali", "shimla", 
                "rishikesh", "ladakh", "leh", "srinagar", "andaman", "port blair", "coorg", "ooty",
                "pondicherry", "mysore", "amritsar", "jaisalmer"
            ]
            dest_lower = trip.to_city.lower()
            # If it's NOT in the common Indian list, assume International (or Flight needed)
            # This is a loose heuristic for the "fake" ticket
            if not any(city in dest_lower for city in indian_cities):
                is_international = True

        # Setup Ticket Details
        transport_mode = "FLIGHT" if is_international else "TRAIN"
        if not is_international and random.choice([True, False]):
             # Randomly assign Bus for some domestic trips if not specific
             # But let's stick to Train/Flight for "Premium" feel unless it's short distance.
             # Let's default Domestic to Flight for long distance, Train for others?
             # For simplicity: International = Flight, Domestic = Flight (if luxury) or Train.
             if trip.budget_level == "cheap":
                 transport_mode = "BUS"
             elif trip.budget_level == "moderate":
                 transport_mode = "TRAIN"
             else:
                 transport_mode = "FLIGHT"
        
        # Force Flight for International
        if is_international:
            transport_mode = "FLIGHT"

        # Generate Fake Details
        carrier = "TravelOrbit Air" if transport_mode == "FLIGHT" else ("Indian Railways" if transport_mode == "TRAIN" else "Volvo AC Bus")
        vehicle_number = f"{random.choice(['AI', '6E', 'UK'])}-{random.randint(100, 999)}" if transport_mode == "FLIGHT" else f"{random.randint(12000, 12999)}"
        
        from_loc = trip.from_city or "Origin City"
        to_loc = trip.to_city or "Destination"
        
        dept_time = "10:00 AM"
        arr_time = "02:00 PM"
        
        # Passengers
        passengers_html = ""
        if trip.passengers:
            passengers_list = trip.passengers if isinstance(trip.passengers, list) else []
            for p in passengers_list:
                seat = f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
                p_name = p.get("name", "Traveler")
                passengers_html += f"""
                <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding: 5px 0;">
                    <span>{p_name}</span>
                    <span style="font-weight: bold;">Seat: {seat}</span>
                </div>
                """
        else:
             passengers_html = "<div>Guest Traveler</div>"

        # Ticket HTML Template
        ticket_html = f"""
        <div class="container">
            <h2>🎫 Your Travel Ticket ({transport_mode})</h2>
            <div style="border: 2px dashed #667eea; background: #fff; padding: 0; border-radius: 10px; overflow: hidden; position: relative;">
                
                <!-- Header -->
                <div style="background: #667eea; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: bold; font-size: 18px;">{transport_mode} TICKET</div>
                    <div style="font-family: monospace; font-size: 14px;">PNR: {booking_number}</div>
                </div>
                
                <!-- Body -->
                <div style="padding: 20px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                        <div style="text-align: left;">
                            <div style="font-size: 12px; color: #888;">FROM</div>
                            <div style="font-size: 20px; font-weight: bold; color: #333;">{from_loc.upper()}</div>
                            <div style="font-size: 14px; color: #555;">{dept_time}</div>
                        </div>
                        <div style="text-align: center; align-self: center;">
                            <div style="font-size: 24px; color: #ccc;">✈</div>
                            <div style="font-size: 10px; color: #999;">{vehicle_number}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 12px; color: #888;">TO</div>
                            <div style="font-size: 20px; font-weight: bold; color: #333;">{to_loc.upper()}</div>
                            <div style="font-size: 14px; color: #555;">{arr_time}</div>
                        </div>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 10px; border-radius: 5px;">
                        <div style="font-size: 12px; color: #888; margin-bottom: 5px;">PASSENGERS</div>
                        {passengers_html}
                    </div>
                    
                    <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 12px; color: #888;">OPERATED BY</div>
                            <div style="font-weight: 600; color: #667eea;">{carrier}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 12px; color: #888;">CLASS</div>
                            <div style="font-weight: 600;">Economy</div>
                        </div>
                    </div>
                </div>
                
                <!-- Fake Barcode -->
                <div style="background: #333; color: white; padding: 10px; text-align: center; font-family: monospace; letter-spacing: 4px;">
                    ||| || ||| | |||| ||| || |||||
                </div>
            </div>
        </div>
        """
        return ticket_html

    @classmethod
    def build_complete_email_html(
        cls,
        trip: Trip,
        payment: Payment,
        booking_number: str
    ) -> str:
        """Build complete, optimized email HTML"""
        
        header = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {cls.EMAIL_STYLES}
        </head>
        <body>
        <div class="container">
            <div class="header">
                <h1>🎒 Your TravelOrbit Trip is Confirmed!</h1>
                <p>Booking Confirmation & Itinerary</p>
            </div>
        </div>
        """
        
        trip_summary = cls._build_trip_summary_html(trip, payment, booking_number)
        ticket = cls._build_ticket_html(trip, booking_number)
        hotel_info = cls._build_hotel_info_html(trip)
        daily_itinerary = cls._build_daily_itinerary_html(trip)
        travelers = cls._build_travelers_html(trip)
        invoice = cls._build_invoice_html(trip, payment, booking_number)
        footer = cls._build_footer_html()
        
        complete_html = f"""
        {header}
        {trip_summary}
        {ticket}
        {hotel_info}
        {daily_itinerary}
        {travelers}
        {invoice}
        {footer}
        </body>
        </html>
        """
        
        return complete_html

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send email via SMTP with error handling and attachment support
        attachments: List of dicts with keys 'filename', 'content' (bytes), 'mime_type' (optional)
        Returns True if successful, False otherwise
        """
        
        # Validate configuration
        if not settings.SMTP_HOST or not settings.SENDER_EMAIL:
            print("⚠️ SMTP not configured. Email content:")
            print(html_body)
            return False
        
        # Safeguard: skip placeholder emails in development
        try:
            recipient_domain = to_email.split("@", 1)[1].lower()
            if recipient_domain in ("example.com", "example.org", "test.com"):
                print(f"⚠️ Skipping placeholder email to {to_email} (development mode)")
                return False
        except Exception:
            pass
        
        try:
            # Create multipart message
            msg = MIMEMultipart("mixed") if attachments else MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SENDER_EMAIL
            msg["To"] = to_email
            
            # Create the body part
            if attachments:
                body_part = MIMEMultipart("alternative")
                if text_body:
                    body_part.attach(MIMEText(text_body, "plain"))
                body_part.attach(MIMEText(html_body, "html"))
                msg.attach(body_part)
            else:
                if text_body:
                    msg.attach(MIMEText(text_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))
            
            # Attach files
            if attachments:
                for attachment in attachments:
                    filename = attachment.get("filename", "attachment")
                    content = attachment.get("content")
                    if content:
                        part = MIMEApplication(content, Name=filename)
                        part['Content-Disposition'] = f'attachment; filename="{filename}"'
                        msg.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending email to {to_email}: {e}")
            return False

    @staticmethod
    def _build_hotel_info_html(trip: Trip) -> str:
        """Build hotel information section"""
        if not trip.ai_summary_json:
            return ""
            
        try:
            itinerary_data = trip.ai_summary_json
            if isinstance(itinerary_data, str):
                import json
                itinerary_data = json.loads(itinerary_data)
                
            hotel = itinerary_data.get("hotel")
            if not hotel:
                return ""
                
            name = hotel.get("name", "Hotel")
            rating = hotel.get("rating", "")
            description = hotel.get("description", "")
            map_url = hotel.get("map_url", "")
            image_search = hotel.get("image_search", "")
            
            hotel_html = f"""
            <div class="container">
                <h2>🏨 Accommodation Details</h2>
                <div class="booking-info" style="border-left-color: #ff9800; background: #fff3e0;">
                    <div style="font-size: 18px; font-weight: bold; color: #e65100;">{name}</div>
                    {f'<div style="color: #f57c00; font-weight: 500;">{rating}</div>' if rating else ''}
                    {f'<div style="margin-top: 5px; color: #555;">{description}</div>' if description else ''}
                    
                    <div style="margin-top: 10px;">
                        {f'<a href="{map_url}" style="text-decoration: none; color: #e65100; font-weight: bold; margin-right: 15px;">📍 View on Map</a>' if map_url else ''}
                        {f'<a href="{image_search}" style="text-decoration: none; color: #e65100; font-weight: bold;">📷 View Photos</a>' if image_search else ''}
                    </div>
                </div>
            </div>
            """
            return hotel_html
            
        except Exception as e:
            return ""

    @staticmethod
    def _build_feedback_email_html(trip: Trip) -> str:
        """Build feedback request email HTML"""
        feedback_link = f"http://localhost:5500/feedback.html?trip_id={trip.id}"
        
        feedback_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {EmailService.EMAIL_STYLES}
        </head>
        <body>
        <div class="container">
            <div class="header">
                <h1>👋 Welcome Back!</h1>
                <p>We hope you had an amazing trip!</p>
            </div>
            
            <div class="container">
                <h2>How was your trip to {trip.to_city}?</h2>
                <p>We'd love to hear about your experience. Your feedback helps us improve and help other travelers plan their perfect trips.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{feedback_link}" class="media-link" style="padding: 15px 30px; font-size: 16px;">Rate Your Trip</a>
                </div>
                
                <p>It only takes a minute!</p>
            </div>
            
            {EmailService._build_footer_html()}
        </div>
        </body>
        </html>
        """
        return feedback_html

    @staticmethod
    def send_feedback_request_email(trip: Trip) -> bool:
        """Send feedback request email"""
        html_body = EmailService._build_feedback_email_html(trip)
        subject = f"Welcome back! How was your trip to {trip.to_city}?"
        return EmailService.send_email(trip.email, subject, html_body)


# Convenience functions for backwards compatibility
def send_booking_email(trip: Trip, payment: Payment, booking_number: str, to_email: str) -> bool:
    """Send complete booking confirmation email with PDF itinerary"""
    from app.pdf_service import PDFService
    
    html_body = EmailService.build_complete_email_html(trip, payment, booking_number)
    subject = f"Your TravelOrbit Booking Confirmed - Booking No: {booking_number}"
    
    # Generate PDF
    pdf_bytes = PDFService.generate_itinerary_pdf(trip, payment, booking_number)
    attachments = []
    if pdf_bytes:
        attachments.append({
            "filename": f"Itinerary_{booking_number}.pdf",
            "content": pdf_bytes,
            "mime_type": "application/pdf"
        })
    
    return EmailService.send_email(to_email, subject, html_body, attachments=attachments)
