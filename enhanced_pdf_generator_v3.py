"""
Enhanced Magazine-Style Travel Itinerary PDF Generator
Generates colorful, gradient-rich travel itineraries with AI-fetched images
"""

import io
import requests
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from PIL import Image as PILImage, ImageDraw, ImageFont, ImageFilter
import textwrap

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

# Color hex values for text (without # prefix)
COLOR_HEX = {
    'primary_gradient_1': 'FF6B6B',
    'primary_gradient_2': '4ECDC4',
    'accent_gold': 'FFD93D',
    'accent_green': '6BCB77',
    'accent_purple': 'A8E6CF',
    'accent_orange': 'FF8C42',
    'accent_pink': 'FF69B4',
    'accent_blue': '00D4FF',
    'dark_text': '2C3E50',
    'light_text': 'FFFFFF',
    'aqua_gradient': '00E5E5',
}

class EnhancedTravelPDFGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.elements = []
        self.image_cache = {}
        
    def fetch_image_from_unsplash(self, query, width=800, height=600):
        """Fetch high-quality images from Unsplash based on search query"""
        try:
            # Unsplash API key (using demo - in production use valid API key)
            url = f"https://source.unsplash.com/{width}x{height}/?{query}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                img = PILImage.open(io.BytesIO(response.content))
                return img
            return None
        except Exception as e:
            print(f"Error fetching image: {e}")
            return None
    
    def create_gradient_overlay_image(self, base_image, overlay_color=(0, 0, 0, 100)):
        """Add gradient overlay to enhance contrast"""
        try:
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            # Create gradient overlay
            overlay = PILImage.new('RGBA', base_image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            for i in range(base_image.size[1]):
                alpha = int((i / base_image.size[1]) * 120)
                overlay_draw.rectangle(
                    [(0, i), (base_image.size[0], i+1)],
                    fill=(0, 0, 0, alpha)
                )
            
            base_image.paste(overlay, (0, 0), overlay)
            return base_image
        except Exception as e:
            print(f"Error creating overlay: {e}")
            return base_image
    
    def enhance_image_colors(self, image):
        """Enhance image brightness and contrast"""
        from PIL import ImageEnhance
        try:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.3)
            
            return image
        except Exception as e:
            print(f"Error enhancing image: {e}")
            return image
    
    def create_placeholder_image(self, width, height, text, gradient_colors):
        """Create a beautiful gradient placeholder image"""
        try:
            img = PILImage.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Create gradient background
            for i in range(height):
                ratio = i / height
                r = int(gradient_colors[0][0] * (1 - ratio) + gradient_colors[1][0] * ratio)
                g = int(gradient_colors[0][1] * (1 - ratio) + gradient_colors[1][1] * ratio)
                b = int(gradient_colors[0][2] * (1 - ratio) + gradient_colors[1][2] * ratio)
                draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
            
            # Add text
            try:
                font_size = 60
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font)
            return img
        except Exception as e:
            print(f"Error creating placeholder: {e}")
            return PILImage.new('RGB', (width, height), color='white')
    
    def get_destination_image(self, destination, query_override=None):
        """Get image for destination with fallback to placeholder"""
        cache_key = destination.lower()
        
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        query = query_override or f"{destination} travel destination beach landscape"
        
        try:
            img = self.fetch_image_from_unsplash(query, 1200, 900)
            if img:
                img = self.enhance_image_colors(img)
                self.image_cache[cache_key] = img
                return img
        except Exception as e:
            print(f"Could not fetch image for {destination}: {e}")
        
        # Fallback to colorful gradient placeholder
        gradient = [(255, 107, 107), (78, 205, 196)]  # Coral to Teal
        placeholder = self.create_placeholder_image(1200, 900, destination, gradient)
        self.image_cache[cache_key] = placeholder
        return placeholder
    
    def create_pdf(self, trip_data, output_path="travel_itinerary.pdf"):
        """Generate complete magazine-style PDF"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=0,
            bottomMargin=0,
            leftMargin=0,
            rightMargin=0
        )
        
        story = []
        
        # PAGE 1: COVER PAGE
        story.append(self._create_cover_page(trip_data))
        
        # PAGE 2: TRIP SUMMARY
        story.append(PageBreak())
        story.append(self._create_summary_page(trip_data))
        
        # PAGE 3-7: DAY BY DAY PLANS
        for day_num, day_data in enumerate(trip_data.get('itinerary', []), 1):
            story.append(PageBreak())
            story.append(self._create_day_page(day_num, day_data, trip_data))
        
        # PAGE 8: HOTEL DETAILS
        story.append(PageBreak())
        story.append(self._create_hotel_page(trip_data))
        
        # PAGE 9: WEATHER FORECAST
        story.append(PageBreak())
        story.append(self._create_weather_page(trip_data))
        
        # PAGE 10: PACKING CHECKLIST
        story.append(PageBreak())
        story.append(self._create_packing_page(trip_data))
        
        # PAGE 11: FLIGHT INFORMATION
        story.append(PageBreak())
        story.append(self._create_flight_page(trip_data))
        
        # PAGE 12: EMERGENCY CONTACTS
        story.append(PageBreak())
        story.append(self._create_emergency_page(trip_data))
        
        # PAGE 13: CURRENCY & TIPS
        story.append(PageBreak())
        story.append(self._create_currency_page(trip_data))
        
        # PAGE 14: PAYMENT DETAILS
        story.append(PageBreak())
        story.append(self._create_payment_page(trip_data))
        
        # PAGE 15: ATTACHMENTS
        story.append(PageBreak())
        story.append(self._create_attachments_page(trip_data))
        
        # PAGE 16: THANK YOU
        story.append(PageBreak())
        story.append(self._create_thankyou_page())
        
        doc.build(story)
        print(f"PDF generated: {output_path}")
    
    def _create_cover_page(self, trip_data):
        """Create magazine-style cover page"""
        destination = trip_data.get('destination', 'Dream Destination')
        start_date = trip_data.get('start_date', '2025-03-12')
        end_date = trip_data.get('end_date', '2025-03-16')
        travelers = trip_data.get('travelers', '2 Adults, 1 Child')
        
        # Get destination image
        img = self.get_destination_image(destination)
        
        # Create temporary image file
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        story = []
        
        # Add main image
        img_obj = Image(img_io, width=7.5*inch, height=5.5*inch)
        story.append(img_obj)
        
        # Title with gradient effect (simulated with colored text)
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=48,
            textColor=COLORS['light_text'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=20,
        )
        
        duration_days = (datetime.strptime(end_date, '%Y-%m-%d') - 
                        datetime.strptime(start_date, '%Y-%m-%d')).days
        
        title = Paragraph(
            f"{duration_days} Days • {destination}<br/>Luxury Escape",
            title_style
        )
        story.append(title)
        
        # Subtitle
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=18,
            textColor=COLORS['accent_gold'],
            alignment=TA_CENTER,
            fontName='Helvetica',
        )
        
        subtitle = Paragraph(
            "Your Personalized TravelOrbit Itinerary",
            subtitle_style
        )
        story.append(subtitle)
        
        # Travel dates
        dates_style = ParagraphStyle(
            'Dates',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            textColor=COLORS['light_text'],
            alignment=TA_CENTER,
        )
        
        dates_text = Paragraph(
            f"{start_date} – {end_date}",
            dates_style
        )
        story.append(dates_text)
        
        # Number of travelers
        travelers_text = Paragraph(
            travelers,
            dates_style
        )
        story.append(travelers_text)
        
        # Paid stamp (simulated)
        paid_style = ParagraphStyle(
            'PaidStamp',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=24,
            textColor=COLORS['accent_gold'],
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold',
        )
        
        paid_stamp = Paragraph("✓ PAID", paid_style)
        story.append(paid_stamp)
        
        return story
    
    def _create_summary_page(self, trip_data):
        """Create trip summary page with gradient cards"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['primary_gradient_1'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("Trip Summary", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary data
        destination = trip_data.get('destination', 'Destination')
        hotel = trip_data.get('hotel_name', 'Hotel Resort')
        cost = trip_data.get('total_cost', '₹1,32,500')
        duration = trip_data.get('duration', '5 Days, 4 Nights')
        package_type = trip_data.get('package_type', 'Luxury')
        
        # Create summary boxes as table
        summary_data = [
            [f"📅 Duration", f"{duration}"],
            [f"🏨 Hotel", f"{hotel}"],
            [f"💼 Package", f"{package_type}"],
            [f"💰 Total Cost", f"{cost} — PAID"],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS['accent_purple']),
            ('BACKGROUND', (1, 0), (1, -1), COLORS['accent_blue']),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS['dark_text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_2']),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [COLORS['accent_pink'], COLORS['accent_gold']])
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Welcome text
        welcome_style = ParagraphStyle(
            'Welcome',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=12,
            textColor=COLORS['dark_text'],
            alignment=TA_JUSTIFY,
            spaceAfter=20,
            leading=18,
        )
        
        welcome_text = Paragraph(
            f"<b>Welcome to your dream getaway!</b><br/>"
            f"This itinerary is crafted specially for your {destination} trip. "
            f"Enjoy a relaxing, picture-perfect vacation customized by TravelOrbit AI. "
            f"Every moment has been planned to ensure you have the most memorable experience.",
            welcome_style
        )
        story.append(welcome_text)
        
        return story
    
    def _create_day_page(self, day_num, day_data, trip_data):
        """Create day-by-day itinerary page"""
        story = []
        
        destination = trip_data.get('destination', 'Destination')
        day_title = day_data.get('title', f'Day {day_num}')
        activities = day_data.get('activities', ['Activity 1', 'Activity 2', 'Activity 3'])
        description = day_data.get('description', 'Explore and enjoy your day!')
        
        # Day header with gradient background (simulated with colored paragraph)
        header_style = ParagraphStyle(
            'DayHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=32,
            textColor=COLORS['light_text'],
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=20,
        )
        
        day_header = Paragraph(
            f"<font color='#{COLOR_HEX['primary_gradient_1']}'>DAY {day_num}</font> — {day_title}",
            header_style
        )
        story.append(day_header)
        
        # Get a scenic image for the day
        query = f"{destination} {day_title.lower()} travel"
        img = self.get_destination_image(destination, query)
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        img_obj = Image(img_io, width=6*inch, height=3*inch)
        story.append(img_obj)
        story.append(Spacer(1, 0.15*inch))
        
        # Description
        desc_style = ParagraphStyle(
            'Description',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=11,
            textColor=COLORS['dark_text'],
            alignment=TA_JUSTIFY,
            spaceAfter=15,
            leading=16,
        )
        
        story.append(Paragraph(description, desc_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Activities timeline with emojis
        activities_style = ParagraphStyle(
            'Activities',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        story.append(Paragraph("<b>Activities & Timeline:</b>", activities_style))
        
        emojis = ['✈', '🚗', '🏨', '🍽', '🌅', '🏖', '🎭', '📸']
        for idx, activity in enumerate(activities):
            emoji = emojis[idx % len(emojis)]
            story.append(Paragraph(f"{emoji} {activity}", activities_style))
        
        story.append(Spacer(1, 0.1*inch))
        
        # Map link button (simulated)
        map_style = ParagraphStyle(
            'MapLink',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            textColor=COLORS['accent_blue'],
            alignment=TA_LEFT,
        )
        
        story.append(Paragraph(
            "<u>📍 View on Google Maps</u>",
            map_style
        ))
        
        return story
    
    def _create_hotel_page(self, trip_data):
        """Create hotel details page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['primary_gradient_2'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("Hotel Details", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Hotel image
        img = self.get_destination_image(trip_data.get('destination', 'Hotel'), "luxury hotel resort")
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        img_obj = Image(img_io, width=6*inch, height=3.5*inch)
        story.append(img_obj)
        story.append(Spacer(1, 0.2*inch))
        
        # Hotel info
        hotel_name = trip_data.get('hotel_name', 'Luxury Resort')
        rating = trip_data.get('hotel_rating', '⭐⭐⭐⭐⭐')
        checkin = trip_data.get('start_date', '2025-03-12')
        checkout = trip_data.get('end_date', '2025-03-16')
        
        info_style = ParagraphStyle(
            'HotelInfo',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            textColor=COLORS['dark_text'],
            fontName='Helvetica-Bold',
            spaceAfter=10,
        )
        
        story.append(Paragraph(f"<b>{hotel_name}</b>", info_style))
        story.append(Paragraph(f"Rating: {rating}", info_style))
        story.append(Paragraph(f"Check-in: {checkin}", info_style))
        story.append(Paragraph(f"Check-out: {checkout}", info_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Amenities
        amenities_style = ParagraphStyle(
            'Amenities',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=11,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        story.append(Paragraph("<b>Amenities:</b>", amenities_style))
        
        amenities_data = [
            ['🛏 Room', '🍳 Breakfast', '🏖 Beach Access'],
            ['🧖 Spa', '📶 Free WiFi', '🏋 Gym'],
            ['🎾 Sports', '🍷 Bar & Lounge', '🎰 Casino'],
        ]
        
        amenities_table = Table(amenities_data, colWidths=[2*inch, 2*inch, 2*inch])
        amenities_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['accent_purple']),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS['dark_text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_1']),
        ]))
        
        story.append(amenities_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Contact info
        contact_style = ParagraphStyle(
            'Contact',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        story.append(Paragraph("<b>Contact Information:</b>", contact_style))
        story.append(Paragraph("📞 +960 123 4567", contact_style))
        story.append(Paragraph("🌐 www.sunislandresort.com", contact_style))
        story.append(Paragraph("📧 reservations@sunislandresort.com", contact_style))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("<u>📍 View on Google Maps</u>", contact_style))
        
        return story
    
    def _create_weather_page(self, trip_data):
        """Create weather forecast page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['accent_orange'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("Weather Forecast", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Sample weather data
        weather_data = [
            ['Day', 'Condition', 'High', 'Low', 'Details'],
            ['Day 1', '☀️ Sunny', '32°C', '26°C', 'Perfect beach day'],
            ['Day 2', '🌤️ Partly Cloudy', '31°C', '25°C', 'Warm and pleasant'],
            ['Day 3', '⛅ Partly Cloudy', '30°C', '24°C', 'Light breeze'],
            ['Day 4', '🌊 Rainy', '29°C', '23°C', 'Afternoon showers'],
            ['Day 5', '☀️ Sunny', '32°C', '26°C', 'Clear skies return'],
        ]
        
        weather_table = Table(weather_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 1*inch, 1.8*inch])
        weather_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_blue']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['light_text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_1']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['accent_pink'], COLORS['accent_gold']])
        ]))
        
        story.append(weather_table)
        
        return story
    
    def _create_packing_page(self, trip_data):
        """Create packing checklist page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['accent_pink'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("Packing Checklist", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Checklist items
        checklist_style = ParagraphStyle(
            'ChecklistItem',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=11,
            textColor=COLORS['dark_text'],
            spaceAfter=10,
            leading=16,
        )
        
        categories = {
            'Essential Items': ['☑ Passport & Visas', '☑ Travel Insurance', '☑ Flight Tickets', '☑ Hotel Vouchers'],
            'Clothing': ['☑ Lightweight clothes', '☑ Swim wear', '☑ Casual dresses', '☑ Evening wear'],
            'Toiletries': ['☑ Sunscreen (SPF 50+)', '☑ Moisturizer', '☑ Deodorant', '☑ Medications'],
            'Accessories': ['☑ Sunglasses', '☑ Hat/Cap', '☑ Flip-flops', '☑ Watch'],
            'Electronics': ['☑ Phone & Charger', '☑ Camera', '☑ Power bank', '☑ Adapter'],
        }
        
        for category, items in categories.items():
            story.append(Paragraph(f"<b>{category}</b>", checklist_style))
            for item in items:
                story.append(Paragraph(item, checklist_style))
            story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _create_flight_page(self, trip_data):
        """Create flight information page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['primary_gradient_1'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("Flight Information", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Flight details as boarding pass style
        flight_data = [
            ['Airline', 'Air India Express'],
            ['Flight Number', 'AI-123'],
            ['PNR', 'ABC123XYZ'],
            ['Departure', '12 March 2025 • 06:00 AM'],
            ['Arrival', '12 March 2025 • 09:30 AM'],
            ['Terminal', 'Terminal 3'],
            ['Gate', 'TBD'],
            ['Baggage Allowance', '20 kg (1 checked bag)'],
        ]
        
        flight_table = Table(flight_data, colWidths=[2.5*inch, 4*inch])
        flight_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS['accent_gold']),
            ('BACKGROUND', (1, 0), (1, -1), COLORS['accent_blue']),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS['dark_text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_2']),
        ]))
        
        story.append(flight_table)
        
        return story
    
    def _create_emergency_page(self, trip_data):
        """Create emergency contacts page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=colors.red,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("🚨 Emergency Contacts", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        contacts_data = [
            ['Contact Type', 'Phone Number', 'Available'],
            ['Hotel Desk', '+960 123 4567', '24/7'],
            ['TravelOrbit Support', '+91 98765 43210', '24/7'],
            ['Local Emergency', '911', '24/7'],
            ['Ambulance', '+960 114', '24/7'],
            ['Police', '+960 119', '24/7'],
            ['Embassy', '+960 330 1960', 'Mon-Fri'],
        ]
        
        contacts_table = Table(contacts_data, colWidths=[2*inch, 2.5*inch, 1.5*inch])
        contacts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['light_text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.red),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
        ]))
        
        story.append(contacts_table)
        
        return story
    
    def _create_currency_page(self, trip_data):
        """Create currency and local tips page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['accent_gold'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("💱 Currency & Local Tips", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Currency conversion
        currency_data = [
            ['INR', 'USD', 'EUR', 'Local (MVR)'],
            ['₹100', '$1.20', '€1.10', 'MVR 15.40'],
            ['₹1,000', '$12.00', '€11.00', 'MVR 154'],
            ['₹10,000', '$120', '€110', 'MVR 1,540'],
        ]
        
        currency_table = Table(currency_data, colWidths=[1.75*inch, 1.75*inch, 1.75*inch, 1.75*inch])
        currency_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent_gold']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['dark_text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['primary_gradient_1']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['accent_pink'], COLORS['accent_gold']])
        ]))
        
        story.append(currency_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Local tips
        tips_style = ParagraphStyle(
            'Tips',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=11,
            textColor=COLORS['dark_text'],
            spaceAfter=10,
            leading=16,
        )
        
        story.append(Paragraph("<b>Local Tips & Etiquette:</b>", tips_style))
        story.append(Paragraph("💡 Dress modestly when visiting local areas", tips_style))
        story.append(Paragraph("💡 Learn basic local phrases like 'Salaam' (Hello)", tips_style))
        story.append(Paragraph("💡 Respect local customs and traditions", tips_style))
        story.append(Paragraph("💡 Best SIM cards available at airport", tips_style))
        story.append(Paragraph("💡 Tipping is appreciated (5-10%)", tips_style))
        story.append(Paragraph("💡 Avoid scams: Book tours through your hotel", tips_style))
        
        return story
    
    def _create_payment_page(self, trip_data):
        """Create payment details page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['accent_green'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("✔ Payment Received", header_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Amount box
        amount_style = ParagraphStyle(
            'Amount',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=48,
            textColor=COLORS['accent_gold'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        
        cost = trip_data.get('total_cost', '₹1,32,500')
        story.append(Paragraph(f"{cost} — <font color='green'>PAID</font>", amount_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Payment details
        payment_data = [
            ['Payment Method', 'Razorpay'],
            ['Transaction ID', 'pay_2A8hf7sK9L2pQx'],
            ['Payment Date', f"{datetime.now().strftime('%d %B %Y')}"],
            ['Status', 'Confirmed ✓'],
        ]
        
        payment_table = Table(payment_data, colWidths=[2.5*inch, 4*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS['accent_green']),
            ('BACKGROUND', (1, 0), (1, -1), COLORS['accent_blue']),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS['dark_text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['accent_green']),
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Included services
        services_style = ParagraphStyle(
            'Services',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=11,
            textColor=COLORS['dark_text'],
            spaceAfter=8,
        )
        
        story.append(Paragraph("<b>Included Services:</b>", services_style))
        story.append(Paragraph("✓ 5 Nights Accommodation at Sun Island Resort", services_style))
        story.append(Paragraph("✓ Daily Breakfast & Dinner", services_style))
        story.append(Paragraph("✓ Airport Transfers", services_style))
        story.append(Paragraph("✓ Guided Island Tours", services_style))
        story.append(Paragraph("✓ 24/7 Concierge Support", services_style))
        
        return story
    
    def _create_attachments_page(self, trip_data):
        """Create attachments page"""
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'PageHeader',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=36,
            textColor=COLORS['primary_gradient_2'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("📎 Attachments", header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Attachments list with icons
        attachment_style = ParagraphStyle(
            'Attachment',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=12,
            textColor=COLORS['dark_text'],
            spaceAfter=15,
            leading=20,
        )
        
        story.append(Paragraph("📄 Flight E-Ticket (Air India Express)", attachment_style))
        story.append(Paragraph("📄 Hotel Voucher (Sun Island Resort)", attachment_style))
        story.append(Paragraph("📄 Travel Insurance Document", attachment_style))
        story.append(Paragraph("📄 Visa Approval (if applicable)", attachment_style))
        story.append(Paragraph("📄 Activity Booking Confirmations", attachment_style))
        story.append(Paragraph("📄 Restaurant Reservations", attachment_style))
        
        return story
    
    def _create_thankyou_page(self):
        """Create thank you page with gradient background"""
        story = []
        
        # Create a spacer to push content to center
        story.append(Spacer(1, 1.5*inch))
        
        # Thank you text
        thankyou_style = ParagraphStyle(
            'ThankYou',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=56,
            textColor=COLORS['accent_pink'],
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story.append(Paragraph("Have a wonderful<br/>journey!", thankyou_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Powered by
        powered_style = ParagraphStyle(
            'Powered',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=18,
            textColor=COLORS['primary_gradient_1'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )
        
        story.append(Paragraph("✈ Powered by TravelOrbit AI", powered_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Social media / contact
        contact_style = ParagraphStyle(
            'Contact',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            textColor=COLORS['dark_text'],
            alignment=TA_CENTER,
        )
        
        story.append(Paragraph("www.travelorbit.com | support@travelorbit.com", contact_style))
        
        return story


# Sample data structure for trip
SAMPLE_TRIP_DATA = {
    'destination': 'Maldives',
    'start_date': '2025-03-12',
    'end_date': '2025-03-16',
    'travelers': '2 Adults, 1 Child',
    'duration': '5 Days, 4 Nights',
    'package_type': 'Honeymoon',
    'hotel_name': 'Sun Island Resort, Maldives',
    'hotel_rating': '⭐⭐⭐⭐⭐',
    'total_cost': '₹1,32,500',
    'payment_id': 'pay_2A8hf7sK9L2pQx',
    'itinerary': [
        {
            'title': 'Arrival in Maldives',
            'description': 'Welcome to your luxury escape! Upon arrival at Velana International Airport, our concierge will greet you with refreshments. Take a scenic speedboat transfer to Sun Island Resort, check in, and enjoy a sunset welcome cocktail on the private beach.',
            'activities': ['Airport arrival', 'Speedboat transfer', 'Hotel check-in', 'Sunset cocktail', 'Beach walk'],
        },
        {
            'title': 'Water Sports & Island Exploration',
            'description': 'A day filled with adventure! Enjoy snorkeling in crystal-clear waters teeming with tropical fish. Visit nearby islands, explore coral reefs, and experience the vibrant marine life. Evening spent at the spa and dinner at the beachfront restaurant.',
            'activities': ['Snorkeling', 'Island tour', 'Reef diving', 'Spa treatment', 'Beachfront dinner'],
        },
        {
            'title': 'Leisure & Relaxation',
            'description': 'A day to unwind and rejuvenate. Enjoy breakfast on your private villa terrace, spend the day at the beach or by the pool. Afternoon massage at the spa, sunset fishing trip, and romantic dinner under the stars.',
            'activities': ['Breakfast terrace', 'Beach time', 'Pool relaxation', 'Spa massage', 'Sunset fishing'],
        },
        {
            'title': 'Cultural Immersion',
            'description': 'Explore the local culture! Visit the local market, taste authentic Maldivian cuisine, meet local artisans, and learn about the island\'s rich history. Evening traditional music and dance performance at the resort.',
            'activities': ['Local market visit', 'Cultural tour', 'Local cuisine', 'Artisan meeting', 'Traditional show'],
        },
        {
            'title': 'Departure Day',
            'description': 'Bid farewell to paradise. Enjoy a final breakfast with ocean views. Speedboat transfer to the airport. Carry memories of an unforgettable journey and look forward to returning to TravelOrbit\'s next destination!',
            'activities': ['Final breakfast', 'Souvenir shopping', 'Speedboat transfer', 'Airport check-in', 'Departure'],
        },
    ]
}


if __name__ == "__main__":
    # Generate the PDF
    generator = EnhancedTravelPDFGenerator()
    generator.create_pdf(SAMPLE_TRIP_DATA, "travel_itinerary_enhanced.pdf")
    print("✓ Enhanced magazine-style travel itinerary PDF created successfully!")
