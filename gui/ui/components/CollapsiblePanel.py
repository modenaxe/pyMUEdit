from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtSvg import QSvgWidget

from .CleanTheme import CleanTheme


class CollapsiblePanel(QFrame):
    """
    A collapsible panel with header and content area
    that can be expanded or collapsed by clicking the header.
    """

    def __init__(self, title, parent=None):
        """
        Initialize a collapsible panel

        Args:
            title (str): The title for the panel
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        # Setup frame
        self.setObjectName("collapsiblePanel")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            f"""
            QFrame#collapsiblePanel {{
                background-color: {CleanTheme.BG_CARD};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 8px;
            }}
            """
        )

        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Create header with expand/collapse button
        self.header_widget = QWidget()
        self.header_widget.setObjectName("collapsibleHeader")
        self.header_widget.setStyleSheet(
            f"""
            QWidget#collapsibleHeader {{
                background-color: {CleanTheme.BG_CARD};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {CleanTheme.BORDER};
            }}
            QWidget#collapsibleHeader:hover {{
                background-color: {CleanTheme.BG_SIDEBAR};
            }}
            """
        )
        self.header_widget.setCursor(Qt.CursorShape.PointingHandCursor)

        # Header layout
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(15, 8, 15, 8)

        # Title label
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")

        # Expand/collapse indicator
        self.toggle_button = QPushButton()
        self.toggle_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {CleanTheme.TEXT_SECONDARY};
                padding: 0px;
            }}
            """
        )
        self.toggle_button.setFixedSize(20, 20)

        # Use SVG icon for toggle button
        self.toggle_button.setIcon(QIcon("public/down_arrow_icon.svg"))
        self.toggle_button.setIconSize(QSize(10, 10))
        # Add header components
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.toggle_button)

        # Content area
        self.content_widget = QWidget()
        self.content_widget.setObjectName("collapsibleContent")
        self.content_widget.setStyleSheet(
            f"""
            QWidget#collapsibleContent {{
                background-color: {CleanTheme.BG_CARD};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            """
        )

        # Content layout
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(10)

        # Add header and content to main layout
        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.content_widget)

        # Set initial state
        self.is_expanded = True

        # Connect signals
        self.header_widget.mousePressEvent = self.toggle_collapsed  # type:ignore
        self.toggle_button.clicked.connect(self.toggle_collapsed)

    def add_widget(self, widget):
        """
        Add a widget to the content area

        Args:
            widget (QWidget): The widget to add

        Returns:
            QWidget: The added widget for chaining
        """
        self.content_layout.addWidget(widget)
        return widget

    def toggle_collapsed(self, event=None):
        """Toggle between expanded and collapsed states"""
        self.is_expanded = not self.is_expanded

        # Update the toggle button icon based on state
        if self.is_expanded:
            self.toggle_button.setIcon(QIcon("public/down_arrow_icon.svg"))
        else:
            self.toggle_button.setIcon(QIcon("public/up_arrow_icon.svg"))

        # Show/hide content
        self.content_widget.setVisible(self.is_expanded)
