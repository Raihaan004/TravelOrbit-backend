"""
TravelOrbit PDF Generator Configuration
Easily customize colors, fonts, and layout settings
"""

from reportlab.lib import colors

# ======================== COLOR THEMES ========================

# Theme 1: Tropical Paradise (Default)
THEME_TROPICAL = {
    'primary_gradient_1': colors.HexColor('#FF6B6B'),      # Coral Red
    'primary_gradient_2': colors.HexColor('#4ECDC4'),      # Teal
    'accent_gold': colors.HexColor('#FFD93D'),             # Gold
    'accent_green': colors.HexColor('#6BCB77'),            # Green
    'accent_purple': colors.HexColor('#A8E6CF'),           # Light Purple
    'accent_orange': colors.HexColor('#FF8C42'),           # Orange
    'accent_pink': colors.HexColor('#FF69B4'),             # Pink
    'accent_blue': colors.HexColor('#00D4FF'),             # Bright Blue
    'dark_text': colors.HexColor('#2C3E50'),               # Dark Blue
    'light_text': colors.white,                             # White
    'aqua_gradient': colors.HexColor('#00E5E5'),           # Aqua
}

# Theme 2: Sunset Adventure
THEME_SUNSET = {
    'primary_gradient_1': colors.HexColor('#FF4757'),      # Sunset Red
    'primary_gradient_2': colors.HexColor('#FFA502'),      # Orange
    'accent_gold': colors.HexColor('#FFE66D'),             # Bright Yellow
    'accent_green': colors.HexColor('#2ED573'),            # Bright Green
    'accent_purple': colors.HexColor('#DDA0DD'),           # Plum
    'accent_orange': colors.HexColor('#FF6348'),           # Dark Orange
    'accent_pink': colors.HexColor('#FF6B9D'),             # Hot Pink
    'accent_blue': colors.HexColor('#0984E3'),             # Deep Blue
    'dark_text': colors.HexColor('#1A1A1A'),               # Almost Black
    'light_text': colors.white,
    'aqua_gradient': colors.HexColor('#FF7F50'),           # Coral
}

# Theme 3: Mountain Escape
THEME_MOUNTAIN = {
    'primary_gradient_1': colors.HexColor('#2C5AA0'),      # Mountain Blue
    'primary_gradient_2': colors.HexColor('#5C946E'),      # Forest Green
    'accent_gold': colors.HexColor('#F0AD4E'),             # Muted Gold
    'accent_green': colors.HexColor('#52C41A'),            # Natural Green
    'accent_purple': colors.HexColor('#9254DE'),           # Mountain Purple
    'accent_orange': colors.HexColor('#D4380D'),           # Deep Orange
    'accent_pink': colors.HexColor('#EB2F96'),             # Mountain Pink
    'accent_blue': colors.HexColor('#1890FF'),             # Sky Blue
    'dark_text': colors.HexColor('#262626'),               # Charcoal
    'light_text': colors.white,
    'aqua_gradient': colors.HexColor('#13C2C2'),           # Teal
}

# Theme 4: Urban Elegance
THEME_URBAN = {
    'primary_gradient_1': colors.HexColor('#1A1A1A'),      # Black
    'primary_gradient_2': colors.HexColor('#666666'),      # Dark Gray
    'accent_gold': colors.HexColor('#D4AF37'),             # Gold
    'accent_green': colors.HexColor('#00AA66'),            # Green
    'accent_purple': colors.HexColor('#663399'),           # Purple
    'accent_orange': colors.HexColor('#FF8C00'),           # Orange
    'accent_pink': colors.HexColor('#FF1493'),             # Deep Pink
    'accent_blue': colors.HexColor('#0066CC'),             # Blue
    'dark_text': colors.HexColor('#333333'),               # Dark
    'light_text': colors.white,
    'aqua_gradient': colors.HexColor('#00CED1'),           # Dark Turquoise
}

