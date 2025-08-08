from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme

class GeneralButton(QPushButton):

    """
    General button for sidebars
    parameters:
        label (string): text for the button 
        action (lambda: action): the action the button triggers.
    """

    def __init__(self, label="", action=None, parent=None):
        super().__init__(label, parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {CleanTheme.ANALYSIS_BG_BUTTON};
                color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                border-radius: 5px;
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

    # Sets the width 
    # I defined the width for the 'revert' button to be 100, so just defining that for consistency,
    def set_width(self, width):
        self.setFixedWidth(width)

