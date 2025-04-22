from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize

from .CleanTheme import CleanTheme


class ActionButton(QPushButton):
    """A clean, minimalist button for actions"""

    def __init__(self, text, icon=None, primary=True, parent=None):
        """
        Initialize an action button

        Args:
            text (str): Button text
            icon: Icon to display (QIcon, path to image, or StandardPixmap)
            primary (bool): Whether to use primary (dark) or secondary (light) styling
            parent (QWidget): Parent widget
        """
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 9))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Set icon if provided
        if icon:
            # Convert to QIcon if it's not already
            if not isinstance(icon, QIcon):
                if isinstance(icon, str):
                    icon = QIcon(icon)
                elif isinstance(icon, int) or (hasattr(icon, "__int__") and not isinstance(icon, bool)):
                    from PyQt5.QtWidgets import QApplication

                    icon = QApplication.style().standardIcon(icon)  # type:ignore

            self.setIcon(icon)  # type:ignore
            self.setIconSize(QSize(16, 16))

        # Style based on primary or secondary
        if primary:
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
            """
            )
        else:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: white;
                    color: {CleanTheme.TEXT_PRIMARY};
                    border: 1px solid {CleanTheme.BORDER};
                    border-radius: 4px;
                    padding: 8px 15px;
                }}
                QPushButton:hover {{
                    background-color: #f5f5f5;
                }}
                QPushButton:pressed {{
                    background-color: #e0e0e0;
                }}
            """
            )
