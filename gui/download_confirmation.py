
import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QStyle,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize

# Helper function to get standard icons
def get_icon(standard_icon):
    """Gets a standard Qt icon."""
    return QApplication.style().standardIcon(standard_icon)

class ExportCompleteWindow(QWidget):
    """
    A QWidget window displaying confirmation of a successful export,
    providing a direct download link and showing recent exports.
    """
    def __init__(self, parent=None):
        """
        Initializes the ExportCompleteWindow.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Export Complete")
        self.setMinimumSize(700, 550) # Adjusted minimum size

        # Define color scheme
        self.colors = {
            "bg_main": "#f8f9fa",
            "bg_card": "#ffffff",
            "border": "#e0e0e0",
            "shadow": QColor(0, 0, 0, 30),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_success": "#198754", # Green for success icon/text
            "button_dark_bg": "#212529",
            "button_dark_text": "#ffffff",
            "button_dark_hover": "#343a40",
            "download_row_bg": "#f8f9fa",
            "download_row_border": "#eeeeee",
            "download_btn_hover": "#dee2e6",
            "download_btn_pressed": "#ced4da",
        }

        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30) # Adjust margins
        main_layout.setSpacing(10) # Space between top button and cards

        # --- Top: Return Button ---
        main_layout.addWidget(self._create_return_button(), alignment=Qt.AlignLeft)
        main_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Space below button

        # --- Center: Content Area (Cards) ---
        content_layout = QVBoxLayout() # Layout to hold the two cards
        content_layout.setSpacing(25) # Space between the two cards

        # Card 1: Export Complete Confirmation
        content_layout.addWidget(self._create_confirmation_card())

        # Card 2: Recent Exports
        content_layout.addWidget(self._create_recent_exports_section())

        main_layout.addLayout(content_layout)
        main_layout.addStretch(1) # Push content upwards

    def _create_styled_card(self):
        """Creates a basic styled QFrame card."""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("styledCard")
        card.setStyleSheet(f"""
            #styledCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
            }}
            #styledCard > * {{ /* Basic reset for direct children */
                background-color: transparent;
                border: none;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(self.colors['shadow'])
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25) # Padding inside the card
        card_layout.setSpacing(18)
        return card, card_layout

    def _create_return_button(self):
        """Creates the 'Return to Dashboard' button."""
        return_button = QPushButton(" Return to Dashboard") # Leading space for alignment
        return_button.setIcon(get_icon(QStyle.SP_ArrowLeft))
        return_button.setIconSize(QSize(16, 16))
        return_button.setCursor(Qt.PointingHandCursor)
        return_button.setFont(QFont("Arial", 9))
        # Minimal styling to look like plain text link
        return_button.setStyleSheet(f"""
            QPushButton {{
                color: {self.colors['text_secondary']};
                background-color: transparent;
                border: none;
                text-align: left; /* Align text left */
                padding: 5px 0px; /* Adjust padding */
            }}
            QPushButton:hover {{
                color: {self.colors['text_primary']}; /* Darken text on hover */
                text-decoration: underline;
            }}
        """)
        return_button.clicked.connect(self.handle_return_to_dashboard)
        return return_button

    def _create_confirmation_card(self):
        """Creates the top card showing the 'Export Complete!' message."""
        confirm_card, confirm_layout = self._create_styled_card()
        confirm_layout.setAlignment(Qt.AlignCenter) # Center items vertically

        # Success Icon (Styled QLabel)
        icon_label = QLabel()
        icon_size = 48 # Larger icon size
        pixmap = get_icon(QStyle.SP_DialogApplyButton).pixmap(QSize(icon_size // 2, icon_size // 2)) # Standard check icon

        # Create a circular background using QPixmap drawing (more complex)
        # Or, use a simpler styled QLabel approach:
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.colors['text_success']}; /* Green background */
                color: white; /* Icon color (if using font icon) */
                border-radius: {icon_size // 2}px; /* Makes it circular */
                border: 2px solid {self.colors['bg_card']}; /* Optional: small border */
                padding: 5px; /* Adjust padding around icon */
            }}
        """)
        # Need to ensure the pixmap itself is white or recolored if needed
        # This styling primarily affects the background circle.

        confirm_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        confirm_layout.addSpacerItem(QSpacerItem(10, 5, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Small space

        # Title
        title_label = QLabel("Export Complete!")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;")
        confirm_layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Subtitle
        subtitle_label = QLabel("Your file has been successfully exported and is ready for download")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;")
        subtitle_label.setWordWrap(True) # Allow wrapping
        confirm_layout.addWidget(subtitle_label, alignment=Qt.AlignCenter)

        confirm_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Space before download row

        # Download Row
        confirm_layout.addWidget(self._create_download_row("Export_2025_01_15.csv", "15.2 MB"))

        return confirm_card

    def _create_download_row(self, filename, filesize):
        """Creates the inset row for the main download."""
        download_frame = QFrame()
        download_frame.setObjectName("downloadRow")
        download_frame.setStyleSheet(f"""
            #downloadRow {{
                background-color: {self.colors['download_row_bg']};
                border: 1px solid {self.colors['download_row_border']};
                border-radius: 5px;
                padding: 12px 15px; /* Padding inside the row */
            }}
            #downloadRow > * {{
                background-color: transparent;
                border: none;
            }}
        """)

        row_layout = QHBoxLayout(download_frame)
        row_layout.setContentsMargins(0,0,0,0) # Padding handled by frame
        row_layout.setSpacing(10)

        # File Icon
        icon_label = QLabel()
        icon_pixmap = get_icon(QStyle.SP_FileIcon).pixmap(QSize(18, 18))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(18, 18))
        icon_label.setStyleSheet("margin-top: 2px;")

        # File Info (Name + Size)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0,0,0,0)

        filename_label = QLabel(filename)
        filename_label.setFont(QFont("Arial", 10, QFont.Bold))
        filename_label.setStyleSheet(f"color: {self.colors['text_primary']};")

        filesize_label = QLabel(filesize)
        filesize_label.setFont(QFont("Arial", 9))
        filesize_label.setStyleSheet(f"color: {self.colors['text_secondary']};")

        info_layout.addWidget(filename_label)
        info_layout.addWidget(filesize_label)

        row_layout.addWidget(icon_label)
        row_layout.addLayout(info_layout)
        row_layout.addStretch(1) # Push button to the right

        # Download Button
        download_button = QPushButton("Download")
        download_button.setFont(QFont("Arial", 9, QFont.Bold))
        download_button.setIcon(get_icon(QStyle.SP_ArrowDown)) # Download icon
        download_button.setIconSize(QSize(14, 14))
        download_button.setMinimumHeight(32)
        download_button.setCursor(Qt.PointingHandCursor)
        download_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['button_dark_bg']};
                color: {self.colors['button_dark_text']};
                border: none;
                border-radius: 5px;
                padding: 6px 15px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_dark_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['button_dark_bg']};
            }}
        """)
        # Use lambda to pass filename if needed, or use a member variable
        download_button.clicked.connect(lambda checked=False, fn=filename: self.handle_main_download(fn))
        row_layout.addWidget(download_button)

        return download_frame

    def _create_recent_exports_section(self):
        """Creates the bottom card listing recent exports."""
        recent_card, recent_layout = self._create_styled_card()

        title_label = QLabel("Recent Exports")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; margin-bottom: 5px;") # Less bottom margin
        recent_layout.addWidget(title_label)

        # Add recent export items
        # Sample data - replace with actual data source
        recent_exports_data = [
            {"filename": "Export_2025_01_15.csv", "metadata": "15.2 MB • Exported today"},
            {"filename": "Export_2025_01_14.csv", "metadata": "12.8 MB • Exported yesterday"},
            {"filename": "Export_2025_01_13.csv", "metadata": "14.5 MB • Exported 2 days ago"},
        ]

        for item_data in recent_exports_data:
            recent_layout.addWidget(self._create_recent_export_item(
                item_data["filename"],
                item_data["metadata"]
            ))

        recent_layout.addStretch(1) # Push items up

        return recent_card

    def _create_recent_export_item(self, filename, metadata):
        """Creates a widget representing a single recent export item row."""
        item_widget = QFrame()
        item_widget.setObjectName("recentExportItem")
        # Slightly simpler row styling
        item_widget.setStyleSheet(f"""
            #recentExportItem {{
                background-color: transparent; /* Use card bg */
                border: none;
                border-radius: 4px; /* Optional rounding */
                padding: 8px 0px; /* Vertical padding, no horizontal */
            }}
             #recentExportItem:hover {{
                 background-color: {self.colors['download_row_bg']}; /* Subtle hover */
            }}
            /* Ensure children backgrounds are transparent */
            #recentExportItem > * {{
                 background-color: transparent;
                 border: none;
            }}
        """)

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 0, 5, 0) # Small horizontal margin
        item_layout.setSpacing(12)

        # File Icon
        icon_label = QLabel()
        icon_pixmap = get_icon(QStyle.SP_FileIcon).pixmap(QSize(18, 18))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(18, 18))
        icon_label.setStyleSheet("margin-top: 1px;")

        item_layout.addWidget(icon_label)

        # File Info (Filename and Metadata)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(1)

        filename_label = QLabel(filename)
        filename_label.setFont(QFont("Arial", 10))
        filename_label.setStyleSheet(f"color: {self.colors['text_primary']};")

        metadata_label = QLabel(metadata)
        metadata_label.setFont(QFont("Arial", 9))
        metadata_label.setStyleSheet(f"color: {self.colors['text_secondary']};")

        info_layout.addWidget(filename_label)
        info_layout.addWidget(metadata_label)
        item_layout.addWidget(info_widget, 1) # Allow info section to stretch

        # Download Button (Icon only)
        download_button = QPushButton()
        download_button.setIcon(get_icon(QStyle.SP_ArrowDown))
        download_button.setIconSize(QSize(16, 16))
        download_button.setFixedSize(30, 30)
        download_button.setCursor(Qt.PointingHandCursor)
        download_button.setToolTip(f"Download {filename}")
        download_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['download_btn_hover']};
            }}
             QPushButton:pressed {{
                background-color: {self.colors['download_btn_pressed']};
            }}
        """)
        download_button.clicked.connect(lambda checked=False, fn=filename: self.handle_recent_download(fn))
        item_layout.addWidget(download_button)

        return item_widget

    # --- Placeholder Slots ---

    def handle_return_to_dashboard(self):
        """Placeholder slot for the 'Return to Dashboard' button."""
        print("Returning to Dashboard...")
        # Add logic to close this window and show the dashboard
        # self.parent().show_dashboard() or similar signal/slot mechanism
        self.close()

    def handle_main_download(self, filename):
        """Placeholder slot for the main 'Download' button."""
        print(f"Downloading main exported file: {filename}")
        # Add actual download logic here

    def handle_recent_download(self, filename):
        """Placeholder slot for downloading a file from the recent list."""
        print(f"Downloading recent export: {filename}")
        # Add actual download logic here


# --- Main execution block (for testing the window independently) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle("Fusion") # Optional

    complete_window = ExportCompleteWindow()
    complete_window.show()

    sys.exit(app.exec_())