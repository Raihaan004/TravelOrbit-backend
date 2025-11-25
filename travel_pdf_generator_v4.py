"""
Enhanced Magazine-Style Travel Itinerary PDF Generator v4
Generates colorful, gradient-rich travel itineraries with AI-fetched images
"""

import io
import requests
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from PIL import Image as PILImage, ImageDraw, ImageFont, ImageEnhance

# Color Palette - Bright, Colorful, Magazine Style
COLORS = {
    'primary_gradient_1': colors.HexColor('#FF6B6B'),
    'primary_gradient_2': colors.HexColor('#4ECDC4'),
    'accent_gold': colors.HexColor('#FFD93D'),
    'accent_green': colors.HexColor('#6BCB77'),
    'accent_purple': colors.HexColor('#A8E6CF'),
    'accent_orange': colors.HexColor('#FF8C42'),
    'accent_pink': colors.HexColor('#FF69B4'),
    'accent_blue': colors.HexColor('#00D4FF'),
    'dark_text': colors.HexColor('#2C3E50'),
    'light_text': colors.white,
    'aqua_gradient': colors.HexColor('#00E5E5'),
}

class TravelPDFGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.image_cache = {}
        
    def fetch_image_from_unsplash(self, query, width=800, height=600):
        """Fetch high-quality images from Unsplash"""
        try:
            url = f"https://source.unsplash.com/{width}x{height}/?{query}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                img = PILImage.open(io.BytesIO(response.content))
                return img
            return None
        except Exception as e:
            print(f"Warning: Could not fetch image ({e})")
            return None
    
    def enhance_image_colors(self, image):
        """Enhance image brightness and contrast"""
        try:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.15)
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.25)
            
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.35)
            
            return image
        except:
            return image
    
    def create_gradient_placeholder(self, width, height, text, gradient_colors):
        """Create a beautiful gradient placeholder image"""
        try:
            img = PILImage.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Create gradient
            for i in range(height):
                ratio = i / height
                r = int(gradient_colors[0][0] * (1 - ratio) + gradient_colors[1][0] * ratio)
                g = int(gradient_colors[0][1] * (1 - ratio) + gradient_colors[1][1] * ratio)
                b = int(gradient_colors[0][2] * (1 - ratio) + gradient_colors[1][2] * ratio)
                draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font)
            return img
        except:
            return PILImage.new('RGB', (width, height), color='#FF6B6B')
    
    def get_image(self, destination, query_override=None):
        """Get image for destination"""
        cache_key = destination.lower()
        
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        query = query_override or f"{destination} travel destination scenic landscape"
        
        img = self.fetch_image_from_unsplash(query, 1000, 700)
        if img:
            img = self.enhance_image_colors(img)
        else:
            # Fallback to gradient
            gradient = [(255, 107, 107), (78, 205, 196)]
            img = self.create_gradient_placeholder(1000, 700, destination, gradient)
        
        self.image_cache[cache_key] = img
        return img
    
    def image_to_bytes(self, pil_image):
        """Convert PIL image to BytesIO"""
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def create_pdf(self, trip_data, output_path="travel_itinerary.pdf"):
        """Generate complete magazine-style PDF"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=0.3*inch,
            bottomMargin=0.3*inch,
            leftMargin=0.4*inch,
            rightMargin=0.4*inch
        )
        
        story = []
        
        # PAGE 1: COVER
        story.extend(self.create_cover_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 2: SUMMARY
        story.extend(self.create_summary_page(trip_data))
        story.append(PageBreak())
        
        # PAGES 3-7: DAY BY DAY
        for day_num, day_data in enumerate(trip_data.get('itinerary', []), 1):
            story.extend(self.create_day_page(day_num, day_data, trip_data))
            if day_num < len(trip_data.get('itinerary', [])):
                story.append(PageBreak())
        
        story.append(PageBreak())
        
        # PAGE 8: HOTEL
        story.extend(self.create_hotel_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 9: WEATHER
        story.extend(self.create_weather_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 10: PACKING
        story.extend(self.create_packing_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 11: FLIGHT
        story.extend(self.create_flight_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 12: EMERGENCY
        story.extend(self.create_emergency_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 13: CURRENCY & TIPS
        story.extend(self.create_currency_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 14: PAYMENT
        story.extend(self.create_payment_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 15: ATTACHMENTS
        story.extend(self.create_attachments_page(trip_data))
        story.append(PageBreak())
        
        # PAGE 16: THANK YOU
        story.extend(self.create_thankyou_page())
        
        doc.build(story)
        print(f"✓ PDF created successfully: {output_path}")
    
    def create_cover_page(self, trip_data):
        """Create magazine-style cover page"""
        elements = []
        
        destination = trip_data.get('destination', 'Dream Destination')
        start_date = trip_data.get('start_date', '2025-03-12')
        end_date = trip_data.get('end_date', '2025-03-16')
        travelers = trip_data.get('travelers', '2 Adults, 1 Child')
        
        # Get image
        img_pil = self.get_image(destination, "destination cover travel")
        img_bytes = self.image_to_bytes(img_pil)
        
        # Add image
        img = Image(img_bytes, width=6.8*inch, height=5*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.3*inch))
        
        # Calculate duration
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        duration = (end - start).days
        
        # Title
        title_style = ParagraphStyle(
            'CoverTitle',
            fontSize=52,
            textColor=COLORS['primary_gradient_1'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=15,
        )
        elements.append(Paragraph(f"{duration} Days • {destination}", title_style))
        
        # Subtitle
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontSize=18,
            textColor=COLORS['accent_gold'],
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=15,
        )
        elements.append(Paragraph("Your Personalized TravelOrbit Itinerary", subtitle_style))
        
        # Info
        info_style = ParagraphStyle(
            'Info',
            fontSize=12,
            textColor=COLORS['dark_text'],
            alignment=TA_CENTER,
            spaceAfter=8,
        )
        elements.append(Paragraph(f"📅 {start_date} – {end_date}", info_style))
        elements.append(Paragraph(f"👥 {travelers}", info_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Paid stamp
        paid_style = ParagraphStyle(
            'PaidStamp',
            fontSize=28,
            textColor=COLORS['accent_gold'],
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold',
        )
        elements.append(Paragraph("✓ PAID", paid_style))
        
        return elements
    
    def create_summary_page(self, trip_data):
        """Create trip summary page"""
        elements = []
        
        # Header
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['primary_gradient_1'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        elements.append(Paragraph("Trip Summary", header_style))
        
        destination = trip_data.get('destination', 'Destination')
        hotel = trip_data.get('hotel_name', 'Hotel')
        cost = trip_data.get('total_cost', '₹1,32,500')
        duration = trip_data.get('duration', '5 Days')
        package = trip_data.get('package_type', 'Luxury')
        
        # Summary table
        summary_data = [
            [Paragraph("📅 <b>Duration</b>", ParagraphStyle('', fontSize=11, textColor=COLORS['dark_text'])), 
             Paragraph(duration, ParagraphStyle('', fontSize=11, textColor=COLORS['dark_text']))],
            [Paragraph("🏨 <b>Hotel</b>", ParagraphStyle('', fontSize=11, textColor=COLORS['dark_text'])), 
             Paragraph(hotel, ParagraphStyle('', fontSize=11, textColor=COLORS['dark_text']))],
            [Paragraph("💼 <b>Package</b>", ParagraphStyle('', fontSize=11, textColor=COLORS['dark_text'])), 
             Paragraph(package, ParagraphStyle('', fontSize=11, textColor=COLORS['dark_text']))],
            [Paragraph("💰 <b>Total Cost</b>", ParagraphStyle('', fontSize=11, textColor=COLORS['dark_text'])), 
             Paragraph(f"{cost} — PAID", ParagraphStyle('', fontSize=11, textColor=COLORS['accent_green']))],
        ]
        
        table = Table(summary_data, colWidths=[2.2*inch, 4.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS['accent_purple']),
            ('BACKGROUND', (1, 0), (1, -1), COLORS['accent_pink']),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_2']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Welcome text
        welcome_style = ParagraphStyle(
            'Welcome',
            fontSize=12,
            textColor=COLORS['dark_text'],
            alignment=TA_JUSTIFY,
            leading=18,
        )
        welcome = (
            f"<b>Welcome to your dream getaway!</b><br/><br/>"
            f"This itinerary is crafted specially for your {destination} trip. "
            f"Enjoy a relaxing, picture-perfect vacation customized by TravelOrbit AI. "
            f"Every moment has been planned to ensure you have the most memorable experience."
        )
        elements.append(Paragraph(welcome, welcome_style))
        
        return elements
    
    def create_day_page(self, day_num, day_data, trip_data):
        """Create day page"""
        elements = []
        
        destination = trip_data.get('destination', 'Destination')
        title = day_data.get('title', f'Day {day_num}')
        description = day_data.get('description', 'Explore and enjoy!')
        activities = day_data.get('activities', [])
        
        # Header
        header_style = ParagraphStyle(
            'DayHeader',
            fontSize=32,
            textColor=COLORS['primary_gradient_2'],
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=20,
        )
        elements.append(Paragraph(f"DAY {day_num} — {title}", header_style))
        
        # Image
        img_pil = self.get_image(destination, f"{title} {destination} travel")
        img_bytes = self.image_to_bytes(img_pil)
        img = Image(img_bytes, width=5.5*inch, height=3.5*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.15*inch))
        
        # Description
        desc_style = ParagraphStyle(
            'Description',
            fontSize=11,
            textColor=COLORS['dark_text'],
            alignment=TA_JUSTIFY,
            leading=16,
            spaceAfter=15,
        )
        elements.append(Paragraph(description, desc_style))
        
        # Activities
        activities_style = ParagraphStyle(
            'Activity',
            fontSize=10,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        elements.append(Paragraph("<b>Activities & Timeline:</b>", activities_style))
        
        emojis = ['✈', '🚗', '🏨', '🍽', '🌅', '🏖', '🎭', '📸']
        for idx, activity in enumerate(activities):
            emoji = emojis[idx % len(emojis)]
            elements.append(Paragraph(f"{emoji} {activity}", activities_style))
        
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("<u>📍 View on Google Maps</u>", activities_style))
        
        return elements
    
    def create_hotel_page(self, trip_data):
        """Create hotel page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['accent_pink'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=25,
        )
        elements.append(Paragraph("🏨 Hotel Details", header_style))
        
        # Hotel image
        img_pil = self.get_image(trip_data.get('destination', 'Hotel'), "luxury resort hotel")
        img_bytes = self.image_to_bytes(img_pil)
        img = Image(img_bytes, width=5.5*inch, height=3.5*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.15*inch))
        
        # Hotel info
        hotel_style = ParagraphStyle(
            'HotelInfo',
            fontSize=13,
            fontName='Helvetica-Bold',
            textColor=COLORS['dark_text'],
            spaceAfter=10,
        )
        
        elements.append(Paragraph(trip_data.get('hotel_name', 'Luxury Resort'), hotel_style))
        elements.append(Paragraph(f"Rating: {trip_data.get('hotel_rating', '⭐⭐⭐⭐⭐')}", hotel_style))
        elements.append(Paragraph(f"Check-in: {trip_data.get('start_date', '2025-03-12')}", hotel_style))
        elements.append(Paragraph(f"Check-out: {trip_data.get('end_date', '2025-03-16')}", hotel_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Amenities
        elements.append(Paragraph("<b>Amenities:</b>", hotel_style))
        
        amenities_data = [
            [Paragraph("🛏 Room", ParagraphStyle('', fontSize=10, textColor=COLORS['dark_text'])),
             Paragraph("🍳 Breakfast", ParagraphStyle('', fontSize=10, textColor=COLORS['dark_text'])),
             Paragraph("🏖 Beach Access", ParagraphStyle('', fontSize=10, textColor=COLORS['dark_text']))],
            [Paragraph("🧖 Spa", ParagraphStyle('', fontSize=10, textColor=COLORS['dark_text'])),
             Paragraph("📶 WiFi", ParagraphStyle('', fontSize=10, textColor=COLORS['dark_text'])),
             Paragraph("🏋 Gym", ParagraphStyle('', fontSize=10, textColor=COLORS['dark_text']))],
        ]
        
        table = Table(amenities_data, colWidths=[2*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['accent_purple']),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_1']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Contact
        contact_style = ParagraphStyle(
            'Contact',
            fontSize=10,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        elements.append(Paragraph("<b>Contact Information:</b>", contact_style))
        elements.append(Paragraph("📞 +960 123 4567", contact_style))
        elements.append(Paragraph("🌐 www.sunislandresort.com", contact_style))
        elements.append(Paragraph("📧 reservations@sunislandresort.com", contact_style))
        
        return elements
    
    def create_weather_page(self, trip_data):
        """Create weather page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['accent_orange'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=25,
        )
        elements.append(Paragraph("🌦 Weather Forecast", header_style))
        
        weather_data = [
            [Paragraph("<b>Day</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>Condition</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>High</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>Low</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>Details</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold'))],
            [Paragraph("Day 1", ParagraphStyle('', fontSize=9)), 
             Paragraph("☀️ Sunny", ParagraphStyle('', fontSize=9)),
             Paragraph("32°C", ParagraphStyle('', fontSize=9)),
             Paragraph("26°C", ParagraphStyle('', fontSize=9)),
             Paragraph("Perfect beach", ParagraphStyle('', fontSize=9))],
            [Paragraph("Day 2", ParagraphStyle('', fontSize=9)), 
             Paragraph("🌤️ Partly Cloudy", ParagraphStyle('', fontSize=9)),
             Paragraph("31°C", ParagraphStyle('', fontSize=9)),
             Paragraph("25°C", ParagraphStyle('', fontSize=9)),
             Paragraph("Warm & pleasant", ParagraphStyle('', fontSize=9))],
            [Paragraph("Day 3", ParagraphStyle('', fontSize=9)), 
             Paragraph("⛅ Partly Cloudy", ParagraphStyle('', fontSize=9)),
             Paragraph("30°C", ParagraphStyle('', fontSize=9)),
             Paragraph("24°C", ParagraphStyle('', fontSize=9)),
             Paragraph("Light breeze", ParagraphStyle('', fontSize=9))],
            [Paragraph("Day 4", ParagraphStyle('', fontSize=9)), 
             Paragraph("🌊 Rainy", ParagraphStyle('', fontSize=9)),
             Paragraph("29°C", ParagraphStyle('', fontSize=9)),
             Paragraph("23°C", ParagraphStyle('', fontSize=9)),
             Paragraph("Afternoon rain", ParagraphStyle('', fontSize=9))],
            [Paragraph("Day 5", ParagraphStyle('', fontSize=9)), 
             Paragraph("☀️ Sunny", ParagraphStyle('', fontSize=9)),
             Paragraph("32°C", ParagraphStyle('', fontSize=9)),
             Paragraph("26°C", ParagraphStyle('', fontSize=9)),
             Paragraph("Clear skies", ParagraphStyle('', fontSize=9))],
        ]
        
        table = Table(weather_data, colWidths=[1*inch, 1.3*inch, 0.9*inch, 0.9*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_blue']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_1']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['accent_pink'], COLORS['accent_gold']]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(table)
        
        return elements
    
    def create_packing_page(self, trip_data):
        """Create packing page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['accent_pink'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=25,
        )
        elements.append(Paragraph("🧳 Packing Checklist", header_style))
        
        categories = {
            'Essential Items': ['☑ Passport & Visas', '☑ Travel Insurance', '☑ Flight Tickets', '☑ Hotel Vouchers'],
            'Clothing': ['☑ Lightweight clothes', '☑ Swim wear', '☑ Casual dresses', '☑ Evening wear'],
            'Toiletries': ['☑ Sunscreen (SPF 50+)', '☑ Moisturizer', '☑ Deodorant', '☑ Medicines'],
            'Accessories': ['☑ Sunglasses', '☑ Hat/Cap', '☑ Flip-flops', '☑ Watch'],
            'Electronics': ['☑ Phone & Charger', '☑ Camera', '☑ Power bank', '☑ Adapter'],
        }
        
        cat_style = ParagraphStyle(
            'Category',
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary_gradient_1'],
            spaceAfter=10,
        )
        
        item_style = ParagraphStyle(
            'Item',
            fontSize=10,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        for category, items in categories.items():
            elements.append(Paragraph(f"<b>{category}</b>", cat_style))
            for item in items:
                elements.append(Paragraph(item, item_style))
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def create_flight_page(self, trip_data):
        """Create flight page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['primary_gradient_1'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=25,
        )
        elements.append(Paragraph("🛫 Flight Information", header_style))
        
        flight_data = [
            [Paragraph("<b>Airline</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("Air India Express", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Flight Number</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("AI-123", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>PNR</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("ABC123XYZ", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Departure</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("12 March 2025 • 06:00 AM", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Arrival</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("12 March 2025 • 09:30 AM", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Terminal</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("Terminal 3", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Gate</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("TBD", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Baggage</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("20 kg (1 checked bag)", ParagraphStyle('', fontSize=10))],
        ]
        
        table = Table(flight_data, colWidths=[2.2*inch, 4.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS['accent_gold']),
            ('BACKGROUND', (1, 0), (1, -1), COLORS['accent_blue']),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_2']),
        ]))
        elements.append(table)
        
        return elements
    
    def create_emergency_page(self, trip_data):
        """Create emergency page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=colors.red,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=25,
        )
        elements.append(Paragraph("🚨 Emergency Contacts", header_style))
        
        contacts = [
            [Paragraph("<b>Contact</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>Number</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>Available</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold'))],
            [Paragraph("Hotel Desk", ParagraphStyle('', fontSize=9)),
             Paragraph("+960 123 4567", ParagraphStyle('', fontSize=9)),
             Paragraph("24/7", ParagraphStyle('', fontSize=9))],
            [Paragraph("TravelOrbit Support", ParagraphStyle('', fontSize=9)),
             Paragraph("+91 98765 43210", ParagraphStyle('', fontSize=9)),
             Paragraph("24/7", ParagraphStyle('', fontSize=9))],
            [Paragraph("Local Emergency", ParagraphStyle('', fontSize=9)),
             Paragraph("911", ParagraphStyle('', fontSize=9)),
             Paragraph("24/7", ParagraphStyle('', fontSize=9))],
            [Paragraph("Ambulance", ParagraphStyle('', fontSize=9)),
             Paragraph("+960 114", ParagraphStyle('', fontSize=9)),
             Paragraph("24/7", ParagraphStyle('', fontSize=9))],
            [Paragraph("Police", ParagraphStyle('', fontSize=9)),
             Paragraph("+960 119", ParagraphStyle('', fontSize=9)),
             Paragraph("24/7", ParagraphStyle('', fontSize=9))],
        ]
        
        table = Table(contacts, colWidths=[2.2*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.red),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
        ]))
        elements.append(table)
        
        return elements
    
    def create_currency_page(self, trip_data):
        """Create currency page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['accent_gold'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=25,
        )
        elements.append(Paragraph("💱 Currency & Local Tips", header_style))
        
        # Currency table
        curr_data = [
            [Paragraph("<b>INR</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>USD</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>EUR</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("<b>Local (MVR)</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold'))],
            [Paragraph("₹100", ParagraphStyle('', fontSize=9)),
             Paragraph("$1.20", ParagraphStyle('', fontSize=9)),
             Paragraph("€1.10", ParagraphStyle('', fontSize=9)),
             Paragraph("MVR 15.40", ParagraphStyle('', fontSize=9))],
            [Paragraph("₹1,000", ParagraphStyle('', fontSize=9)),
             Paragraph("$12.00", ParagraphStyle('', fontSize=9)),
             Paragraph("€11.00", ParagraphStyle('', fontSize=9)),
             Paragraph("MVR 154", ParagraphStyle('', fontSize=9))],
            [Paragraph("₹10,000", ParagraphStyle('', fontSize=9)),
             Paragraph("$120", ParagraphStyle('', fontSize=9)),
             Paragraph("€110", ParagraphStyle('', fontSize=9)),
             Paragraph("MVR 1,540", ParagraphStyle('', fontSize=9))],
        ]
        
        table = Table(curr_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_gold']),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_1']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['accent_pink'], colors.white]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tips
        tips_style = ParagraphStyle(
            'Tips',
            fontSize=11,
            textColor=COLORS['dark_text'],
            spaceAfter=10,
        )
        
        elements.append(Paragraph("<b>Local Tips & Etiquette:</b>", tips_style))
        tips = [
            "💡 Dress modestly when visiting local areas",
            "💡 Learn basic local phrases like 'Salaam' (Hello)",
            "💡 Respect local customs and traditions",
            "💡 Best SIM cards available at airport",
            "💡 Tipping is appreciated (5-10%)",
            "💡 Avoid scams: Book tours through your hotel",
        ]
        
        tip_item_style = ParagraphStyle(
            'TipItem',
            fontSize=10,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        for tip in tips:
            elements.append(Paragraph(tip, tip_item_style))
        
        return elements
    
    def create_payment_page(self, trip_data):
        """Create payment page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['accent_green'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        elements.append(Paragraph("✔ Payment Received", header_style))
        
        # Amount
        amount_style = ParagraphStyle(
            'Amount',
            fontSize=48,
            textColor=COLORS['accent_gold'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        cost = trip_data.get('total_cost', '₹1,32,500')
        elements.append(Paragraph(f"{cost}", amount_style))
        
        # Status
        status_style = ParagraphStyle(
            'Status',
            fontSize=24,
            textColor=COLORS['accent_green'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        elements.append(Paragraph("✓ PAYMENT CONFIRMED", status_style))
        
        # Payment details
        payment_data = [
            [Paragraph("<b>Payment Method</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("Razorpay", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Transaction ID</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph("pay_2A8hf7sK9L2pQx", ParagraphStyle('', fontSize=10))],
            [Paragraph("<b>Payment Date</b>", ParagraphStyle('', fontSize=10, fontName='Helvetica-Bold')),
             Paragraph(f"{datetime.now().strftime('%d %B %Y')}", ParagraphStyle('', fontSize=10))],
        ]
        
        table = Table(payment_data, colWidths=[2.2*inch, 4.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS['accent_green']),
            ('BACKGROUND', (1, 0), (1, -1), COLORS['accent_blue']),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['accent_green']),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Included
        elements.append(Paragraph("<b>Included Services:</b>", ParagraphStyle('', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['dark_text'])))
        
        services = [
            "✓ 5 Nights Accommodation at Sun Island Resort",
            "✓ Daily Breakfast & Dinner",
            "✓ Airport Transfers",
            "✓ Guided Island Tours",
            "✓ 24/7 Concierge Support",
        ]
        
        service_style = ParagraphStyle(
            'Service',
            fontSize=10,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        for service in services:
            elements.append(Paragraph(service, service_style))
        
        return elements
    
    def create_attachments_page(self, trip_data):
        """Create attachments page"""
        elements = []
        
        header_style = ParagraphStyle(
            'Header',
            fontSize=36,
            textColor=COLORS['primary_gradient_2'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=25,
        )
        elements.append(Paragraph("📎 Attachments", header_style))
        
        attachment_style = ParagraphStyle(
            'Attachment',
            fontSize=11,
            textColor=COLORS['dark_text'],
            spaceAfter=15,
        )
        
        attachments = [
            "📄 Flight E-Ticket (Air India Express)",
            "📄 Hotel Voucher (Sun Island Resort)",
            "📄 Travel Insurance Document",
            "📄 Visa Approval (if applicable)",
            "📄 Activity Booking Confirmations",
            "📄 Restaurant Reservations",
            "📄 Emergency Contact Card",
        ]
        
        for attachment in attachments:
            elements.append(Paragraph(attachment, attachment_style))
        
        return elements
    
    def create_thankyou_page(self):
        """Create thank you page"""
        elements = []
        
        elements.append(Spacer(1, 1.8*inch))
        
        thankyou_style = ParagraphStyle(
            'ThankYou',
            fontSize=56,
            textColor=COLORS['accent_pink'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=40,
        )
        elements.append(Paragraph("Have a wonderful<br/>journey!", thankyou_style))
        
        powered_style = ParagraphStyle(
            'Powered',
            fontSize=20,
            textColor=COLORS['primary_gradient_1'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=30,
        )
        elements.append(Paragraph("✈ Powered by TravelOrbit AI", powered_style))
        
        contact_style = ParagraphStyle(
            'Contact',
            fontSize=11,
            textColor=COLORS['dark_text'],
            alignment=TA_CENTER,
        )
        elements.append(Paragraph("www.travelorbit.com | support@travelorbit.com", contact_style))
        
        return elements


# Sample trip data
SAMPLE_TRIP = {
    'destination': 'Maldives',
    'start_date': '2025-03-12',
    'end_date': '2025-03-16',
    'travelers': '2 Adults, 1 Child',
    'duration': '5 Days, 4 Nights',
    'package_type': 'Honeymoon Package',
    'hotel_name': 'Sun Island Resort, Maldives',
    'hotel_rating': '⭐⭐⭐⭐⭐',
    'total_cost': '₹1,32,500',
    'itinerary': [
        {
            'title': 'Arrival in Maldives',
            'description': 'Welcome to your luxury escape! Upon arrival at Velana International Airport, our concierge will greet you. Take a scenic speedboat transfer to Sun Island Resort, check in, and enjoy a sunset welcome cocktail on the private beach.',
            'activities': ['Airport arrival', 'Speedboat transfer', 'Hotel check-in', 'Sunset cocktail', 'Beach walk'],
        },
        {
            'title': 'Water Sports & Island Exploration',
            'description': 'A day filled with adventure! Enjoy snorkeling in crystal-clear waters with tropical fish. Visit nearby islands, explore coral reefs, and experience vibrant marine life. Evening spent at the spa and dinner at the beachfront restaurant.',
            'activities': ['Snorkeling', 'Island tour', 'Reef diving', 'Spa treatment', 'Beachfront dinner'],
        },
        {
            'title': 'Leisure & Relaxation',
            'description': 'A day to unwind and rejuvenate. Enjoy breakfast on your private villa terrace, spend the day at the beach or pool. Afternoon massage at the spa, sunset fishing trip, and romantic dinner under the stars.',
            'activities': ['Breakfast terrace', 'Beach time', 'Pool relaxation', 'Spa massage', 'Sunset fishing'],
        },
        {
            'title': 'Cultural Immersion',
            'description': 'Explore the local culture! Visit the local market, taste authentic Maldivian cuisine, meet local artisans, and learn about the island\'s rich history. Evening traditional music and dance performance at the resort.',
            'activities': ['Local market visit', 'Cultural tour', 'Local cuisine', 'Artisan meeting', 'Traditional show'],
        },
        {
            'title': 'Departure Day',
            'description': 'Bid farewell to paradise. Enjoy a final breakfast with ocean views. Speedboat transfer to the airport. Carry memories of an unforgettable journey and look forward to returning for your next TravelOrbit destination!',
            'activities': ['Final breakfast', 'Souvenir shopping', 'Speedboat transfer', 'Airport check-in', 'Departure'],
        },
    ]
}


if __name__ == "__main__":
    print("Generating magazine-style travel itinerary PDF...")
    generator = TravelPDFGenerator()
    generator.create_pdf(SAMPLE_TRIP, "travel_itinerary_magazine.pdf")
