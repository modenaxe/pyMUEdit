from PyQt5.QtWidgets import QSpinBox
from .CleanTheme import CleanTheme
from .FormField import FormField


class FormSpinBox(FormField):
    """
    A styled integer spin box with a label

    This component combines a label with a styled QSpinBox
    for a consistent look throughout the application.
    """

    def __init__(self, label_text, value=0, min_value=0, max_value=100, parent=None):
        """
        Initialize a spin box form field

        Args:
            label_text (str): The text for the label
            value (int): Initial value
            min_value (int): Minimum allowed value
            max_value (int): Maximum allowed value
            parent (QWidget, optional): Parent widget
        """
        super().__init__(label_text, parent)

        self.spinbox = QSpinBox()
        self.spinbox.setValue(value)
        self.spinbox.setRange(min_value, max_value)
        self.spinbox.setStyleSheet(
            f"""
            QSpinBox {{
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 16px;
                subcontrol-origin: margin;
                border-left: 1px solid {CleanTheme.BORDER};
            }}
            QSpinBox::up-button {{
                subcontrol-position: top right;
                border-top-right-radius: 3px;
            }}
            QSpinBox::down-button {{
                subcontrol-position: bottom right;
                border-bottom-right-radius: 3px;
            }}
            QSpinBox::up-arrow {{
                image: url(public/up_arrow_icon.svg);
                width: 10px;
                height: 10px;
            }}
            QSpinBox::down-arrow {{
                image: url(public/down_arrow_icon.svg);
                width: 10px;
                height: 10px;
            }}
            """
        )

        self.layout.addWidget(self.spinbox)
