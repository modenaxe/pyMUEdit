from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import QPushButton

from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class PropertiesInnerDialogButton(QPushButton):

    """Buttons within Motor Unit Properties dialogs"""

    def __init__(self, text):
        super().__init__(text)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Arial", 11))
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #495057;
                color: #e9ecee;
                border: none;
                height: 40%;
                max-width: 100%;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: #4a5672;
            }}
        """
        )
