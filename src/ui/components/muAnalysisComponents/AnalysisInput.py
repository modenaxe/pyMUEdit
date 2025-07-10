from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QLabel, 
    QLineEdit,
)
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText

class AnalysisInput(QWidget):
    
    """
    Returns an input with a label
    """

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
                background-color: {CleanTheme.ANALYSIS_BG_CARD};
                color: {CleanTheme.ANALYSIS_TEXT_SECONDARY};
                border-radius: 4px;
                padding-left: 10px;
                height: 40px;
            }}
        """
        )
        self.input = input
        layout.addWidget(input)

    def set(self, value=None):
        self.input.setText(value)

    def get(self, value=None):
        return self.input.text()
