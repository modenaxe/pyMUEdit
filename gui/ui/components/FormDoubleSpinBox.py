from PyQt5.QtWidgets import QDoubleSpinBox
from .CleanTheme import CleanTheme
from .FormField import FormField


class FormDoubleSpinBox(FormField):
    """
    A styled double spin box with a label

    This component combines a label with a styled QDoubleSpinBox
    for a consistent look throughout the application.
    """

    def __init__(self, label_text, value=0.0, min_value=0.0, max_value=1.0, step=0.1, parent=None):
        """
        Initialize a double spin box form field

        Args:
            label_text (str): The text for the label
            value (float): Initial value
            min_value (float): Minimum allowed value
            max_value (float): Maximum allowed value
            step (float): Step size for increments/decrements
            parent (QWidget, optional): Parent widget
        """
        super().__init__(label_text, parent)

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setValue(value)
        self.spinbox.setRange(min_value, max_value)
        self.spinbox.setSingleStep(step)
        self.spinbox.setStyleSheet(
            f"""
            QDoubleSpinBox {{
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 16px;
                subcontrol-origin: margin;
                border-left: 1px solid {CleanTheme.BORDER};
            }}
            QDoubleSpinBox::up-button {{
                subcontrol-position: top right;
                border-top-right-radius: 3px;
            }}
            QDoubleSpinBox::down-button {{
                subcontrol-position: bottom right;
                border-bottom-right-radius: 3px;
            }}
            QDoubleSpinBox::up-arrow {{
                image: url(public/up_arrow_icon.svg);
                width: 10px;
                height: 10px;
            }}
            QDoubleSpinBox::down-arrow {{
                image: url(public/down_arrow_icon.svg);
                width: 10px;
                height: 10px;
            }}
            """
        )

        self.layout.addWidget(self.spinbox)
