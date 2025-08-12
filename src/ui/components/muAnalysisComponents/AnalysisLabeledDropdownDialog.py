from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout, QWidget

from ui.components.muAnalysisComponents.AnalysisDropdownDialog import \
    AnalysisDropdownDialog
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class AnalysisLabeledDropdownDialog(QWidget):

    """UI component for defining a dark dropdown with a placeholder label"""

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
        """Getter function, just to make life a little easier
        Params: None
        Returns: (str) current selected item in dropdown. Empty string if nothing is selected.
        """
        return self.dropdown.currentText()
