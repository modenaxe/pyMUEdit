from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme

class MajorHeading(QLabel):

    """
    ui component for major headings on sidebars
    """

    def __init__(self, label):
        super().__init__(label)
        self.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")