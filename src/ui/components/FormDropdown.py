from PyQt5.QtWidgets import QComboBox
from .CleanTheme import CleanTheme
from .FormField import FormField


class FormDropdown(FormField):
    """
    A styled dropdown/combobox with a label

    This component combines a label with a styled QComboBox
    for a consistent look throughout the application.
    """

    def __init__(self, label_text, items=None, parent=None):
        """
        Initialize a dropdown form field

        Args:
            label_text (str): The text for the label
            items (list, optional): List of items to add to the dropdown
            parent (QWidget, optional): Parent widget
        """
        super().__init__(label_text, parent)

        self.dropdown = QComboBox()
        self.dropdown.setStyleSheet(
            f"""
            QComboBox {{
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                padding: 5px 8px;
                background-color: white;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {CleanTheme.BORDER};
            }}
            QComboBox::down-arrow {{
                image: url(public/down_arrow_icon.svg);
                width: 10px;
                height: 10px;
            }}
            """
        )

        if items:
            self.dropdown.addItems(items)

        self.layout.addWidget(self.dropdown)
