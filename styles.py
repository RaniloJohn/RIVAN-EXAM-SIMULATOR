class Styles:
    # Color Palettes
    DARK_PALETTE = {
        "bg_primary": "#0f172a",       # Slate 900
        "bg_secondary": "#1e293b",     # Slate 800
        "bg_tertiary": "#334155",      # Slate 700
        "text_primary": "#f8fafc",     # Slate 50
        "text_secondary": "#94a3b8",   # Slate 400
        "border": "#334155",           # Slate 700
        "accent": "#0ea5e9",           # Sky 500
        "accent_hover": "#38bdf8",     # Sky 400
        "correct": "#10b981",          # Emerald 500
        "incorrect": "#ef4444",        # Red 500
        "flagged": "#f59e0b",          # Amber 500
        "highlight": "#1e293b"
    }

    LIGHT_PALETTE = {
        "bg_primary": "#f8fafc",       # Slate 50
        "bg_secondary": "#ffffff",     # White
        "bg_tertiary": "#f1f5f9",      # Slate 100
        "text_primary": "#0f172a",     # Slate 900
        "text_secondary": "#475569",   # Slate 600
        "border": "#cbd5e1",           # Slate 300
        "accent": "#0284c7",           # Sky 600
        "accent_hover": "#0ea5e9",     # Sky 500
        "correct": "#059669",          # Emerald 600
        "incorrect": "#dc2626",        # Red 600
        "flagged": "#d97706",          # Amber 600
        "highlight": "#f1f5f9"
    }

    @classmethod
    def get_qss(cls, dark_mode=True):
        p = cls.DARK_PALETTE if dark_mode else cls.LIGHT_PALETTE
        
        return f"""
        /* Global Base */
        QWidget {{
            background-color: {p["bg_primary"]};
            color: {p["text_primary"]};
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            font-size: 13px;
        }}
        
        /* Main Window & Sidebar */
        QMainWindow {{
            background-color: {p["bg_primary"]};
        }}
        
        QFrame#sidebar {{
            background-color: {p["bg_secondary"]};
            border-right: 1px solid {p["border"]};
        }}
        
        /* Header / Navbar */
        QFrame#header {{
            background-color: {p["bg_secondary"]};
            border-bottom: 1px solid {p["border"]};
        }}

        /* Scroll Area Content */
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        
        /* Cards and Sections */
        QFrame#card {{
            background-color: {p["bg_secondary"]};
            border: 1px solid {p["border"]};
            border-radius: 12px;
        }}
        
        QFrame#card_highlight {{
            background-color: {p["bg_secondary"]};
            border: 2px solid {p["accent"]};
            border-radius: 12px;
        }}

        /* Buttons */
        QPushButton {{
            background-color: {p["bg_tertiary"]};
            color: {p["text_primary"]};
            border: 1px solid {p["border"]};
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {p["border"]};
            border-color: {p["accent"]};
        }}
        QPushButton:pressed {{
            background-color: {p["bg_primary"]};
        }}
        
        /* Accent Button (Primary) */
        QPushButton#primary_btn {{
            background-color: {p["accent"]};
            color: #ffffff;
            border: none;
        }}
        QPushButton#primary_btn:hover {{
            background-color: {p["accent_hover"]};
        }}
        QPushButton#primary_btn:pressed {{
            background-color: {p["accent"]};
        }}
        
        /* Flag / Correct / Incorrect Buttons */
        QPushButton#flag_btn {{
            background-color: transparent;
            border: 1px solid {p["flagged"]};
            color: {p["flagged"]};
        }}
        QPushButton#flag_btn:hover {{
            background-color: {p["flagged"]}22;
        }}
        QPushButton#flag_btn[active="true"] {{
            background-color: {p["flagged"]};
            color: #ffffff;
        }}

        QPushButton#bookmark_btn {{
            background-color: transparent;
            border: 1px solid {p["accent"]};
            color: {p["accent"]};
        }}
        QPushButton#bookmark_btn:hover {{
            background-color: {p["accent"]}22;
        }}
        QPushButton#bookmark_btn[active="true"] {{
            background-color: {p["accent"]};
            color: #ffffff;
        }}
        
        /* Input & Controls */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
            background-color: {p["bg_secondary"]};
            color: {p["text_primary"]};
            border: 1px solid {p["border"]};
            border-radius: 6px;
            padding: 6px 12px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border-color: {p["accent"]};
        }}
        
        /* Lists & Directories */
        QListWidget {{
            background-color: {p["bg_secondary"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            padding: 4px;
        }}
        QListWidget::item {{
            border-radius: 4px;
            padding: 8px 12px;
            margin: 2px 0;
            color: {p["text_primary"]};
        }}
        QListWidget::item:hover {{
            background-color: {p["bg_tertiary"]};
        }}
        QListWidget::item:selected {{
            background-color: {p["accent"]}33;
            color: {p["accent"]};
            border-left: 3px solid {p["accent"]};
            font-weight: bold;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {p["bg_secondary"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }}
        QProgressBar::chunk {{
            background-color: {p["accent"]};
            border-radius: 6px;
        }}
        
        /* Sidebar Scroll Bar */
        QScrollBar:vertical {{
            border: none;
            background: {p["bg_primary"]};
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {p["border"]};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p["accent"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* Headers / Texts */
        QLabel#title {{
            font-size: 20px;
            font-weight: 700;
            color: {p["text_primary"]};
        }}
        QLabel#subtitle {{
            font-size: 14px;
            color: {p["text_secondary"]};
        }}
        QLabel#timer_lbl {{
            font-size: 18px;
            font-weight: 700;
            color: {p["text_primary"]};
        }}
        
        /* Question Checkboxes & Radio Buttons */
        QCheckBox, QRadioButton {{
            padding: 8px;
            spacing: 8px;
            font-size: 13px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {p["border"]};
            border-radius: 4px;
            background-color: {p["bg_secondary"]};
        }}
        QRadioButton::indicator {{
            border-radius: 9px;
        }}
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {p["accent"]};
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {p["accent"]};
            border-color: {p["accent"]};
            image: url(cache/check.png); /* Fallback to styled colors */
        }}
        
        /* Dialogs */
        QDialog {{
            background-color: {p["bg_primary"]};
            border: 1px solid {p["border"]};
        }}
        """

    @classmethod
    def get_html_css(cls, dark_mode=True):
        p = cls.DARK_PALETTE if dark_mode else cls.LIGHT_PALETTE
        
        return f"""
        body {{
            background-color: {p["bg_secondary"]};
            color: {p["text_primary"]};
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            margin: 15px;
        }}
        h1, h2, h3, h4 {{
            color: {p["text_primary"]};
            margin-top: 0;
        }}
        p {{
            margin-bottom: 12px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background-color: {p["bg_primary"]};
        }}
        th, td {{
            border: 1px solid {p["border"]};
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: {p["bg_tertiary"]};
            font-weight: bold;
        }}
        .img-container {{
            margin: 15px 0;
            text-align: center;
            border: 1px solid {p["border"]};
            padding: 10px;
            border-radius: 8px;
            background-color: {p["bg_primary"]};
        }}
        .explanation-box {{
            margin-top: 20px;
            padding: 15px;
            border-left: 4px solid {p["correct"]};
            background-color: {p["bg_primary"]};
            border-radius: 0 8px 8px 0;
        }}
        .incorrect-highlight {{
            color: {p["incorrect"]};
            font-weight: bold;
        }}
        .correct-highlight {{
            color: {p["correct"]};
            font-weight: bold;
        }}
        """
