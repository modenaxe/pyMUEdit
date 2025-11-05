from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox

# defining absolute path for icons
ABS_PATH = Path(__file__).parent.parent.parent.parent
ICONS_PATH = ABS_PATH / "public"
down_arrow_path = "public/down_arrow_icon.svg"


# For dropdown inputs for the analysis tab (factory method)
class AnalysisDropdownDialog(QComboBox):

    """UI component for defining a dark dropdown with a placeholder label"""

    def __init__(self, label, items=None, parent=None):
        super().__init__(parent)

        self.setStyleSheet(
            f"""
            QComboBox {{
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin: 0px;
                padding-left: 10px;
                height: 40px;
                font-weight: 400;
                font-size: 14px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                border: none;
                width: 40px;
                border-left: 1px solid #ddd;
                background: transparent;
                margin-left: 5px;
            }}
            QComboBox::down-arrow {{
                image: url({down_arrow_path});
                width: 10px;
                height: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                selection-background-color: #0078d4;
                selection-color: white;
                outline: none;
                font-size: 14px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #e5e5e5;
            }}
            QComboBox QAbstractItemView::item:last {{
                border-bottom: none;
            }}
            QComboBox:disabled {{
                background-color: #f2f2f2;
                color: gray;
            }}
            """
        )
        self.setPlaceholderText(label)
        if items:
            self.addItems(items)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
