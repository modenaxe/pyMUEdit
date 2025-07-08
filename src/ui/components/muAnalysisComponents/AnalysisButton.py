from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme

class AnalysisButton(QPushButton):
    """
    Button for analysis tab UI 

    parameters:
        label (string): text for the button 
        action (lambda: action): the thing the button triggers. Make sure you include `lambda:` in param
    """
    def __init__(self, label="", action=None, parent=None):
        super().__init__(label, parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {CleanTheme.ANALYSIS_BG_BUTTON};
                color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                border-radius: 4px;
                padding: 0px 10px;
                height: 40px;
            }}
            QPushButton:hover {{
                background-color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                color: {CleanTheme.ANALYSIS_BG_BUTTON};
            }}
        """
        )
        self.clicked.connect(action)

