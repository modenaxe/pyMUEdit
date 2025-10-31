from pathlib import Path

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QSizePolicy,
                             QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

def create_footer(import_window, prev_window, next_window):
    """Create the footer with file info and navigation buttons."""
    footer = QFrame()
    footer.setObjectName("footer")
    footer.setStyleSheet(
        f"""
        #footer {{
            background-color: {CleanTheme.BG_MAIN};
            border-top: 1px solid {CleanTheme.BORDER};
        }}
    """
    )
    footer_layout = QHBoxLayout(footer)
    footer_layout.setContentsMargins(20, 10, 20, 10)

    # Create file info labels
    import_window.footer_file_info = QLabel("No file selected")
    import_window.footer_file_info.setStyleSheet(
        f"color: {CleanTheme.TEXT_PRIMARY};")
    import_window.size_info = QLabel("Size: --")
    import_window.size_info.setStyleSheet(
        f"color: {CleanTheme.TEXT_SECONDARY};")
    import_window.format_info = QLabel("Format: --")
    import_window.format_info.setStyleSheet(
        f"color: {CleanTheme.TEXT_SECONDARY};")

    # Add file info to layout
    footer_layout.addWidget(import_window.footer_file_info)
    footer_layout.addStretch(1)
    footer_layout.addWidget(import_window.size_info)
    footer_layout.addSpacing(10)
    footer_layout.addWidget(import_window.format_info)
    footer_layout.addSpacing(20)

    # Create navigation buttons
    # prev_btn = ActionButton("← Previous", primary=False)
    # prev_btn.clicked.connect(import_window.go_back)

    import_window.next_btn = ActionButton("Next →", primary=True)
    import_window.next_btn.clicked.connect(
        import_window.go_to_algorithm_screen)
    import_window.next_btn.setEnabled(False)

    # Add navigation buttons to layout
    # footer_layout.addWidget(prev_btn)
    footer_layout.addSpacing(10)
    footer_layout.addWidget(import_window.next_btn)
    return footer
