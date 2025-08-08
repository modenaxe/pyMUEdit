from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout, QWidget

from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme

# defining absolute path for icons
ABS_PATH = Path(__file__).parent.parent.parent.parent
ICONS_PATH = ABS_PATH / "public"
down_arrow_white_path = ICONS_PATH / "down_arrow_white_icon.svg"


# For dropdown inputs for the analysis tab (factory method)
class AnalysisDropdownDialog(QComboBox):

    """
    Initialise a dropdown without a label (label is a placeholder)
    """

    def __init__(self, label, items=None, parent=None):
        super().__init__(parent)

        self.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {CleanTheme.ANALYSIS_DIALOG_DROPDOWN};
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
                image: url({down_arrow_white_path});
                width: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {CleanTheme.ANALYSIS_DIALOG_TEXT};
                border: 0px;
            }}
            QComboBox:disabled {{
                background-color: {CleanTheme.ANALYSIS_BG_DROPDOWN_DISABLED};
                color: {CleanTheme.TEXT_PRIMARY}
            }}
            """
        )
        self.setPlaceholderText(label)
        if items:
            self.addItems(items)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


# too hard to convert the old class 'AnalysisDropdown' into a QWidget child class, that supports
# labeled and non-labeled dropdowns, so I thought a new class would be better
class AnalysisLabeledDropdownDialog(QWidget):
    def __init__(self, label="", items=None, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # the label
        label = AnalysisText.create_label(label)
        layout.addWidget(label)

        # the dropdown, taken from init
        dropdown = AnalysisDropdownDialog("", items=items)
        dropdown.adjustSize()
        dropdown.setPlaceholderText("")
        layout.addWidget(dropdown)
        self.dropdown = dropdown

    def get(self):
        return self.dropdown.currentText()
