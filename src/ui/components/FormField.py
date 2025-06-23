from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from .CleanTheme import CleanTheme


class FormField(QWidget):
    """
    Base class for form fields with a label and input widget

    This class serves as a foundation for all form field components,
    handling the common layout and styling.
    """

    def __init__(self, label_text, parent=None):
        """
        Initialize a form field with a label

        Args:
            label_text (str): The text for the label
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        self.layout = QVBoxLayout(self)  # type:ignore
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        self.label = QLabel(label_text)
        self.label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        self.label.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")

        self.layout.addWidget(self.label)
