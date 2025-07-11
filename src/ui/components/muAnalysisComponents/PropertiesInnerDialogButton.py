from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from PyQt5.QtGui import QFont, QCursor

class PropertiesInnerDialogButton(QPushButton):

    """Buttons within Motor Unit Properties dialogs"""

    def __init__(self, text):
        super().__init__(text )
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #495057;
                color: #e9ecee;
                border: none;
                height: 40%;
                max-width: 100%;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #4a5672;
            }}
        """
        )
