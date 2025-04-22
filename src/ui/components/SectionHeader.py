from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont

from .CleanTheme import CleanTheme


class SectionHeader(QWidget):
    """A clean section header with title"""

    def __init__(self, title, parent=None):
        """
        Initialize a section header

        Args:
            title (str): Section title
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        self.layout = QVBoxLayout(self)  # type:ignore
        self.layout.setContentsMargins(0, 0, 0, 10)

        # Create title label
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Normal))
        self.title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")

        self.layout.addWidget(self.title_label)