# Theme 5: Pastel Dreams
THEME_PASTEL = {
    'primary_gradient_1': colors.HexColor('#FFB6C1'),      # Light Pink
    'primary_gradient_2': colors.HexColor('#B0E0E6'),      # Powder Blue
    'accent_gold': colors.HexColor('#FFDAB9'),             # Peach
    'accent_green': colors.HexColor('#90EE90'),            # Light Green
    'accent_purple': colors.HexColor('#DDA0DD'),           # Plum
    'accent_orange': colors.HexColor('#FFD699'),           # Light Orange
    'accent_pink': colors.HexColor('#FFC0CB'),             # Pink
    'accent_blue': colors.HexColor('#ADD8E6'),             # Light Blue
    'dark_text': colors.HexColor('#696969'),               # Dim Gray
    'light_text': colors.white,
    'aqua_gradient': colors.HexColor('#AFEEEE'),           # Pale Turquoise
}

# Theme 6: Desert Sunset
THEME_DESERT = {
    'primary_gradient_1': colors.HexColor('#CD5C5C'),      # Indian Red
    'primary_gradient_2': colors.HexColor('#DEB887'),      # Burlywood
    'accent_gold': colors.HexColor('#FFD700'),             # Gold
    'accent_green': colors.HexColor('#98FB98'),            # Pale Green
    'accent_purple': colors.HexColor('#EE82EE'),           # Violet
    'accent_orange': colors.HexColor('#FF7F50'),           # Coral
    'accent_pink': colors.HexColor('#DB7093'),             # Pale Violet Red
    'accent_blue': colors.HexColor('#87CEEB'),             # Sky Blue
    'dark_text': colors.HexColor('#8B4513'),               # Saddle Brown
    'light_text': colors.white,
    'aqua_gradient': colors.HexColor('#F0E68C'),           # Khaki
}

# ======================== FONT SETTINGS ========================

FONTS = {
    'default': {
        'header': 'Helvetica-Bold',
        'body': 'Helvetica',
        'accent': 'Helvetica-BoldOblique',
    },
    'elegant': {
        'header': 'Times-Bold',
        'body': 'Times-Roman',
        'accent': 'Times-BoldItalic',
    },
    'modern': {
        'header': 'Courier-Bold',
        'body': 'Courier',
        'accent': 'Courier-BoldOblique',
    },
}

# ======================== LAYOUT SETTINGS ========================

LAYOUT = {
    'default': {
        'page_size': 'A4',
        'top_margin': 0.3,        # inches
        'bottom_margin': 0.3,     # inches
        'left_margin': 0.4,       # inches
        'right_margin': 0.4,      # inches
        'line_spacing': 1.5,
    },
    'compact': {
        'page_size': 'A4',
        'top_margin': 0.2,
        'bottom_margin': 0.2,
        'left_margin': 0.3,
        'right_margin': 0.3,
        'line_spacing': 1.3,
    },
    'spacious': {
        'page_size': 'A4',
        'top_margin': 0.5,
        'bottom_margin': 0.5,
        'left_margin': 0.6,
        'right_margin': 0.6,
        'line_spacing': 1.8,
    },
}

# ======================== FONT SIZES ========================

FONT_SIZES = {
    'default': {
        'page_title': 36,         # Main page header
        'section_title': 32,      # Section headers
        'subsection': 18,         # Subsection headers
        'body': 11,               # Body text
        'small': 10,              # Small text
        'tiny': 9,                # Tiny text
        'label': 12,              # Labels
    },
    'large': {
        'page_title': 42,
        'section_title': 38,
        'subsection': 22,
        'body': 13,
        'small': 12,
        'tiny': 11,
        'label': 14,
    },
    'small': {
        'page_title': 28,
        'section_title': 24,
        'subsection': 14,
        'body': 9,
        'small': 8,
        'tiny': 7,
        'label': 10,
    },
}

# ======================== IMAGE SETTINGS ========================

IMAGE_CONFIG = {
    'hero_image': {
        'width': 6.8,             # inches
        'height': 5.0,            # inches
        'quality': 'high',        # high, medium, low
    },
    'day_image': {
        'width': 5.5,
        'height': 3.5,
        'quality': 'high',
    },
    'hotel_image': {
        'width': 5.5,
        'height': 3.5,
        'quality': 'high',
    },
    'thumbnail': {
        'width': 2.0,
        'height': 1.5,
        'quality': 'medium',
    },
    'brightness_boost': 1.15,    # 0.5 - 2.0 (1.0 = no change)
    'contrast_boost': 1.25,      # 0.5 - 2.0
    'color_saturation': 1.35,    # 0.5 - 2.0
}

# ======================== TABLE SETTINGS ========================

