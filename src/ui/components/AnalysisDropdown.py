from PyQt5.QtWidgets import (
    QComboBox, 
    QFrame, 
    QVBoxLayout,
    QLabel,
)
from PyQt5.QtCore import Qt
from ui.components.CleanTheme import CleanTheme
from ui.components.AnalysisText import AnalysisText


# For dropdown inputs for the analysis tab (factory method)
class AnalysisDropdown(QComboBox):
    """
    Initialise a dropdown without a label (label is a placeholder)

    Args:
        label: (string): placeholder text for dropdown
        items (list of strings, optional): Array of options 
        parent (QWidget, optional): Parent widget
    """
    def __init__(self, label, items=None, parent=None):
        super().__init__(parent)

        self.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {CleanTheme.ANALYSIS_BG_DROPDOWN}; 
                color: {CleanTheme.ANALYSIS_TEXT_SECONDARY};
                border-radius: 4px;
                margin: 0px;
                padding-left: 10px;
                height: 40px;
                font-weight: 400;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                border: 0px;
                width: fit-content;
                padding: 0px 20px;
            }}
            QComboBox::down-arrow {{
                image: url(src/public/down_arrow_white_icon.svg);
                width: 10px;
            }}
            QComboBox QAbstractItemView {{
                border: 0px;
            }}
            """
        )
        self.setPlaceholderText(label)
        if items: self.addItems(items)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def get_value(self):
        return self.currentText()

    """
    Initialise a dropdown with a label

    Args:
        label: (string): placeholder text for dropdown
        items (list of strings, optional): Array of options 
        parent (QWidget, optional): Parent widget
    """
    @staticmethod
    def labeled_dropdown(label="", items=None, parent=None):
        box = QFrame()
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box.layout = box_layout

        # the label
        dropdown_label = AnalysisText.create_label(label)
        box_layout.addWidget(dropdown_label)

        # the dropdown, taken from init
        dropdown_dropdown = AnalysisDropdown("", items=items)
        dropdown_dropdown.adjustSize()
        dropdown_dropdown.setPlaceholderText("")
        box.dropdown = dropdown_dropdown
        box_layout.addWidget(dropdown_dropdown)

        return box 

