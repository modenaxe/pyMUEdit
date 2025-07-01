from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QLabel, 
    QLineEdit,
)
from ui.components.CleanTheme import CleanTheme
from ui.components.AnalysisText import AnalysisText

"""
Returns an input with a label
"""
class AnalysisInput(QWidget):
    def __init__(self, label="", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # label 
        input_label = AnalysisText.create_label(label) 
        layout.addWidget(input_label)

        # input 
        input = QLineEdit()
        input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {CleanTheme.ANALYSIS_BG_DROPDOWN};
                color: {CleanTheme.ANALYSIS_TEXT_SECONDARY};
                border-radius: 4px;
                padding-left: 10px;
                height: 40px;
            }}
        """
        )
        # input_input.setPlaceholderText("")
        self.input = input
        layout.addWidget(input)

    def set(self, value=None):
        self.input.setText(value)

    def get(self, value=None):
        return self.input.text()
