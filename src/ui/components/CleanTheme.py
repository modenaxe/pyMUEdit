from PyQt5.QtGui import QColor


class CleanTheme:
    """Clean, minimalist color theme for the application"""

    # Main backgrounds
    BG_MAIN = "#F9F9F9"  # Very light gray for main background
    BG_CARD = "#FFFFFF"  # White for cards
    BG_SIDEBAR = "#FFFFFF"  # White for sidebar
    BG_VISUALIZATION = "#F2F2F2"  # Light gray for visualization cards

    # Text colors
    TEXT_PRIMARY = "#333333"  # Dark gray for primary text
    TEXT_SECONDARY = "#777777"  # Medium gray for secondary text

    # Borders and shadows
    BORDER = "#E0E0E0"  # Light gray for borders
    SHADOW = QColor(0, 0, 0, 15)  # Very subtle shadow
