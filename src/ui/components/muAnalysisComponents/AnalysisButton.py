from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme

class AnalysisButton(QPushButton):
    """
    Button for analysis tab UI 

    parameters:
        label (string): text for the button 
        action (action): the thing the button triggers
            - sometimes you have to put lambda in it, I have no idea how python works
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

    # Sets the width 
    # I defined the width for the 'revert' button to be 100, so just defining that for consistency,
    # in case someone else wants to use this method 
    # I would've defined a function that essentially removes the width css line, but it's looks 
    # kinda complicated so I don't think it's worth it
    def set_width(self, width):
        self.setFixedWidth(width)

