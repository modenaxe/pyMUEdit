from PyQt5.QtWidgets import QLineEdit

from .CleanTheme import CleanTheme
from .FormField import FormField


class FormInput(FormField):
    """
    A styled input box with a label

    This component combines a label with a styled QLineEdit
    for a consistent look throughout the application.
    """

    def __init__(self, label_text, default_text=None, parent=None):
        """
        Initialize a dropdown form field

        Args:
            label_text (str): The text for the label
            default_text (str, optional): default text
            parent (QWidget, optional): Parent widget
        """
        super().__init__(label_text, parent)

        self.input = QLineEdit()
        self.input.setStyleSheet(
            f"""
            QLineEdit {{
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                padding: 5px 8px;
                background-color: white;
            }}
            """
        )

        if default_text:
            self.input.setText(default_text)

        self.layout.addWidget(self.input)
