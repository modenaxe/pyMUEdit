from PyQt5.QtWidgets import (
    QComboBox, 
    QFrame, 
    QVBoxLayout,
    QLabel,
    QWidget,
)
from PyQt5.QtCore import Qt
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText


# For dropdown inputs for the analysis tab (factory method)
class AnalysisDropdown(QComboBox):
    
    """
    Initialise a dropdown without a label (label is a placeholder)
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


# too hard to convert the old class 'AnalysisDropdown' into a QWidget child class, that supports
# labeled and non-labeled dropdowns, so I thought a new class would be better 
class AnalysisLabeledDropdown(QWidget):
    def __init__(self, label="", items=None, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # the label
        label = AnalysisText.create_label(label)
        layout.addWidget(label)

        # the dropdown, taken from init
        dropdown = AnalysisDropdown("", items=items)
        dropdown.adjustSize()
        dropdown.setPlaceholderText("")
        layout.addWidget(dropdown)
        self.dropdown = dropdown

    def get(self):
        return self.dropdown.currentText()

