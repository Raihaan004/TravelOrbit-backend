import io
import logging
import os
import tempfile
import requests
from datetime import datetime
from xhtml2pdf import pisa
from app.config import settings
from trip_plan.models import Trip, Payment

logger = logging.getLogger(__name__)

class PDFService:
    """
    Service to generate magazine-style PDF itineraries using xhtml2pdf.
    """

    @staticmethod
    def link_callback(uri, rel):
        """
        Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
        """
        if uri.startswith('http'):
            try:
                # Use a proper user agent to avoid being blocked
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(uri, headers=headers, timeout=10)
                if response.status_code == 200:
                    # Create a temp file
                    ext = ".jpg"
                    if "png" in response.headers.get("Content-Type", ""):
                        ext = ".png"
                    
                    fd, path = tempfile.mkstemp(suffix=ext)
                    with os.fdopen(fd, 'wb') as tmp:
                        tmp.write(response.content)
                    return path
            except Exception as e:
                logger.error(f"Error fetching {uri}: {e}")
        return uri

    @staticmethod
    def _format_currency(amount, currency="INR"):
        symbol = "₹" if currency == "INR" else currency
        return f"{symbol} {amount:,.2f}"

    @staticmethod
    def generate_itinerary_pdf(trip: Trip, payment: Payment, booking_number: str) -> bytes:
        """
        Generates a PDF itinerary for the given trip.
        Returns the PDF content as bytes.
        """
        try:
            # Prepare data
            html_content = PDFService._build_html(trip, payment, booking_number)
            
            # Convert to PDF
            pdf_file = io.BytesIO()
            pisa_status = pisa.CreatePDF(
                io.StringIO(html_content),
                dest=pdf_file,
                encoding='utf-8',
                link_callback=PDFService.link_callback
            )

            if pisa_status.err:
                logger.error(f"PDF generation error: {pisa_status.err}")
                return None

            return pdf_file.getvalue()

        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            return None

    @staticmethod
    def _build_html(trip: Trip, payment: Payment, booking_number: str) -> str:
        """
        Builds the complete HTML for the PDF.
        """
        # Extract data
        destination = trip.to_city or "Unknown Destination"
        start_date = trip.start_date.strftime("%d %b") if trip.start_date else "TBD"
        end_date = trip.end_date.strftime("%d %b %Y") if trip.end_date else "TBD"
        duration = f"{trip.duration_days} Days"
        travelers_count = len(trip.passengers) if trip.passengers else 1
        travelers_text = f"{travelers_count} Adults"
        
        # Vibrant Colors (no black)
        color_primary = "#FF6B35"     # Vibrant Orange
        color_secondary = "#004E89"   # Deep Blue
        color_accent = "#1BA0C8"      # Bright Cyan
        color_gold = "#FFD700"        # Gold
        color_pink = "#FF1493"        # Deep Pink
        color_green = "#00D84F"       # Bright Green
        color_purple = "#9D4EDD"      # Vibrant Purple
        color_yellow = "#FFE66D"      # Bright Yellow
        color_text = "#1A1A1A"        # Very Dark Gray (not black)
        color_bg_light = "#E8F4F8"    # Light Cyan
        color_bg_warm = "#FFF0E6"     # Warm Cream
        
        # CSS with Full-Page Coverage - Simplified for xhtml2pdf
        css = f"""
        <style>
            @page {{
                size: A4;
                margin: 0;
                padding: 0;
            }}
            * {{
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                color: {color_text};
                margin: 0;
                padding: 0;
            }}
            .page {{
                page-break-after: always;
            }}
            h1 {{ 
                font-size: 42pt; 
                color: {color_primary}; 
                margin-bottom: 20pt;
                font-weight: bold;
            }}
            h2 {{ 
                font-size: 28pt; 
                color: {color_secondary}; 
                margin-bottom: 15pt;
                margin-top: 15pt;
                border-bottom: 4pt solid {color_gold}; 
                padding-bottom: 8pt;
                display: block;
            }}
            h3 {{
                font-size: 20pt;
                color: {color_primary};
                margin-bottom: 10pt;
                margin-top: 12pt;
            }}
            
            img {{
                border-radius: 15pt;
                max-width: 100%;
                height: auto;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            td {{
                padding: 10pt;
            }}
        </style>
        """
        
        # Cover Page - Simplified for xhtml2pdf compatibility
        cover_page = f"""
        <div class="page" style="background: linear-gradient(135deg, {color_primary} 0%, {color_purple} 100%); padding: 50pt; text-align: center; color: white;">
            <div style="padding-top: 100pt;">
                <div style="font-size: 48pt; margin-bottom: 20pt;">✈️</div>
                <div class="cover-logo" style="font-size: 32pt; margin-bottom: 30pt;">TRAVELORBIT</div>
                <div class="cover-title" style="font-size: 54pt; margin-bottom: 12pt; color: white;">Your Travel Itinerary</div>
                <div class="cover-subtitle" style="font-size: 28pt; margin-bottom: 30pt; color: {color_gold};">{duration} • {destination}</div>
                <div class="cover-details" style="font-size: 18pt; line-height: 1.8; margin-bottom: 50pt;">
                    📅 {start_date} – {end_date}<br/>
                    👥 {travelers_text}
                </div>
                <div style="margin-top: 80pt; font-size: 14pt; opacity: 0.9;">
                    Your personal AI travel companion<br/>
                    <strong>Get ready for an unforgettable journey!</strong>
                </div>
            </div>
        </div>
        """
        
        # Trip Summary Page - Simplified Structure
        amount_formatted = PDFService._format_currency(payment.amount, payment.currency)
        summary_page = f"""
        <div class="page" style="background: linear-gradient(135deg, #FFF0E6 0%, #E8F4F8 100%);">
            <div style="background: linear-gradient(90deg, {color_primary} 0%, {color_accent} 100%); color: white; padding: 20pt; text-align: center;">
                <div style="font-size: 28pt; font-weight: bold;">✨ Trip Overview</div>
            </div>
            <div style="padding: 30pt;">
                
                <div style="background: linear-gradient(135deg, {color_bg_light} 0%, {color_bg_warm} 100%); border-radius: 20pt; padding: 25pt; margin-bottom: 25pt; border: 3pt solid {color_accent};">
                    <h3 style="color: {color_primary}; margin-top: 0; font-size: 20pt;">📍 Destination</h3>
                    <p style="font-size: 26pt; font-weight: bold; color: {color_secondary}; margin-bottom: 20pt;">{destination}</p>
                    
                    <table width="100%" style="margin-bottom: 0;">
                        <tr>
                            <td width="50%" style="vertical-align: top; padding: 15pt; padding-left: 0;">
                                <h3 style="color: {color_primary}; font-size: 18pt;">📅 Dates</h3>
                                <p style="font-size: 16pt; margin-bottom: 15pt;">{start_date} - {end_date}</p>
                                
                                <h3 style="color: {color_primary}; font-size: 18pt;">⏱ Duration</h3>
                                <p style="font-size: 16pt; margin-bottom: 15pt;">{duration}</p>
                                
                                <h3 style="color: {color_primary}; font-size: 18pt;">👥 Travelers</h3>
                                <p style="font-size: 16pt;">{travelers_text}</p>
                            </td>
                            <td width="50%" style="vertical-align: top; text-align: center; padding: 25pt; background: linear-gradient(135deg, #FFE8E8 0%, #E8F4FF 100%); border-radius: 15pt;">
                                <div style="background-color: {color_green}; color: white; padding: 10pt 25pt; border-radius: 25pt; font-weight: bold; font-size: 16pt; display: inline-block; margin-bottom: 15pt;">✔ PAID</div>
                                <div style="margin-top: 15pt; font-size: 13pt; color: {color_text}; font-weight: bold;">Total Investment</div>
                                <div style="font-size: 38pt; color: {color_primary}; font-weight: bold; margin: 12pt 0;">{amount_formatted}</div>
                                <div style="margin-top: 20pt; font-size: 11pt; color: {color_accent}; font-weight: bold; letter-spacing: 2pt;">BOOKING #{booking_number}</div>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="height: 5pt; background: linear-gradient(90deg, {color_primary} 0%, {color_accent} 50%, {color_purple} 100%); margin: 25pt 0; border-radius: 3pt;"></div>
                
                <h2 style="font-size: 24pt; color: {color_secondary}; margin-bottom: 12pt; border-bottom: 4pt solid {color_gold}; padding-bottom: 8pt; display: inline-block;">✈️ Flight Information</h2>
                <div style="background: linear-gradient(135deg, {color_bg_light} 0%, #E0F7FF 100%); border: 2pt solid {color_accent}; border-radius: 15pt; padding: 20pt; margin-bottom: 20pt;">
                    <p style="font-size: 15pt; margin-bottom: 15pt;"><strong>Route Details:</strong></p>
                    <table width="100%">
                        <tr>
                            <td style="font-size: 18pt; color: {color_primary}; font-weight: bold; text-align: left;">📍 {trip.from_city or 'Origin'}</td>
                            <td align="center" style="font-size: 28pt; color: {color_primary};">✈</td>
                            <td style="font-size: 18pt; color: {color_primary}; font-weight: bold; text-align: right;">📍 {trip.to_city or 'Destination'}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin-top: 20pt;">
                    <img src="https://loremflickr.com/535/200/airport,plane,travel" style="width: 100%; border-radius: 15pt; height: 180pt; object-fit: cover;" />
                </div>
            </div>
        </div>
        """
        
        # Day by Day Pages with Enhanced Design
        itinerary_pages = ""
        if trip.ai_summary_json:
            try:
                import json
                itinerary_data = trip.ai_summary_json
                if isinstance(itinerary_data, str):
                    itinerary_data = json.loads(itinerary_data)
                
                days = itinerary_data.get("days", []) if isinstance(itinerary_data, dict) else (itinerary_data if isinstance(itinerary_data, list) else [])
                
                # Group days into pages
                current_page_days = []
                page_count = 0
                for i, day in enumerate(days):
                    current_page_days.append(day)
                    if len(current_page_days) == 2 or i == len(days) - 1:
                        page_count += 1
                        # Rotate gradient colors
                        if page_count % 2 == 0:
                            bg_gradient = "linear-gradient(135deg, #E8F4F8 0%, #FFF0E6 100%)"
                        else:
                            bg_gradient = "linear-gradient(135deg, #F0E8FF 0%, #E8F8F0 100%)"
                        
                        itinerary_pages += f'<div class="page" style="background: {bg_gradient};">'
                        itinerary_pages += f'<div class="page-header"><div class="page-header-content">🗓️ Day-by-Day Itinerary</div></div>'
                        itinerary_pages += '<div class="container" style="padding-top: 40pt;">'
                        
                        for day_idx, day_info in enumerate(current_page_days):
                            day_title = day_info.get("day", f"Day {day_idx+1}")
                            activities = day_info.get("activities", [])
                            
                            # Alternate day header gradients
                            if day_idx % 2 == 0:
                                day_gradient = f"linear-gradient(90deg, {color_secondary} 0%, {color_accent} 100%)"
                            else:
                                day_gradient = f"linear-gradient(90deg, {color_purple} 0%, {color_pink} 100%)"
                            
                            itinerary_pages += f"""
                            <div class="day-card">
                                <div class="day-header" style="background: {day_gradient}; padding: 18pt 20pt;">
                                    <strong>{day_title}</strong>
                                </div>
                                <div class="day-content">
                            """
                            
                            if isinstance(activities, list):
                                for act_idx, act in enumerate(activities):
                                    activity_name = ""
                                    activity_time = ""
                                    if isinstance(act, dict):
                                        activity_name = act.get("name", "")
                                        activity_time = act.get("time", "")
                                    else:
                                        activity_name = str(act)
                                    
                                    # Icon rotation
                                    icons = ["🌅", "🏨", "🍽️", "🎭", "🛍️", "🏖️", "🎢", "📸", "🌆"]
                                    icon = icons[act_idx % len(icons)]
                                    
                                    if activity_time:
                                        itinerary_pages += f'<div class="activity-item"><strong style="color: {color_primary}; font-size: 16pt;">{icon} {activity_time}</strong><br/><span style="color: {color_text};">{activity_name}</span></div>'
                                    else:
                                        itinerary_pages += f'<div class="activity-item"><strong style="color: {color_primary}; font-size: 16pt;">{icon}</strong> {activity_name}</div>'
                            elif isinstance(activities, str):
                                itinerary_pages += f'<div class="activity-item">{activities}</div>'
                            
                            itinerary_pages += "</div></div>"
                        
                        itinerary_pages += '</div></div>'
                        current_page_days = []
                        
            except Exception as e:
                logger.error(f"Error parsing itinerary for PDF: {e}")
        
        # Hotel & Packing Page with Full-Page Design
        hotel_page = f"""
        <div class="page" style="background: linear-gradient(135deg, #FFF0E6 0%, #FFE8E8 100%);">
            <div class="page-header">
                <div class="page-header-content">🏨 Stay & Preparation</div>
            </div>
            <div class="container" style="padding-top: 40pt;">
                
                <div style="margin-bottom: 30pt;">
                    <h2>🏨 Accommodation Details</h2>
                    <div class="hotel-box">
                        <h3 style="color: #8B6914; margin-top: 0; font-size: 24pt;">Your Recommended Stay</h3>
                        <p style="font-size: 16pt; color: {color_text}; margin-bottom: 15pt;">Check your booking confirmation for specific hotel details and contact information.</p>
                        <div style="margin-top: 15pt; border-radius: 15pt; overflow: hidden;">
                            <img src="https://loremflickr.com/535/250/hotel,luxury,bedroom" style="width: 100%; height: 200pt; object-fit: cover; border-radius: 15pt;" />
                        </div>
                    </div>
                </div>
                
                <div style="margin-bottom: 30pt;">
                    <h2>🧳 Packing Essentials</h2>
                    <table width="100%">
                        <tr>
                            <td width="50%" valign="top" style="padding-right: 15pt;">
                                <div class="packing-item">✅ Passport / ID</div>
                                <div class="packing-item">✅ Booking Confirmations</div>
                                <div class="packing-item">✅ Chargers & Powerbank</div>
                                <div class="packing-item">✅ Medications & First Aid</div>
                            </td>
                            <td width="50%" valign="top" style="padding-left: 15pt;">
                                <div class="packing-item">✅ Comfortable Shoes</div>
                                <div class="packing-item">✅ Weather-Appropriate Clothes</div>
                                <div class="packing-item">✅ Toiletries</div>
                                <div class="packing-item">✅ Cash / Credit Cards</div>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <h2>🚨 Emergency Contacts</h2>
                <div class="emergency-box">
                    <p><strong>🔴 TravelOrbit Support:</strong> +91-98765-43210</p>
                    <p><strong>🔴 Local Emergency:</strong> 112</p>
                    <p><strong>🔴 Embassy/Consulate:</strong> +91-9876-543210</p>
                </div>
            </div>
        </div>
        """
        
        # Payment Confirmation Page
        payment_page = f"""
        <div class="page" style="background: linear-gradient(135deg, #E8F8F0 0%, #E8F4F8 100%); display: flex; align-items: center; justify-content: center;">
            <div style="text-align: center; padding: 40pt; width: 100%;">
                <div style="font-size: 80pt; color: {color_green}; margin-bottom: 15pt;">✔</div>
                <h1 style="color: {color_green}; margin-bottom: 10pt; font-size: 48pt;">Payment Confirmed!</h1>
                <div style="font-size: 52pt; font-weight: bold; color: {color_primary}; margin-bottom: 40pt;">{amount_formatted}</div>
                
                <div style="background: linear-gradient(135deg, #FFFFFF 0%, {color_bg_light} 100%); display: inline-block; padding: 30pt; border-radius: 20pt; border: 3pt solid {color_accent}; text-align: left; max-width: 450pt;">
                    <p style="font-size: 16pt; margin: 12pt 0; color: {color_text};"><strong>📋 Transaction ID:</strong> <span style="font-family: monospace; color: {color_secondary};">{payment.provider_payment_id}</span></p>
                    <p style="font-size: 16pt; margin: 12pt 0; color: {color_text};"><strong>📅 Date:</strong> {payment.created_at.strftime("%d %b %Y, %I:%M %p")}</p>
                    <p style="font-size: 16pt; margin: 12pt 0; color: {color_text};"><strong>💳 Method:</strong> {payment.provider.title()}</p>
                    <p style="font-size: 16pt; margin: 12pt 0; color: {color_text};"><strong>🎫 Booking:</strong> #{booking_number}</p>
                </div>
                
                <div style="margin-top: 40pt;">
                    <p style="font-size: 14pt; color: {color_accent}; font-weight: bold;">👇 Scan QR to view full itinerary</p>
                    <div style="width: 180pt; height: 180pt; background-color: white; border: 4pt solid {color_accent}; margin: 20pt auto; display: flex; align-items: center; justify-content: center; border-radius: 10pt;">
                        <p style="color: {color_text}; font-weight: bold; font-size: 14pt;">[QR Code]</p>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Thank You Page with Full-Page Gradient
        thank_you_page = f"""
        <div class="page" style="background: linear-gradient(135deg, {color_primary} 0%, {color_purple} 50%, {color_accent} 100%); display: flex; align-items: center; justify-content: center; text-align: center;">
            <div style="padding: 50pt; color: white;">
                <div style="font-size: 64pt; margin-bottom: 20pt;">🌍</div>
                <h1 style="font-size: 54pt; color: white; margin-bottom: 15pt; font-weight: bold;">Have an Amazing Journey!</h1>
                <p style="font-size: 32pt; color: {color_gold}; font-weight: bold; margin-bottom: 25pt;">Bon Voyage</p>
                <div style="margin-top: 60pt; font-size: 16pt; color: rgba(255,255,255,0.95); line-height: 1.8;">
                    <p style="margin-bottom: 15pt;">We're excited to be part of your adventure!</p>
                    <p style="margin-bottom: 15pt;">📧 Questions? Email us: support@travelorbit.com</p>
                    <p style="margin-bottom: 15pt;">📱 Call us: +91-98765-43210</p>
                    <div style="margin-top: 40pt; font-size: 14pt; font-weight: bold; letter-spacing: 3pt;">
                        ✨ TRAVELORBIT AI ✨<br/>
                        Your Personal Travel Companion
                    </div>
                </div>
            </div>
        </div>
        """

        return f"""
        <html>
        <head>
            {css}
        </head>
        <body>
            {cover_page}
            {summary_page}
            {itinerary_pages}
            {hotel_page}
            {payment_page}
            {thank_you_page}
        </body>
        </html>
        """
