from pathlib import Path

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QSizePolicy,
                             QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

# Import custom components
from ui.components import (ActionButton, CleanCard, CleanTheme, SectionHeader,
                           Sidebar, VisualizationPanel)
from ui.components.CleanScrollBar import CleanScrollBar

# Footer class for resuability, extensibility and maintability
class Footer(QFrame):
    """Persistent footer component with file info and nav buttons across all tabs."""

    def __init__(self, on_prev=None, on_next=None, parent=None):
        super().__init__(parent)

        """Create the footer with file info and navigation buttons."""
        self.setObjectName("footer")
        self.setStyleSheet(
            f"""
            #footer {{
                background-color: {CleanTheme.BG_MAIN};
                border-top: 1px solid {CleanTheme.BORDER};
            }}
        """
        )
        
        footer_layout = QHBoxLayout(self)
        footer_layout.setContentsMargins(20, 10, 20, 10)

        # Create file info labels
        self.footer_file_info = QLabel("No file selected")
        self.footer_file_info.setStyleSheet(
            f"color: {CleanTheme.TEXT_PRIMARY};")

        self.size_info = QLabel("Size: --")
        self.size_info.setStyleSheet(
            f"color: {CleanTheme.TEXT_SECONDARY};")

        self.format_info = QLabel("Format: --")
        self.format_info.setStyleSheet(
            f"color: {CleanTheme.TEXT_SECONDARY};")

        # Add file info to layout
        footer_layout.addWidget(self.footer_file_info)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.size_info)
        footer_layout.addSpacing(10)
        footer_layout.addWidget(self.format_info)
        footer_layout.addSpacing(20)

        # Create navigation buttons
        self.prev_btn = ActionButton("← Previous", primary=False)
        self.prev_btn.setEnabled(False)
        #  prev_btn.clicked.connect(import_window.go_back)

        self.next_btn = ActionButton("Next →", primary=True)
        self.next_btn.setEnabled(False)
        # self.next_btn.clicked.connect(
        #     import_window.go_to_algorithm_screen)
        # import_window.next_btn.setEnabled(False)

        # Add navigation buttons to layout
        footer_layout.addWidget(self.prev_btn)
        footer_layout.addSpacing(10)
        footer_layout.addWidget(self.next_btn)

