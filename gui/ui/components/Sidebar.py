from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os

from .CleanTheme import CleanTheme
from .SidebarButton import SidebarButton
from .DatasetItem import DatasetItem
from .SectionHeader import SectionHeader


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

        # Keep track of added sections for later cleanup
        self.recent_files_section = None

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

    def add_recent_files_section(self, recent_files, on_file_clicked=None):
        """
        Add a Recent Files section to the sidebar

        Args:
            recent_files (list): List of filenames to display
            on_file_clicked (function): Callback function when a file is clicked
        """
        # First remove any existing recent files section
        self.clear_recent_files_section()

        # Create container for recent files
        self.recent_files_section = QFrame()
        recent_files_layout = QVBoxLayout(self.recent_files_section)
        recent_files_layout.setContentsMargins(5, 10, 5, 0)
        recent_files_layout.setSpacing(5)

        # Add section header
        recent_header = SectionHeader("Recent Files")
        recent_files_layout.addWidget(recent_header)

        # Add recent files
        from PyQt5.QtGui import QCursor

        for filename in recent_files:
            # Calculate file size (for demonstration)
            file_size = "2.4 MB"  # Placeholder
            metadata = f"{file_size}"

            # Create dataset item
            dataset_item = DatasetItem(filename, metadata)

            # Make the dataset item clickable
            dataset_item.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if on_file_clicked:
                # Use a lambda with default argument to capture the current filename
                dataset_item.mousePressEvent = lambda event, f=filename: on_file_clicked(f)  # type:ignore

            recent_files_layout.addWidget(dataset_item)

        # Add the recent files section to the sidebar layout before the stretch
        self.layout.insertWidget(self.layout.count() - 1, self.recent_files_section)

    def clear_recent_files_section(self):
        """Remove any existing recent files section from the sidebar"""
        if self.recent_files_section:
            # Remove from layout
            self.layout.removeWidget(self.recent_files_section)
            # Schedule for deletion
            self.recent_files_section.deleteLater()
            self.recent_files_section = None
