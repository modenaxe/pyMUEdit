from PyQt5.QtWidgets import QComboBox 
from .CleanTheme import CleanTheme
from PyQt5.QtCore import Qt


class AnalysisDropdown(QComboBox):
    """
    For dropdown inputs for the analysis tab
    """

    def __init__(self, label, items=None, parent=None):
        """
        Initialise a dropdown with a label

        Args:
            label: (string): placeholder text for dropdown
            items (list of strings, optional): Array of options 
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        self.setStyleSheet(
            f"""
            QComboBox {{
                color: {CleanTheme.ANALYSIS_TEXT_SECONDARY};
                background-color: {CleanTheme.ANALYSIS_BG_DROPDOWN}; 
                border-radius: 4px;
                margin: 0px;
                padding-left: 10px;
                height: 30px;
                font-weight: 400;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                border: 0px;
                padding-right: 10px;
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
        if items:
            self.addItems(items)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # self.layout.setContentsMargins(0, 0, 0, 0)
        # self.layout.setSpacing(5)