TABLE_STYLES = {
    'summary': {
        'header_bg': '#4ECDC4',   # Teal
        'row_bg1': '#A8E6CF',     # Light Purple
        'row_bg2': '#FF69B4',     # Pink
        'text_color': '#2C3E50',  # Dark
        'padding': 12,
    },
    'weather': {
        'header_bg': '#00D4FF',   # Blue
        'row_bg1': '#FF69B4',     # Pink
        'row_bg2': '#FFD93D',     # Gold
        'text_color': '#2C3E50',
        'padding': 10,
    },
    'flight': {
        'header_bg': '#FFD93D',   # Gold
        'row_bg1': '#00D4FF',     # Blue
        'row_bg2': 'white',
        'text_color': '#2C3E50',
        'padding': 10,
    },
    'emergency': {
        'header_bg': 'red',
        'row_bg1': 'lightgrey',
        'row_bg2': 'white',
        'text_color': 'black',
        'padding': 10,
    },
}

# ======================== EMOJI SETTINGS ========================

EMOJIS = {
    'activities': {
        'flight': '✈',
        'car': '🚗',
        'hotel': '🏨',
        'food': '🍽',
        'sunset': '🌅',
        'beach': '🏖',
        'theater': '🎭',
        'photo': '📸',
        'map': '📍',
        'phone': '📞',
        'email': '📧',
        'calendar': '📅',
        'user': '👥',
        'money': '💰',
        'star': '⭐',
        'check': '✓',
        'paid': '✔',
        'warning': '🚨',
    },
}

# ======================== CONFIGURATION LOADER ========================

class PDFConfig:
    """Configuration loader for PDF generator"""
    
    def __init__(self, theme='tropical', font_set='default', layout='default', font_sizes='default'):
        """
        Initialize configuration
        
        Args:
            theme: 'tropical', 'sunset', 'mountain', 'urban', 'pastel', 'desert'
            font_set: 'default', 'elegant', 'modern'
            layout: 'default', 'compact', 'spacious'
            font_sizes: 'default', 'large', 'small'
        """
        self.theme_name = theme
        self.font_set = font_set
        self.layout = layout
        self.font_sizes_name = font_sizes
        
        # Load selected theme
        theme_map = {
            'tropical': THEME_TROPICAL,
            'sunset': THEME_SUNSET,
            'mountain': THEME_MOUNTAIN,
            'urban': THEME_URBAN,
            'pastel': THEME_PASTEL,
            'desert': THEME_DESERT,
        }
        self.colors = theme_map.get(theme, THEME_TROPICAL)
        self.fonts = FONTS.get(font_set, FONTS['default'])
        self.layout_settings = LAYOUT.get(layout, LAYOUT['default'])
        self.font_sizes = FONT_SIZES.get(font_sizes, FONT_SIZES['default'])
    
    def get_color(self, color_name):
        """Get color by name"""
        return self.colors.get(color_name, colors.black)
    
    def get_font(self, font_type):
        """Get font name"""
        return self.fonts.get(font_type, 'Helvetica')
    
    def get_font_size(self, size_name):
        """Get font size by name"""
        return self.font_sizes.get(size_name, 11)
    
    def list_themes(self):
        """List available themes"""
        return list(THEME_TROPICAL.keys())
    
    def list_font_sets(self):
        """List available font sets"""
        return list(FONTS.keys())
    
    def list_layouts(self):
        """List available layouts"""
        return list(LAYOUT.keys())


# ======================== EXAMPLE USAGE ========================

if __name__ == "__main__":
    # Load different configurations
    print("Available Configurations:\n")
    
    # Tropical Theme
    config_tropical = PDFConfig(theme='tropical', layout='spacious', font_sizes='large')
    print(f"Tropical Theme: {config_tropical.colors['primary_gradient_1']}")
    
    # Mountain Theme
    config_mountain = PDFConfig(theme='mountain', layout='default', font_sizes='default')
    print(f"Mountain Theme: {config_mountain.colors['primary_gradient_1']}")
    
    # Urban Theme
    config_urban = PDFConfig(theme='urban', layout='compact', font_sizes='small')
    print(f"Urban Theme: {config_urban.colors['primary_gradient_1']}")
    
    # Desert Theme
    config_desert = PDFConfig(theme='desert', font_set='elegant')
    print(f"Desert Theme: {config_desert.colors['primary_gradient_1']}")
    
    print("\n✓ Configuration system ready for use!")
