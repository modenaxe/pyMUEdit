from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QLabel, 
    QLineEdit,
)
from PyQt5.QtGui import QPalette, QColor
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText

"""
Returns an input with a label. If you don't want a label, don't give it one
"""
class AnalysisInput(QWidget):
    def __init__(self, label="", placeholder="", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # label 
        if (label != ""):
            input_label = AnalysisText.create_label(label) 
            layout.addWidget(input_label)

        # input
        # height has to be 38 because border isn't included
        input = QLineEdit()
        input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {CleanTheme.ANALYSIS_BG_CARD};
                color: {CleanTheme.TEXT_PRIMARY};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                padding-left: 10px;
                height: 38px;
            }}
        """
        )
        # placeholder stuff 
        input.setPlaceholderText(placeholder)
        palette = input.palette()
        palette.setColor(QPalette.PlaceholderText, QColor(CleanTheme.TEXT_SECONDARY))

        self.input = input
        layout.addWidget(input)

    def set(self, value=None):
        self.input.setText(value)

    def get(self, value=None):
        return self.input.text()

    # sets a specific width
    def set_width(self, width):
        self.setFixedWidth(width)
