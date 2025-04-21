from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os

from .CleanTheme import CleanTheme
from .SidebarButton import SidebarButton


class Sidebar(QFrame):
    """
    A clean sidebar with navigation buttons that matches the reference design.
    Uses SVG icons from the public folder and implements proper spacing.
    """

    def __init__(self, app_title="HDEMG App", parent=None):
        """
        Initialize a sidebar with app title and navigation buttons

        Args:
            app_title (str): App title to display at the top
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        self.setObjectName("cleanSidebar")
        self.setFixedWidth(180)

        # Apply styling - clean white background with subtle border
        self.setStyleSheet(
            f"""
            QFrame#cleanSidebar {{
                background-color: {CleanTheme.BG_SIDEBAR};
                border-right: 1px solid {CleanTheme.BORDER};
            }}
        """
        )

        # Set up layout with more padding at the top
        self.layout = QVBoxLayout(self)  # type:ignore
        self.layout.setContentsMargins(5, 20, 5, 20)
        self.layout.setSpacing(0)  # We'll control spacing through the buttons

        # Add app title and icon
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(15, 0, 15, 20)  # More space below title

        # App title
        app_title_label = QLabel(app_title)
        app_title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        app_title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        title_layout.addWidget(app_title_label)

        self.layout.addLayout(title_layout)

        # Container for navigation buttons with proper margins
        self.nav_container = QFrame()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(5, 0, 5, 0)  # Reduced side margins
        self.nav_layout.setSpacing(5)  # Space between buttons

        self.layout.addWidget(self.nav_container)
        self.layout.addStretch(1)

        # Store references to buttons
        self.buttons = {}

    def add_button(self, key, text, icon_name=None, is_selected=False):
        """
        Add a navigation button to the sidebar

        Args:
            key (str): Unique key for the button for later reference
            text (str): Button text
            icon_name (str): Name of SVG icon file in the public folder (without .svg)
            is_selected (bool): Whether the button is initially selected

        Returns:
            SidebarButton: The created button
        """
        # Determine icon path
        icon_path = None
        if icon_name:
            # Construct path to SVG in public folder
            icon_path = os.path.join("public", f"{icon_name}.svg")
            # If file doesn't exist, show a warning
            if not os.path.exists(icon_path):
                print(f"Warning: Icon {icon_path} not found")
                icon_path = None

        # Create button with icon and text
        button = SidebarButton(text, icon_path)
        button.set_selected(is_selected)

        # Add to layout and store reference
        self.nav_layout.addWidget(button)
        self.buttons[key] = button

        return button

    def select_button(self, key):
        """
        Set the selected state of a button

        Args:
            key (str): Key of the button to select
        """
        # Deselect all buttons
        for btn_key, button in self.buttons.items():
            button.set_selected(btn_key == key)
