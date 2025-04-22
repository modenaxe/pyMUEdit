from PyQt5.QtWidgets import QWidget, QVBoxLayout
from .CleanTheme import CleanTheme
from .CleanCard import CleanCard
from .SectionHeader import SectionHeader


class SettingsGroup(CleanCard):
    """
    A group of settings in a card with a title

    This component provides a clean card with a header and organized layout
    for grouping related settings.
    """

    def __init__(self, title, parent=None):
        """
        Initialize a settings group

        Args:
            title (str): The title for the settings group
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        # Create section header
        self.header = SectionHeader(title)

        # Create container for fields
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(10)

        # Add to card layout
        self.content_layout.addWidget(self.header)
        self.content_layout.addWidget(self.fields_container)
        self.content_widget.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")

    def add_field(self, field):
        """
        Add a form field to this settings group

        Args:
            field (QWidget): The form field to add

        Returns:
            QWidget: The added field for chaining
        """
        self.fields_layout.addWidget(field)
        return field
