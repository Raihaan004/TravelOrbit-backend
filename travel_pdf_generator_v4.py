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

from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor

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
                font = ImageFont.truetype("arial.ttf", 60)
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
    
    def create_pdf(self, trip_data, output_path="travel_itinerary.pdf"):
        """Generate complete magazine-style PDF in 2 pages with optimized layout and fake ticket"""
        doc = SimpleDocTemplate(
            output_path,
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
        
        # 4. Day by Day (Bottom 40% - Days 1-3)
        story.append(self.create_itinerary_section(trip_data, start_day=1, end_day=3))
        
        story.append(PageBreak())
        
        # --- PAGE 2 ---
        # 5. Day by Day (Top 20% - Days 4-5)
        story.append(self.create_itinerary_section(trip_data, start_day=4, end_day=5))
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
        print(f"✓ PDF created successfully: {output_path}")

    def create_cover_section(self, trip_data):
        destination = trip_data.get('destination', 'Dream Destination')
        start_date = trip_data.get('start_date', '2025-03-12')
        end_date = trip_data.get('end_date', '2025-03-16')
        travelers = trip_data.get('travelers', '2 Adults, 1 Child')
        
        # Image
        img_pil = self.get_image(destination, "destination cover travel", 1200, 500)
        img_bytes = self.image_to_bytes(img_pil)
        img = Image(img_bytes, width=7.5*inch, height=2.8*inch)
        
        # Text Overlay (Simulated with Table)
        title_style = ParagraphStyle('CoverTitle', fontSize=32, textColor=COLORS['primary_gradient_1'], fontName='Helvetica-Bold', alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle', fontSize=14, textColor=COLORS['accent_gold'], fontName='Helvetica', alignment=TA_CENTER)
        info_style = ParagraphStyle('Info', fontSize=10, textColor=COLORS['dark_text'], alignment=TA_CENTER)
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        duration = (end - start).days
        
        text_content = [
            Paragraph(f"{duration} Days • {destination} Luxury Escape", title_style),
            Paragraph("Your Personalized TravelOrbit Itinerary", subtitle_style),
            Paragraph(f"📅 {start_date} – {end_date} • 👥 {travelers}", info_style),
        ]
        
        # Paid Stamp
        paid_style = ParagraphStyle('Paid', fontSize=14, textColor=COLORS['accent_green'], fontName='Helvetica-Bold', alignment=TA_RIGHT)
        text_content.append(Paragraph("✓ PAID", paid_style))
        
        return Table([[img], [Table([[c] for c in text_content], style=TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))]], 
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
                Paragraph(f"<b>Hotel:</b><br/>{trip_data.get('hotel_name', 'Sun Island Resort')}", summary_style),
                Paragraph(f"<b>Total Cost:</b><br/>{trip_data.get('total_cost', '₹1,32,500')}", summary_style),
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
        large_code_style = ParagraphStyle('BPCode', fontSize=24, textColor=COLORS['primary_gradient_1'], fontName='Helvetica-Bold')
        
        # Data
        airline = "Air India Express"
        flight_no = "AI-123"
        pnr = "ABC123XYZ"
        date = "12 MAR 2025"
        time = "06:00 AM"
        gate = "A4"
        seat = "12A"
        
        # Barcode
        barcode = code128.Code128(pnr, barHeight=0.4*inch, barWidth=1.2)
        
        # Left Section (Main Ticket)
        left_data = [
            [Paragraph(f"✈ {airline}", ParagraphStyle('Air', fontSize=12, fontName='Helvetica-Bold', textColor=COLORS['primary_gradient_2'])), '', '', Paragraph("BOARDING PASS", ParagraphStyle('BPTitle', fontSize=10, alignment=TA_RIGHT, textColor='grey'))],
            [Paragraph("PASSENGER NAME", label_style), Paragraph("FLIGHT", label_style), Paragraph("DATE", label_style), Paragraph("TIME", label_style)],
            [Paragraph(trip_data.get('travelers', 'Guest').split(',')[0], value_style), Paragraph(flight_no, value_style), Paragraph(date, value_style), Paragraph(time, value_style)],
            [Paragraph("FROM", label_style), Paragraph("TO", label_style), Paragraph("GATE", label_style), Paragraph("SEAT", label_style)],
            [Paragraph("DELHI (DEL)", value_style), Paragraph(f"{trip_data.get('destination', 'MALDIVES').upper()} (MLE)", value_style), Paragraph(gate, value_style), Paragraph(seat, value_style)],
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
            [Paragraph(f"SEAT: <font size=14 color='#FF6B6B'>{seat}</font>", value_style)],
            [barcode]
        ]
        
        t_right = Table(right_data, colWidths=[1.8*inch])
        t_right.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
        ]))
        
        # Container Table
        container = Table([[t_left, t_right]], colWidths=[5.4*inch, 2.0*inch])
        container.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('BOX', (0,0), (-1,-1), 1, COLORS['ticket_border']),
            # ('ROUNDEDCORNERS', [10, 10, 10, 10]), # Commented out as it might cause issues in some versions
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
            
            # Image
            img_pil = self.get_image(trip_data.get('destination'), f"{day['title']} activity", 300, 200)
            img = Image(self.image_to_bytes(img_pil), width=1.5*inch, height=1.0*inch)
            
            # Content
            content = [
                Paragraph(f"DAY {day_num} — {day['title']}", header_style),
                Paragraph(day['description'][:150] + "...", text_style),
                Paragraph(f"<b>Timeline:</b> {' → '.join(['✈', '🛥', '🏨', '🍽', '🌅'][:len(day.get('activities', []))])}", ParagraphStyle('Icons', fontSize=12, textColor=COLORS['accent_orange'])),
                Paragraph("<u>View on Map</u>", ParagraphStyle('Link', fontSize=8, textColor='blue'))
            ]
            
            rows.append([img, Table([[c] for c in content], style=TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0)]))])
            rows.append([Spacer(1, 5), Spacer(1, 5)]) # Divider space
            
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
        
        hotel_content = [
            [Paragraph("<b>HOTEL DETAILS</b>", h_head)],
            [Paragraph(f"<b>{trip_data.get('hotel_name')}</b>", ParagraphStyle('HB', fontSize=10, fontName='Helvetica-Bold'))],
            [Paragraph("⭐⭐⭐⭐⭐", h_style)],
            [Paragraph("Check-in: 12 Mar • Check-out: 16 Mar", h_style)],
            [Paragraph("Amenities: 🛏 🍳 🏖 🧖 📶", ParagraphStyle('Am', fontSize=12))],
            [Paragraph("<u>View Location</u>", ParagraphStyle('L', fontSize=8, textColor='blue'))]
        ]
        
        # Weather
        w_content = [
            [Paragraph("<b>WEATHER FORECAST</b>", ParagraphStyle('WH', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['accent_orange']))],
            [Table([
                [Paragraph("Day 1", h_style), Paragraph("☀️ 32°C", h_style)],
                [Paragraph("Day 2", h_style), Paragraph("🌤 31°C", h_style)],
                [Paragraph("Day 3", h_style), Paragraph("⛅ 30°C", h_style)],
            ], style=TableStyle([('GRID', (0,0), (-1,-1), 0.5, 'lightgrey')]))]
        ]
        
        t1 = Table(hotel_content, colWidths=[3.6*inch])
        t1.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, COLORS['accent_pink']), ('PADDING', (0,0), (-1,-1), 6)]))
        
        t2 = Table(w_content, colWidths=[3.6*inch])
        t2.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, COLORS['accent_orange']), ('PADDING', (0,0), (-1,-1), 6)]))
        
        return Table([[t1, t2]], colWidths=[3.75*inch, 3.75*inch])

    def create_packing_currency_section(self, trip_data):
        # Packing
        p_style = ParagraphStyle('P', fontSize=9)
        p_head = ParagraphStyle('PH', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['accent_purple'])
        
        pack_content = [
            [Paragraph("<b>PACKING CHECKLIST</b>", p_head)],
            [Paragraph("• Passport, Tickets, Insurance", p_style)],
            [Paragraph("• Sunscreen, Swimwear, Hat", p_style)],
            [Paragraph("• Chargers, Powerbank, Adapter", p_style)],
            [Paragraph("• Light cotton clothes", p_style)]
        ]
        
        # Currency
        c_content = [
            [Paragraph("<b>CURRENCY & TIPS</b>", ParagraphStyle('CH', fontSize=11, fontName='Helvetica-Bold', textColor=COLORS['accent_gold']))],
            [Paragraph("<b>1 USD = 15.4 MVR</b>", p_style)],
            [Paragraph("Meal: ~150 MVR | Taxi: ~50 MVR", p_style)],
            [Paragraph("• Dress modestly in local areas", p_style)],
            [Paragraph("• Tipping 5-10% appreciated", p_style)]
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
            Paragraph("Total: ₹1,32,500", f_style),
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
