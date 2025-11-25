import io
import logging
import requests
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from PIL import Image as PILImage, ImageDraw, ImageFont, ImageEnhance
from reportlab.graphics.barcode import code128

from app.config import settings
from trip_plan.models import Trip, Payment

logger = logging.getLogger(__name__)

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
    'ticket_bg': colors.HexColor('#F8F9FA'),
    'ticket_border': colors.HexColor('#E9ECEF'),
}

class TravelPDFGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.image_cache = {}
        self.styles = getSampleStyleSheet()
        
    def fetch_image_from_unsplash(self, query, width=800, height=600):
        """Fetch high-quality images from LoremFlickr (more reliable than Unsplash source)"""
        try:
            # Use a proper user agent
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            
            # Clean query for url (comma separated keywords)
            # Ensure we always have nature/place related terms
            base_keywords = query.replace(" ", ",")
            # Add fallback/context keywords to ensure nature/place relevance
            final_keywords = f"{base_keywords},nature,landmark,scenic,travel"
            
            url = f"https://loremflickr.com/{width}/{height}/{final_keywords}"
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                img = PILImage.open(io.BytesIO(response.content))
                return img
            return None
        except Exception as e:
            logger.warning(f"Warning: Could not fetch image ({e})")
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
                font = ImageFont.load_default()
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
    
    def get_image(self, destination, query_override=None, width=800, height=600):
        """Get image for destination"""
        cache_key = f"{destination}_{query_override}_{width}_{height}".lower()
        
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        query = query_override or f"{destination} travel destination scenic landscape"
        
        img = self.fetch_image_from_unsplash(query, width, height)
        if img:
            img = self.enhance_image_colors(img)
        else:
            # Fallback to gradient
            gradient = [(255, 107, 107), (78, 205, 196)]
            img = self.create_gradient_placeholder(width, height, destination, gradient)
        
        self.image_cache[cache_key] = img
        return img
    
    def image_to_bytes(self, pil_image):
        """Convert PIL image to BytesIO"""
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def generate_bytes(self, trip_data):
        """Generate complete magazine-style PDF in 2 pages and return bytes"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.2*inch,
            bottomMargin=0.2*inch,
            leftMargin=0.3*inch,
            rightMargin=0.3*inch
        )
        
        story = []
        
        # --- PAGE 1 ---
        # 1. Cover Section (Top 30%)
        story.append(self.create_cover_section(trip_data))
        story.append(Spacer(1, 0.1*inch))
        
        # 2. Summary Section (Compact)
        story.append(self.create_summary_section(trip_data))
        story.append(Spacer(1, 0.15*inch))

        # 3. Fake Ticket (Boarding Pass) - Visual Highlight
        story.append(self.create_boarding_pass(trip_data))
        story.append(Spacer(1, 0.15*inch))
        
        # 4. Day by Day (All Days - Flow naturally)
        # Calculate total days to ensure all are included without forced breaks
        itinerary_len = len(trip_data.get('itinerary', []))
        # Use a large number to cover all days, min() in the function handles the limit
        story.append(self.create_itinerary_section(trip_data, start_day=1, end_day=itinerary_len + 5))
        
        story.append(Spacer(1, 0.1*inch))
        
        # 6. Hotel & Weather (Middle 20%)
        story.append(self.create_hotel_weather_section(trip_data))
        story.append(Spacer(1, 0.1*inch))
        
        # 7. Packing & Currency (Middle 20%)
        story.append(self.create_packing_currency_section(trip_data))
        story.append(Spacer(1, 0.1*inch))
        
        # 8. Footer Info (Emergency, Payment, Attachments) (Bottom 20%)
        story.append(self.create_footer_info_section(trip_data))
        story.append(Spacer(1, 0.1*inch))
        
        # 9. Thank You
        story.append(self.create_thank_you_section())
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def create_cover_section(self, trip_data):
        destination = trip_data.get('destination', 'Dream Destination')
        start_date = trip_data.get('start_date', 'TBD')
        end_date = trip_data.get('end_date', 'TBD')
        travelers = trip_data.get('travelers', 'Travelers')
        duration = trip_data.get('duration', 'Trip')
        
        # Image
        # Check for static cover image first (app/static/cover_image.jpeg)
        img_pil = None
        static_cover_path = os.path.join(os.path.dirname(__file__), 'static', 'cover_image.jpeg')
        
        if os.path.exists(static_cover_path):
            try:
                img_pil = PILImage.open(static_cover_path)
                # Resize/Crop to fit aspect ratio if needed, but let's just load it
            except Exception as e:
                logger.warning(f"Could not load static cover image: {e}")
        
        if not img_pil:
            img_pil = self.get_image(destination, "destination cover travel", 1200, 500)
            
        img_bytes = self.image_to_bytes(img_pil)
        img = Image(img_bytes, width=7.5*inch, height=2.8*inch)
        
        # Text Overlay (Simulated with Table)
        title_style = ParagraphStyle('CoverTitle', fontSize=32, textColor=COLORS['primary_gradient_1'], fontName='Helvetica-Bold', alignment=TA_CENTER, leading=40)
        subtitle_style = ParagraphStyle('Subtitle', fontSize=14, textColor=COLORS['accent_gold'], fontName='Helvetica', alignment=TA_CENTER, leading=20)
        info_style = ParagraphStyle('Info', fontSize=10, textColor=COLORS['dark_text'], alignment=TA_CENTER, leading=14)
        
        text_content = [
            Paragraph(f"{duration} • {destination} Luxury Escape", title_style),
            Paragraph("Your Personalized TravelOrbit Itinerary", subtitle_style),
            Paragraph(f"📅 {start_date} – {end_date} • 👥 {travelers}", info_style),
        ]
        
        # Paid Stamp
        paid_style = ParagraphStyle('Paid', fontSize=14, textColor=COLORS['accent_green'], fontName='Helvetica-Bold', alignment=TA_RIGHT)
        text_content.append(Paragraph("✓ PAID", paid_style))
        
        return Table([[img], [Table([[c] for c in text_content], style=TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5)
        ]))]], 
        style=TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))

    def create_summary_section(self, trip_data):
        # Summary
        summary_style = ParagraphStyle('Sum', fontSize=10, leading=12)
        summary_header = ParagraphStyle('SumHead', fontSize=12, fontName='Helvetica-Bold', textColor=COLORS['primary_gradient_1'])
        
        # Create a horizontal summary bar
        data = [
            [
                Paragraph("<b>QUICK SUMMARY</b>", summary_header),
                Paragraph(f"<b>Duration:</b><br/>{trip_data.get('duration', '5 Days')}", summary_style),
                Paragraph(f"<b>Package:</b><br/>{trip_data.get('package_type', 'Luxury')}", summary_style),
                Paragraph(f"<b>Hotel:</b><br/>{trip_data.get('hotel_name', 'Recommended Hotel')}", summary_style),
                Paragraph(f"<b>Total Cost:</b><br/>{trip_data.get('total_cost', 'Paid')}", summary_style),
            ]
        ]
        
        t = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), COLORS['ticket_bg']),
            ('BOX', (0,0), (-1,-1), 1, COLORS['primary_gradient_2']),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        return t

    def create_boarding_pass(self, trip_data):
        """Create a realistic-looking fake boarding pass"""
        
        # Styles
        label_style = ParagraphStyle('BPLabel', fontSize=7, textColor='grey', fontName='Helvetica')
        value_style = ParagraphStyle('BPValue', fontSize=10, textColor='black', fontName='Helvetica-Bold')
        
        # Data
        airline = "Air India Express" # Placeholder
        flight_no = "AI-123" # Placeholder
        pnr = trip_data.get('booking_number', 'ABC123XYZ')
        date = trip_data.get('start_date', '12 MAR 2025')
        time = "06:00 AM" # Placeholder
        gate = "A4"
        
        # Generate seats based on travelers
        travelers_str = trip_data.get('travelers', '1 Adult')
        try:
            count = int(travelers_str.split()[0])
        except:
            count = 1
            
        seats = []
        base_row = 12
        chars = ['A', 'B', 'C', 'D', 'E', 'F']
        for i in range(count):
            seats.append(f"{base_row}{chars[i % 6]}")
            if (i + 1) % 6 == 0:
                base_row += 1
        seat_str = ", ".join(seats)
        
        # Barcode - Reduced width to fit
        try:
            barcode = code128.Code128(pnr, barHeight=0.35*inch, barWidth=0.9)
        except:
            barcode = Paragraph("[BARCODE]", value_style)
        
        # Left Section (Main Ticket)
        left_data = [
            [Paragraph(f"✈ {airline}", ParagraphStyle('Air', fontSize=12, fontName='Helvetica-Bold', textColor=COLORS['primary_gradient_2'])), '', '', Paragraph("BOARDING PASS", ParagraphStyle('BPTitle', fontSize=10, alignment=TA_RIGHT, textColor='grey'))],
            [Paragraph("PASSENGER NAME", label_style), Paragraph("FLIGHT", label_style), Paragraph("DATE", label_style), Paragraph("TIME", label_style)],
            [Paragraph(trip_data.get('travelers', 'Guest').split(',')[0], value_style), Paragraph(flight_no, value_style), Paragraph(date, value_style), Paragraph(time, value_style)],
            [Paragraph("FROM", label_style), Paragraph("TO", label_style), Paragraph("GATE", label_style), Paragraph("SEAT", label_style)],
            [Paragraph("ORIGIN", value_style), Paragraph(f"{trip_data.get('destination', 'DESTINATION').upper()}", value_style), Paragraph(gate, value_style), Paragraph(seat_str, value_style)],
        ]
        
        t_left = Table(left_data, colWidths=[2.2*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        t_left.setStyle(TableStyle([
            ('SPAN', (0,0), (2,0)), # Airline Name span
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('TOPPADDING', (0,1), (-1,1), 5),
            ('BOTTOMPADDING', (0,2), (-1,2), 10),
            ('TOPPADDING', (0,3), (-1,3), 5),
        ]))
        
        # Right Section (Stub)
        right_data = [
            [Paragraph("BOARDING PASS", label_style)],
            [Paragraph(trip_data.get('travelers', 'Guest').split(',')[0], value_style)],
            [Paragraph(f"{flight_no} / {date}", value_style)],
            [Paragraph(f"SEAT: <font size=12 color='#FF6B6B'>{seat_str}</font>", value_style)],
            [barcode]
        ]
        
        t_right = Table(right_data, colWidths=[1.8*inch])
        t_right.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        
        # Container Table
        container = Table([[t_left, t_right]], colWidths=[5.4*inch, 2.0*inch])
        container.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('BOX', (0,0), (-1,-1), 1, COLORS['ticket_border']),
            ('LINEAFTER', (0,0), (0,-1), 1, COLORS['ticket_border'], 0, (3,3)),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Wrap in a background box for "pop"
        wrapper = Table([[container]], colWidths=[7.5*inch])
        wrapper.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), COLORS['ticket_bg']),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        
        return wrapper

    def create_itinerary_section(self, trip_data, start_day, end_day):
        rows = []
        header_style = ParagraphStyle('DayHead', fontSize=12, fontName='Helvetica-Bold', textColor=COLORS['primary_gradient_2'])
        text_style = ParagraphStyle('DayText', fontSize=9, leading=11)
        
        itinerary = trip_data.get('itinerary', [])
        
        for i in range(start_day-1, min(end_day, len(itinerary))):
            day = itinerary[i]
            day_num = i + 1
            
            # Calculate Date
            try:
                start_date_str = trip_data.get('start_date', '')
                # Try parsing different formats if needed, but assuming standard format from _prepare_trip_data
                # _prepare_trip_data returns "%d %b %Y" e.g. "12 Mar 2025"
                start_dt = datetime.strptime(start_date_str, "%d %b %Y")
                from datetime import timedelta
                current_dt = start_dt + timedelta(days=i)
                date_str = current_dt.strftime("%d %b")
            except:
                date_str = f"Day {day_num}"

            # Image
            # Use first activity for better image match if available
            img_query = f"{trip_data.get('destination')} {day['title']} landmark"
            activities = day.get('activities', [])
            if activities:
                first_act = activities[0]
                if isinstance(first_act, dict):
                    act_name = first_act.get('name', '')
                    if act_name:
                        img_query = f"{trip_data.get('destination')} {act_name} landmark"
                elif isinstance(first_act, str):
                    img_query = f"{trip_data.get('destination')} {first_act} landmark"

            img_pil = self.get_image(trip_data.get('destination'), img_query, 300, 200)
            img = Image(self.image_to_bytes(img_pil), width=1.5*inch, height=1.0*inch)
            
            # Content
            activities_list = day.get('activities', [])
            if isinstance(activities_list, str):
                activities_list = [activities_list]
            
            # Format activities for display with times if available
            act_display = []
            for act in activities_list:
                if isinstance(act, dict):
                    time = act.get('time', '')
                    name = act.get('name', 'Activity')
                    if time:
                        act_display.append(f"<b>{time}</b>: {name}")
                    else:
                        act_display.append(name)
                else:
                    act_display.append(str(act))
            
            # Join with bullets
            highlights_html = "<br/>".join([f"• {a}" for a in act_display[:5]])
            
            content = [
                Paragraph(f"DAY {day_num} — {date_str} — {day['title']}", header_style),
                Paragraph(day['description'][:250] + "...", text_style),
                Paragraph(f"<b>Highlights & Schedule:</b><br/>{highlights_html}", ParagraphStyle('Icons', fontSize=9, textColor=COLORS['dark_text'], leading=12)),
            ]
            
            rows.append([img, Table([[c] for c in content], style=TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0)]))])
            rows.append([Spacer(1, 5), Spacer(1, 5)]) # Divider space
            
        if not rows:
            return Spacer(1, 0)

        t = Table(rows, colWidths=[1.6*inch, 5.8*inch])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBELOW', (0,0), (-1,-2), 0.5, COLORS['aqua_gradient']),
            ('PADDING', (0,0), (-1,-1), 4)
        ]))
        return t

    def create_hotel_weather_section(self, trip_data):
        # Hotel
        h_style = ParagraphStyle('H', fontSize=9)
        h_head = ParagraphStyle('HH', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['accent_pink'])
        
        start_date = trip_data.get('start_date', 'TBD')
        end_date = trip_data.get('end_date', 'TBD')
        
        hotel_content = [
            [Paragraph("<b>HOTEL DETAILS</b>", h_head)],
            [Paragraph(f"<b>{trip_data.get('hotel_name')}</b>", ParagraphStyle('HB', fontSize=10, fontName='Helvetica-Bold'))],
            [Paragraph(f"📍 {trip_data.get('destination', 'City Center')}", h_style)],
            [Paragraph(f"{trip_data.get('hotel_rating', 'Luxury Stay')}", h_style)],
            [Paragraph(f"Check-in: {start_date} (2:00 PM)", h_style)],
            [Paragraph(f"Check-out: {end_date} (11:00 AM)", h_style)],
            [Paragraph("Amenities: King Bed • Breakfast • Beach Access • Spa • Free WiFi", ParagraphStyle('Am', fontSize=9))],
            [Paragraph('<a href="https://maps.google.com/?q=' + trip_data.get('hotel_name', '').replace(' ', '+') + '" color="blue"><u>View Location on Map</u></a>', ParagraphStyle('L', fontSize=9, textColor='blue'))]
        ]
        
        # Weather Logic
        destination = trip_data.get('destination', '').lower()
        weather_type = "sunny"
        if any(x in destination for x in ['manali', 'shimla', 'leh', 'ladakh', 'swiss', 'switzerland', 'paris', 'london', 'europe']):
            weather_type = "cold"
        elif any(x in destination for x in ['kerala', 'goa', 'bali', 'maldives', 'thai', 'vietnam', 'beach']):
            weather_type = "tropical"
            
        weather_data = []
        if weather_type == "cold":
            weather_data = [
                ("Day 1", "12°C", "Cool Breeze", "blue"),
                ("Day 2", "10°C", "Cloudy", "grey"),
                ("Day 3", "08°C", "Chilly", "blue"),
            ]
        elif weather_type == "tropical":
            weather_data = [
                ("Day 1", "30°C", "Sunny", "orange"),
                ("Day 2", "29°C", "Clear Sky", "orange"),
                ("Day 3", "28°C", "Pleasant", "orange"),
            ]
        else:
            weather_data = [
                ("Day 1", "25°C", "Sunny", "orange"),
                ("Day 2", "24°C", "Pleasant", "green"),
                ("Day 3", "26°C", "Bright", "orange"),
            ]

        w_rows = []
        for day, temp, cond, color in weather_data:
            cond_html = f"<font color='{color}'><b>{cond}</b></font>"
            w_rows.append([
                Paragraph(day, h_style), 
                Paragraph(f"{temp} • {cond_html}", h_style)
            ])

        w_content = [
            [Paragraph("<b>WEATHER FORECAST</b>", ParagraphStyle('WH', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['accent_orange']))],
            [Table(w_rows, style=TableStyle([('GRID', (0,0), (-1,-1), 0.5, 'lightgrey'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 4)]))]
        ]
        
        t1 = Table(hotel_content, colWidths=[3.6*inch])
        t1.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, COLORS['accent_pink']), ('PADDING', (0,0), (-1,-1), 6)]))
        
        t2 = Table(w_content, colWidths=[3.6*inch])
        t2.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, COLORS['accent_orange']), ('PADDING', (0,0), (-1,-1), 6)]))
        
        return Table([[t1, t2]], colWidths=[3.75*inch, 3.75*inch])

    def create_packing_currency_section(self, trip_data):
        # Packing
        p_style = ParagraphStyle('P', fontSize=9, leading=11)
        p_head = ParagraphStyle('PH', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['accent_purple'])
        
        destination = trip_data.get('destination', '').lower()
        
        # Determine packing needs
        is_cold = any(x in destination for x in ['manali', 'shimla', 'leh', 'ladakh', 'swiss', 'switzerland', 'paris', 'london', 'europe', 'snow'])
        is_beach = any(x in destination for x in ['kerala', 'goa', 'bali', 'maldives', 'thai', 'vietnam', 'beach', 'island'])
        
        clothes = "Comfortable walking shoes, Light layers"
        if is_cold:
            clothes = "Heavy Jacket, Thermals, Woolen Cap"
        elif is_beach:
            clothes = "Swimwear, Sunglasses, Sun Hat"

        pack_content = [
            [Paragraph("<b>PACKING CHECKLIST</b>", p_head)],
            [Paragraph("<font color='#FF6B6B'><b>📄 ESSENTIALS</b></font>", p_style)],
            [Paragraph("• Passport/ID • Tickets • Vouchers", p_style)],
            [Spacer(1, 3)],
            [Paragraph("<font color='#FF6B6B'><b>👕 CLOTHING</b></font>", p_style)],
            [Paragraph(f"• {clothes}", p_style)],
            [Spacer(1, 3)],
            [Paragraph("<font color='#FF6B6B'><b>🔌 GADGETS & MISC</b></font>", p_style)],
            [Paragraph("• Charger • Powerbank • Meds", p_style)],
        ]
        
        # Currency Logic
        destination = trip_data.get('destination', '').lower()
        # Heuristic for India vs International
        is_india = any(x in destination for x in ['india', 'goa', 'kerala', 'delhi', 'mumbai', 'bangalore', 'manali', 'shimla', 'jaipur', 'udaipur', 'rishikesh', 'ladakh'])
        
        c_head = ParagraphStyle('CH', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['accent_gold'])
        
        if is_india:
             c_content = [
                [Paragraph("<b>CURRENCY & TIPS</b>", c_head)],
                [Paragraph("<b>Currency: Indian Rupee (INR)</b>", p_style)],
                [Paragraph("Meal: ₹300-500 | Taxi: ₹20/km", p_style)],
                [Paragraph("• UPI is widely accepted", p_style)],
                [Paragraph("• Keep small cash for local shops", p_style)]
            ]
        else:
             c_content = [
                [Paragraph("<b>CURRENCY & TIPS</b>", c_head)],
                [Paragraph("<b>Currency: USD / Local</b>", p_style)],
                [Paragraph("Meal: $15-25 | Taxi: $10-20", p_style)],
                [Paragraph("• Carry International Credit Card", p_style)],
                [Paragraph("• Keep some local cash handy", p_style)]
            ]
        
        t1 = Table(pack_content, colWidths=[3.6*inch])
        t1.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, COLORS['accent_purple']), ('PADDING', (0,0), (-1,-1), 6)]))
        
        t2 = Table(c_content, colWidths=[3.6*inch])
        t2.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, COLORS['accent_gold']), ('PADDING', (0,0), (-1,-1), 6)]))
        
        return Table([[t1, t2]], colWidths=[3.75*inch, 3.75*inch])

    def create_footer_info_section(self, trip_data):
        f_style = ParagraphStyle('F', fontSize=8)
        f_head = ParagraphStyle('FH', fontSize=10, fontName='Helvetica-Bold')
        
        # Emergency
        e_col = [
            Paragraph("<b>EMERGENCY</b>", ParagraphStyle('EH', fontSize=10, fontName='Helvetica-Bold', textColor='red')),
            Paragraph("Hotel: +960 123 4567", f_style),
            Paragraph("Police: 119", f_style),
            Paragraph("Support: +91 98765", f_style)
        ]
        
        # Payment
        pay_col = [
            Paragraph("<b>PAYMENT</b>", ParagraphStyle('PH', fontSize=10, fontName='Helvetica-Bold', textColor='green')),
            Paragraph(f"Total: {trip_data.get('total_cost')}", f_style),
            Paragraph("Status: PAID", f_style),
            Paragraph("Via: Razorpay", f_style)
        ]
        
        # Attachments
        att_col = [
            Paragraph("<b>ATTACHMENTS</b>", ParagraphStyle('AH', fontSize=10, fontName='Helvetica-Bold', textColor='blue')),
            Paragraph("• Flight Ticket", f_style),
            Paragraph("• Hotel Voucher", f_style),
            Paragraph("• Insurance", f_style)
        ]
        
        return Table([[e_col, pay_col, att_col]], colWidths=[2.5*inch, 2.5*inch, 2.5*inch], 
                     style=TableStyle([('GRID', (0,0), (-1,-1), 0.5, 'lightgrey'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 6)]))

    def create_thank_you_section(self):
        return Paragraph("Have a wonderful journey! • Powered by TravelOrbit AI", 
                         ParagraphStyle('Thanks', fontSize=12, fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=COLORS['primary_gradient_1']))


class PDFService:
    """
    Service to generate magazine-style PDF itineraries using ReportLab.
    """

    @staticmethod
    def generate_itinerary_pdf(trip: Trip, payment: Payment, booking_number: str) -> bytes:
        """
        Generates a PDF itinerary for the given trip.
        Returns the PDF content as bytes.
        """
        try:
            # Prepare data
            trip_data = PDFService._prepare_trip_data(trip, payment, booking_number)
            
            # Generate PDF
            generator = TravelPDFGenerator()
            pdf_bytes = generator.generate_bytes(trip_data)
            
            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            return None

    @staticmethod
    def _prepare_trip_data(trip: Trip, payment: Payment, booking_number: str) -> dict:
        """
        Converts Trip and Payment models to the dictionary format expected by TravelPDFGenerator.
        """
        # Parse AI Summary JSON
        itinerary = []
        hotel_name = "Recommended Hotel"
        hotel_rating = "Luxury Stay"
        hotel_desc = ""
        
        if trip.ai_summary_json:
            try:
                if isinstance(trip.ai_summary_json, str):
                    ai_data = json.loads(trip.ai_summary_json)
                else:
                    ai_data = trip.ai_summary_json
                
                # Extract itinerary days
                days = ai_data.get("days", []) if isinstance(ai_data, dict) else (ai_data if isinstance(ai_data, list) else [])
                
                for day in days:
                    # Generate a dynamic description if missing
                    desc = day.get('description', '')
                    activities = day.get('activities', [])
                    
                    if not desc or desc == "Enjoy your day!":
                        # Create description from activities
                        act_names = []
                        for act in activities:
                            if isinstance(act, dict):
                                act_names.append(act.get('name', ''))
                            elif isinstance(act, str):
                                act_names.append(act)
                        
                        if act_names:
                            desc = f"Today's highlights include {', '.join(act_names[:3])}."
                            if len(act_names) > 3:
                                desc += " and more."
                        else:
                            desc = "Enjoy your day exploring the city!"

                    itinerary.append({
                        'title': day.get('title', f"Day {day.get('day', '')}"),
                        'description': desc,
                        'activities': activities
                    })
                
                # Extract hotel if available in summary (assuming structure)
                if isinstance(ai_data, dict) and 'hotel' in ai_data:
                    hotel_info = ai_data['hotel']
                    if isinstance(hotel_info, dict):
                        hotel_name = hotel_info.get('name', 'Recommended Hotel')
                        hotel_rating = hotel_info.get('rating', 'Luxury Stay')
                        hotel_desc = hotel_info.get('description', '')
                    else:
                        hotel_name = str(hotel_info)
                    
            except Exception as e:
                logger.error(f"Error parsing AI summary: {e}")
        
        # Format dates
        start_date = trip.start_date.strftime("%d %b %Y") if trip.start_date else "TBD"
        end_date = trip.end_date.strftime("%d %b %Y") if trip.end_date else "TBD"
        
        # Format cost
        symbol = "₹" if payment.currency == "INR" else payment.currency
        total_cost = f"{symbol} {payment.amount:,.2f}"
        
        # Package Type
        pkg_type = trip.budget_level.title() if trip.budget_level else "Standard"
        if getattr(trip, "include_guide_photographer", 0) == 1:
            pkg_type += " + Guide & Photo"
        
        # Travelers
        travelers_count = len(trip.passengers) if trip.passengers else 1
        travelers_str = f"{travelers_count} Adults"
        if trip.passengers and len(trip.passengers) > 0:
             # Try to get first passenger name
             first_passenger = trip.passengers[0]
             # Assuming passenger model has name field, otherwise fallback
             if hasattr(first_passenger, 'name'):
                 # Just show count for cleaner look in ticket, or "Name + X"
                 # For ticket we need count mainly
                 pass
        
        return {
            'destination': trip.to_city or "Unknown Destination",
            'start_date': start_date,
            'end_date': end_date,
            'travelers': travelers_str,
            'duration': f"{trip.duration_days} Days",
            'package_type': pkg_type,
            'hotel_name': hotel_name,
            'hotel_rating': hotel_rating,
            'hotel_desc': hotel_desc,
            'total_cost': total_cost,
            'booking_number': booking_number,
            'itinerary': itinerary
        }
