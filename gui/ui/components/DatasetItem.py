from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize

from .CleanTheme import CleanTheme


class DatasetItem(QFrame):
    """A clean list item for displaying dataset information"""

    def __init__(self, filename, metadata, parent=None):
        """
        Initialize a dataset item

        Args:
            filename (str): Name of the dataset file
            metadata (str): Additional metadata like size and row count
            parent (QWidget): Parent widget
        """
        super().__init__(parent)
        self.setObjectName("datasetItem")
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumHeight(50)

        # Apply styling
        self.setStyleSheet(
            f"""
            QFrame#datasetItem {{
                background-color: transparent;
                border-bottom: 1px solid {CleanTheme.BORDER};
            }}
            QFrame#datasetItem:hover {{
                background-color: rgba(0, 0, 0, 0.02);
            }}
        """
        )

        # Set up layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # File icon - get proper icon based on file extension
        file_ext = filename.split(".")[-1].lower() if "." in filename else ""
        icon_path = f"public/file_{file_ext}.svg"

        # Default to standard file icon if custom icon not found
        from PyQt5.QtWidgets import QApplication, QStyle

        file_icon = QLabel()
        file_icon.setFixedSize(24, 24)
        file_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Use an appropriate icon based on the file type
        icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)  # type:ignore
        file_icon.setPixmap(icon.pixmap(QSize(20, 20)))

        layout.addWidget(file_icon)

        # Add file information
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        filename_label = QLabel(filename)
        filename_label.setFont(QFont("Segoe UI", 9))
        filename_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")

        metadata_label = QLabel(metadata)
        metadata_label.setFont(QFont("Segoe UI", 8))
        metadata_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")

        info_layout.addWidget(filename_label)
        info_layout.addWidget(metadata_label)
        layout.addLayout(info_layout)

        # Add spacer to push menu button to the right
        layout.addStretch(1)

        # Menu button (three dots)
        menu_button = QPushButton("⋮")
        menu_button.setFont(QFont("Segoe UI", 12))
        menu_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        menu_button.setFixedSize(24, 24)
        menu_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {CleanTheme.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                color: {CleanTheme.TEXT_PRIMARY};
            }}
        """
        )

        layout.addWidget(menu_button)

        # Store references to components for later access
        self.filename_label = filename_label
        self.metadata_label = metadata_label
        self.menu_button = menu_button
