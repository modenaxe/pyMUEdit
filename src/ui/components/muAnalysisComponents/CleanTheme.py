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

    ################################################################
    ########################### ANALYSIS ###########################
    ################################################################
    ANALYSIS_BG_MAIN = "#f8f9fa"
    ANALYSIS_BG_CARD = "#ffffff"
    ANALYSIS_BG_SIDEBAR = "#343a40"
    ANALYSIS_BG_TOPBAR = "#ffffff"
    ANALYSIS_BG_DROPDOWN = "#394150"
    ANALYSIS_BG_DROPDOWN_DISABLED = "#7d8aa3"
    ANALYSIS_BG_DROPDOWN_SEC = "#0A0C0E"
    ANALYSIS_BG_BUTTON = "#495057"
    ANALYSIS_TEXT_PRIMARY = "#ffffff"
    ANALYSIS_TEXT_SECONDARY = "#cccccc"
    ANALYSIS_TEXT_TERTIARY = "#8e8e8e"
    ANALYSIS_TEXT_BUTTON = "#e9ecee"
    ANALYSIS_TEXT_PROMPT = "#6c757d"
    ANALYSIS_TEXT_DARK = "#444444"
    ANALYSIS_DIALOG_BACKGROUND = "#e4e2e2"
    ANALYSIS_DIALOG_TEXT = "#394150"
    ANALYSIS_DIALOG_DROPDOWN = "#60676E"  # unused

    ################################################################
    ########################### DIALOG ###########################
    ################################################################

    DIALOG_TEXT = "#212529"
    DIALOG_CANCEL = "#6c757d"
    DIALOG_CANCEL_HOVER = "#5a6268"
    DIALOG_CONFIRM = "#dc3545"
    DIALOG_CONFIRM_HOVER = "#c82333"

    ################################################################
    ########################### REDS ###########################
    ################################################################

    RED_BACKGROUND = "#e04136"
    RED_HOVER = "#c72b2b"

    """
        self.colors = {
            "bg_main": "#f8f9fa",
            "bg_card": "#ffffff",
            "bg_sidebar": "#f8f9fa",
            "bg_topbar": "#ffffff",
            "border_light": "#e9ecef",
            "shadow": QColor(0, 0, 0, 25),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_title": "#343a40",
            "button_dark_bg": "#343a40",
            "button_dark_hover": "#495057",
            "button_grey_bg": "#e9ecee",
            "checkbox_bg": "#f1f3f5",
    """
