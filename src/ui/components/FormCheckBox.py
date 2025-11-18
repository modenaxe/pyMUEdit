from PyQt5.QtWidgets import QCheckBox
from .CleanTheme import CleanTheme
from .FormField import FormField


class FormCheckBox(FormField):
    """
    A styled checkbox with a label.

    This component uses the existing FormField layout (label + widget)
    and inserts a QCheckBox styled consistently with the application's theme.
    """

    def __init__(self, label_text, checked=False, parent=None):
        """
        Initialize a checkbox form field.

        Args:
            label_text (str): The text for the label.
            checked (bool): Whether the checkbox starts checked.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(label_text, parent)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)

        # Style consistent with CleanTheme
        self.checkbox.setStyleSheet(
            f"""
            QCheckBox {{
                spacing: 8px;
            }}

            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 3px;
                background: white;
            }}

            QCheckBox::indicator:checked {{
                image: url(public/save_success.png);
                border: 1px solid {CleanTheme.BORDER};
            }}

            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid {CleanTheme.BORDER};
            }}
            """
        )

        self.layout.addWidget(self.checkbox)

    def isChecked(self):
        """Convenience getter."""
        return self.checkbox.isChecked()

    def setChecked(self, value: bool):
        """Convenience setter."""
        self.checkbox.setChecked(value)