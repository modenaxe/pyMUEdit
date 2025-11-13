from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class AnalysisInput(QWidget):

    """UI component for defining a text input with an (optional)
    label on top, and/or an (optional) placeholder label
    """

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
        palette.setColor(
            QPalette.PlaceholderText, QColor(
                CleanTheme.TEXT_SECONDARY))

        self.input = input
        layout.addWidget(input)

    def set(self, value=""):
        """Defines the text within the input
        Params:
            - value="": the text to-be placed within the input
        Returns: None
        """
        self.input.setText(value)

    def get(self):
        """Returns the text within the input
        Params: None
        Returns: None
        """
        return self.input.text()

    # sets a specific width
    def set_width(self, width):
        self.setFixedWidth(width)
