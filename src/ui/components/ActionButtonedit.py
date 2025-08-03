from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize
from .CleanTheme import CleanTheme
from pathlib import Path

ICON_DIR = Path(__file__).resolve().parent.parent.parent / "public"
def _ico(name):    
    return QIcon(str(ICON_DIR / f"{name}"))

class ActionButtonedit(QPushButton):
    """A clean, minimalist button for actions"""

    def __init__(self, text, icon=None, primary=True, parent=None, tabs=False, blue=False):
        """
        Initialize an action button

        Args:
            text (str): Button text
            icon: Icon to display (QIcon, path to image, or StandardPixmap)
            primary (bool): Whether to use primary (dark) or secondary (light) styling
            parent (QWidget): Parent widget
        """
        super().__init__(text, parent)
        

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Set icon if provided
        if icon:
            # Convert to QIcon if it's not already
            if not isinstance(icon, QIcon):
                if isinstance(icon, str):
                    icon = _ico(icon)
                elif isinstance(icon, int) or (hasattr(icon, "__int__") and not isinstance(icon, bool)):
                    from PyQt5.QtWidgets import QApplication

                    icon = QApplication.style().standardIcon(icon)  # type:ignore
            self.setIcon(icon)  # type:ignore
            self.setIconSize(QSize(16, 16))
            self.setText("")

        # Style based on primary or secondary
        if primary:
            font = QFont("Segoe UI")
            font.setPointSize(11)
            self.setFont(font)

            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: #333333;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 15px;
                }}
                QPushButton:hover {{
                    background-color: #555555;
                }}
                QPushButton:pressed {{
                    background-color: #222222;
                }}
                QPushButton:disabled {{
                    background-color: #999999;
                    color: #dddddd;
                }}
                QPushButton[active="true"] {{
                    background-color: #444444;
                }}
            """
            )
        
        elif tabs:
            font = QFont("Segoe UI")
            font.setPointSize(12)
            self.setFont(font)
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: #555555;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #f5f5f5;
                }}
    
                QPushButton:pressed {{
                    background-color: #e0e0e0;
                }}

                QPushButton[active="true"] {{
                    background-color: #0072ee;
                    color: white;
                }}

                QPushButton[active="true"]:hover {{
                    background-color: #1565C0;
                }}
            """
            )
        
        elif blue:
            font = QFont("Segoe UI")
            font.setPointSize(11)
            self.setFont(font)
            self.set_blue()
            
        else:
            font = QFont("Segoe UI")
            font.setPointSize(11)
            self.setFont(font)

            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: white;
                    color: {CleanTheme.TEXT_PRIMARY};
                    border: 1px solid {CleanTheme.BORDER};
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #f5f5f5;
                }}
                QPushButton:pressed {{
                    background-color: #e0e0e0;
                }}
                QPushButton:disabled {{
                    background-color: #f0f0f0;
                    color: #aaaaaa;
                    border: 1px solid #e0e0e0;
                }}
                QPushButton[active="true"] {{
                    background-color: #c0ffc0;
                    border: 1px solid green;
                    color: darkgreen;
                }}
            """
            )
    def set_active(self, active: bool):
        """Set the active visual state of the button."""
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        
    def get_active(self):
        return self.property("active")

    def set_blue(self):
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: #0072ee;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            QPushButton:hover {{
                background-color: #1565C0;
                color: #ffffff;
            }}

            QPushButton:pressed {{
                background-color: #e0e0e0;
            }}

            QPushButton:disabled {{
                background-color: #f0f0f0;
                color: #aaaaaa;
                border: 1px solid #e0e0e0;
            }}
            
            QPushButton[active="true"] {{
                background-color: #c0ffc0;
                border: 1px solid green;
                color: darkgreen;
            }}
            """
        )
