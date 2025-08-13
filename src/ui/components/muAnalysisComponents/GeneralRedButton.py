from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton

from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class GeneralRedButton(QPushButton):

    """ui component for general warning red buttons"""

    def __init__(self, label="", parent=None):
        super().__init__(label, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton{{
                background-color: {CleanTheme.RED_BACKGROUND}; /* Red color for reset */
                color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                border: none;
                border-radius: 5px;
                padding: 0px 10px;
                height: 40px;
            }}
            QPushButton:hover {{
                background-color: {CleanTheme.RED_HOVER}; /* Darker red on hover */
            }}
            """
        )
