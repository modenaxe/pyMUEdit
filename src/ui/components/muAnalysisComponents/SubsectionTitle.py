from PyQt5.QtWidgets import QLabel

from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class SubsectionTitle(QLabel):
    """Styled subsection title label for analysis components.
    
    Creates an uppercase, small-font title used for categorizing
    sections within analysis panels.
    """
    
    def __init__(self, text, parent=None):
        """Initialize the subsection title.
        
        Args:
            text: The title text to display
            parent: Parent widget (optional)
        """
        super().__init__(text, parent)
        self.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
            font-size: 10px;
            font-weight: 700;
            font-family: Arial;
            letter-spacing: 1px;
            margin-bottom: 2px;
            text-transform: uppercase;
            """
        )
