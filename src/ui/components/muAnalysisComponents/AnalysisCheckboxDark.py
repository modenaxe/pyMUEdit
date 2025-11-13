from PyQt5.QtWidgets import QCheckBox
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class AnalysisCheckboxDark(QCheckBox):

    """UI component for creating a dark checkbox with an (optional) label"""

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
                background-color: #333333;
                border-color: #333333;
            }}
            """
        )
