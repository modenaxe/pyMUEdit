from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt

from .CleanTheme import CleanTheme


class DatasetItem(QFrame):
    """A clean list item for displaying dataset information"""

    def __init__(self, filename, metadata, in_sidebar=False, parent=None):
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
        
        # Make the item clickable
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Apply styling
        self.setStyleSheet(
            f"""
            QFrame#datasetItem {{
                background-color: transparent;
                border-bottom: 1px solid {CleanTheme.BORDER};
            }}
            QFrame#datasetItem:hover {{
                background-color: rgba(0, 0, 0, 0.05);
            }}
        """
        )

        # Set up layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Try to load the icon, with error handling
        try:
            icon_path = "public/file_icon.svg"
            file_icon = QSvgWidget(icon_path)
            file_icon.setFixedSize(15, 20)
            layout.addWidget(file_icon)
        except Exception as e:
            # Fallback to standard icon
            icon_label = QLabel("📄")
            icon_label.setFixedSize(15, 20)
            layout.addWidget(icon_label)

        # Add file information
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        filename_label = QLabel(filename) if not in_sidebar else QLabel(self._truncate_text(filename, 15))
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
        if not in_sidebar:
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
            self.menu_button = menu_button

        # Store references to components for later access
        self.filename_label = filename_label
        self.metadata_label = metadata_label
        
        # Store the filename for reference
        self.filename = filename
        
        # Store original mousePressEvent method
        self._original_mouse_press = self.mousePressEvent

    def mousePressEvent(self, event):
        """Handle mouse press events for the dataset item"""
        # Find parent dashboard to handle the click
        parent = self.parent()
        while parent is not None:
            try:
                from app.HDEMGDashboard import HDEMGDashboard
                if isinstance(parent, HDEMGDashboard):
                    # Get the dataset info
                    dataset = {
                        "filename": self.filename,
                        "pathname": self.property("pathname") or "",
                        "metadata": self.metadata_label.text()
                    }
                    
                    # Call dashboard's handler
                    if hasattr(parent, 'open_dataset'):
                        parent.open_dataset(dataset)
                    break
                parent = parent.parent()
            except ImportError:
                # If we can't import HDEMGDashboard (likely due to circular imports)
                # Just go up the parent chain
                parent = parent.parent()
                
        # Call original mousePressEvent if it exists
        if hasattr(self, '_original_mouse_press') and callable(self._original_mouse_press):
            self._original_mouse_press(event)

    def _truncate_text(self, text, max_length):
        """
        Truncate text if it exceeds maximum length and add ellipsis

        Args:
            text (str): Text to truncate
            max_length (int): Maximum length before truncation
        """
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text
