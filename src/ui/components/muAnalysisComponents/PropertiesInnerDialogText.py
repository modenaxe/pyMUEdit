from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLineEdit

from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class PropertiesInnerDialogText(QLineEdit):

    """Inputs within Motor Unit Properties dialogs"""

    def __init__(self, text):
        super().__init__()
        self.setMinimumHeight(32)
        self.setPlaceholderText(text)
        self.setFont(QFont("Arial", 11))
        self.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 10px;
                border: 2px solid {CleanTheme.BORDER};
                border-radius: 6px;
                background-color: {CleanTheme.ANALYSIS_BG_CARD};
                color: {CleanTheme.TEXT_PRIMARY};
                font-size: 11pt;
            }}
            QLineEdit:focus {{
                border-color: {CleanTheme.ANALYSIS_BG_BUTTON};
            }}
        """
        )
