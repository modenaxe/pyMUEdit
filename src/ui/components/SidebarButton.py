from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtSvg import QSvgWidget
import os

from .CleanTheme import CleanTheme


class SidebarButton(QPushButton):
    """
    A clean sidebar button with SVG icon and text that matches the reference design.
    Shows a light gray rounded rectangle background ONLY on hover.
    """

    def __init__(self, text, icon_path=None, parent=None):
        """
        Initialize a sidebar button with text and optional SVG icon

        Args:
            text (str): Button text
            icon_path (str): Path to SVG icon file in the public folder
            parent (QWidget): Parent widget
        """

        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(40)  # Taller buttons for better spacing

        # Setup layout for proper icon and text alignment
        self.layout = QHBoxLayout(self)  # type:ignore
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(10)  # Space between icon and text

        # Add SVG icon if provided
        self.icon_widget = None
        if icon_path:
            # Make sure the file exists
            if os.path.exists(icon_path):
                self.icon_widget = QSvgWidget(icon_path)
                self.icon_widget.setFixedSize(18, 18)
                self.layout.addWidget(self.icon_widget)

        # Add text label for better control over alignment
        self.text_label = QLabel(text)
        self.text_label.setFont(QFont("Segoe UI", 9))
        self.layout.addWidget(self.text_label)

        # Add stretch to push content to the left
        self.layout.addStretch(1)

        # Apply styling
        self.setStyleSheet(
            """
            QPushButton {
                border: none;
                background-color: transparent;
                text-align: left;
                padding: 8px 0px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 6px;
            }
            QPushButton:checked {
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 6px;
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
        """
        )

        # Make the button checkable for selected state
        self.setCheckable(True)

    def set_selected(self, selected):
        """Set the button's selected state"""
        self.setChecked(selected)
        if selected:
            self.text_label.setStyleSheet("font-weight: bold;")
        else:
            self.text_label.setStyleSheet("")

    def set_icon(self, icon_path):
        """Change the button's icon to a new SVG"""
        if not os.path.exists(icon_path):
            return

        if self.icon_widget:
            self.icon_widget.load(icon_path)
        else:
            self.icon_widget = QSvgWidget(icon_path)
            self.icon_widget.setFixedSize(18, 18)
            self.layout.insertWidget(0, self.icon_widget)
