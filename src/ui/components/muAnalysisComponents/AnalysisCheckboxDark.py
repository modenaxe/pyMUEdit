from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme

"""
Returns an input with a label. If you don't want a label, don't give it one
"""


class AnalysisCheckboxDark(QCheckBox):
    def __init__(self, label="", parent=None):
        super().__init__(label, parent)

        self.setStyleSheet(
            f"""
            QCheckBox {{
                font-family: Arial;
                font-size: 11px;
                color: {CleanTheme.ANALYSIS_DIALOG_TEXT};
                spacing: 8px;
                margin: 8px 0px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #ced4da;
                border-radius: 3px;
                background-color: #ffffff;
            }}
            QCheckBox::indicator:checked {{
                background-color: {CleanTheme.ANALYSIS_BG_BUTTON};
                border-color: {CleanTheme.ANALYSIS_BG_BUTTON};
            }}
            """
        )
