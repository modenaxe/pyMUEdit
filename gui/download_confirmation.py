import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSpacerItem,
    QSizePolicy, QStyle, QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal # Import pyqtSignal

# Helper function to get standard icons
def get_icon(standard_icon):
    """Gets a standard Qt icon."""
    return QApplication.style().standardIcon(standard_icon)

# Renamed from ExportCompleteWindow
class ExportCompleteWidget(QWidget):
    """
    A QWidget displaying confirmation of a successful export,
    providing a direct download link and showing recent exports.
    """
    # Signals
    return_requested = pyqtSignal()
    download_requested = pyqtSignal(str) # Emits filename to download
    recent_download_requested = pyqtSignal(str) # Emits filename from recent list

    def __init__(self, parent=None):
        """
        Initializes the ExportCompleteWidget.
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # Removed: setWindowTitle, setMinimumSize, top-level stylesheet

        # Define color scheme (can be inherited or defined here)
        self.colors = {
            "bg_main": "#f8f9fa", # Likely overridden by container
            "bg_card": "#ffffff",
            "border": "#e0e0e0",
            "shadow": QColor(0, 0, 0, 30),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_success": "#198754",
            "button_dark_bg": "#212529",
            "button_dark_text": "#ffffff",
            "button_dark_hover": "#343a40",
            "download_row_bg": "#f8f9fa",
            "download_row_border": "#eeeeee",
            "download_btn_hover": "#dee2e6",
            "download_btn_pressed": "#ced4da",
        }

        # --- Main Layout for THIS widget ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) # Add some margin
        main_layout.setSpacing(10)

        # --- Top: Return Button ---
        main_layout.addWidget(self._create_return_button(), alignment=Qt.AlignLeft)
        main_layout.addSpacerItem(QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Reduced space

        # --- Center: Content Area (Cards) ---
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20) # Reduced space between cards
        content_layout.addWidget(self._create_confirmation_card())
        content_layout.addWidget(self._create_recent_exports_section())
        main_layout.addLayout(content_layout)
        main_layout.addStretch(1)

        # Store filename/size labels to update them
        self._download_filename_label = None
        self._download_filesize_label = None
        self._main_download_filename = None # Store filename for download button

    def _create_styled_card(self):
        card = QFrame(); card.setFrameShape(QFrame.StyledPanel); card.setObjectName("styledCardComplete") # Unique name
        card.setStyleSheet(f""" #styledCardComplete {{ background-color: {self.colors['bg_card']}; border: 1px solid {self.colors['border']}; border-radius: 8px; }} #styledCardComplete > * {{ background-color: transparent; border: none; }} """)
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(15); shadow.setColor(self.colors['shadow']); shadow.setOffset(0, 2); card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(20, 20, 20, 20); card_layout.setSpacing(15) # Reduced padding/spacing
        return card, card_layout

    def _create_return_button(self):
        return_button = QPushButton(" Return to Export Setup"); return_button.setIcon(get_icon(QStyle.SP_ArrowLeft)); return_button.setIconSize(QSize(16, 16)); return_button.setCursor(Qt.PointingHandCursor); return_button.setFont(QFont("Arial", 9))
        return_button.setStyleSheet(f""" QPushButton {{ color: {self.colors['text_secondary']}; background-color: transparent; border: none; text-align: left; padding: 5px 0px; }} QPushButton:hover {{ color: {self.colors['text_primary']}; text-decoration: underline; }} """)
        return_button.clicked.connect(self.handle_return) # Connect to internal handler
        return return_button

    def _create_confirmation_card(self):
        confirm_card, confirm_layout = self._create_styled_card(); confirm_layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel(); icon_size = 40 # Smaller icon
        pixmap = get_icon(QStyle.SP_DialogApplyButton).pixmap(QSize(icon_size // 2, icon_size // 2)); icon_label.setPixmap(pixmap); icon_label.setFixedSize(icon_size, icon_size); icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f""" QLabel {{ background-color: {self.colors['text_success']}; border-radius: {icon_size // 2}px; border: 2px solid {self.colors['bg_card']}; padding: 5px; }} """)
        confirm_layout.addWidget(icon_label, alignment=Qt.AlignCenter); confirm_layout.addSpacerItem(QSpacerItem(10, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))
        title_label = QLabel("Export Complete!"); title_label.setFont(QFont("Arial", 16, QFont.Bold)); title_label.setAlignment(Qt.AlignCenter); title_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;"); confirm_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        subtitle_label = QLabel("Your file has been successfully exported."); subtitle_label.setFont(QFont("Arial", 10)); subtitle_label.setAlignment(Qt.AlignCenter); subtitle_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;"); subtitle_label.setWordWrap(True); confirm_layout.addWidget(subtitle_label, alignment=Qt.AlignCenter)
        confirm_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Reduced space
        confirm_layout.addWidget(self._create_download_row("Initializing...", "...")) # Placeholder text
        return confirm_card

    def _create_download_row(self, filename, filesize):
        download_frame = QFrame(); download_frame.setObjectName("downloadRowComplete") # Unique name
        download_frame.setStyleSheet(f""" #downloadRowComplete {{ background-color: {self.colors['download_row_bg']}; border: 1px solid {self.colors['download_row_border']}; border-radius: 5px; padding: 10px 12px; }} #downloadRowComplete > * {{ background-color: transparent; border: none; }} """)
        row_layout = QHBoxLayout(download_frame); row_layout.setContentsMargins(0,0,0,0); row_layout.setSpacing(10)
        icon_label = QLabel(); icon_pixmap = get_icon(QStyle.SP_FileIcon).pixmap(QSize(18, 18)); icon_label.setPixmap(icon_pixmap); icon_label.setFixedSize(QSize(18, 18)); icon_label.setStyleSheet("margin-top: 2px;")
        info_layout = QVBoxLayout(); info_layout.setSpacing(1); info_layout.setContentsMargins(0,0,0,0)
        # Store references to labels
        self._download_filename_label = QLabel(filename); self._download_filename_label.setFont(QFont("Arial", 10, QFont.Bold)); self._download_filename_label.setStyleSheet(f"color: {self.colors['text_primary']};")
        self._download_filesize_label = QLabel(filesize); self._download_filesize_label.setFont(QFont("Arial", 9)); self._download_filesize_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
        info_layout.addWidget(self._download_filename_label); info_layout.addWidget(self._download_filesize_label)
        row_layout.addWidget(icon_label); row_layout.addLayout(info_layout); row_layout.addStretch(1)
        download_button = QPushButton("Download"); download_button.setFont(QFont("Arial", 9, QFont.Bold)); download_button.setIcon(get_icon(QStyle.SP_ArrowDown)); download_button.setIconSize(QSize(14, 14)); download_button.setMinimumHeight(30); download_button.setCursor(Qt.PointingHandCursor)
        download_button.setStyleSheet(f""" QPushButton {{ background-color: {self.colors['button_dark_bg']}; color: {self.colors['button_dark_text']}; border: none; border-radius: 5px; padding: 6px 15px; }} QPushButton:hover {{ background-color: {self.colors['button_dark_hover']}; }} QPushButton:pressed {{ background-color: {self.colors['button_dark_bg']}; }} """)
        download_button.clicked.connect(self.handle_main_download) # Connect to internal handler
        row_layout.addWidget(download_button)
        return download_frame

    def _create_recent_exports_section(self):
        recent_card, recent_layout = self._create_styled_card()
        title_label = QLabel("Recent Exports"); title_label.setFont(QFont("Arial", 14, QFont.Bold)); title_label.setStyleSheet(f"color: {self.colors['text_primary']}; margin-bottom: 5px;"); recent_layout.addWidget(title_label)
        recent_exports_data = [ {"filename": "Export_2025_01_15.csv", "metadata": "15.2 MB • Exported today"}, {"filename": "Export_2025_01_14.csv", "metadata": "12.8 MB • Exported yesterday"}, {"filename": "Export_2025_01_13.csv", "metadata": "14.5 MB • Exported 2 days ago"}, ]
        for item_data in recent_exports_data: recent_layout.addWidget(self._create_recent_export_item(item_data["filename"], item_data["metadata"]))
        recent_layout.addStretch(1)
        return recent_card

    def _create_recent_export_item(self, filename, metadata):
        item_widget = QFrame(); item_widget.setObjectName("recentExportItemComplete") # Unique name
        item_widget.setStyleSheet(f""" #recentExportItemComplete {{ background-color: transparent; border: none; border-radius: 4px; padding: 6px 0px; }} #recentExportItemComplete:hover {{ background-color: {self.colors['download_row_bg']}; }} #recentExportItemComplete > * {{ background-color: transparent; border: none; }} """)
        item_layout = QHBoxLayout(item_widget); item_layout.setContentsMargins(5, 0, 5, 0); item_layout.setSpacing(12)
        icon_label = QLabel(); icon_pixmap = get_icon(QStyle.SP_FileIcon).pixmap(QSize(18, 18)); icon_label.setPixmap(icon_pixmap); icon_label.setFixedSize(QSize(18, 18)); icon_label.setStyleSheet("margin-top: 1px;")
        item_layout.addWidget(icon_label)
        info_widget = QWidget(); info_layout = QVBoxLayout(info_widget); info_layout.setContentsMargins(0,0,0,0); info_layout.setSpacing(1)
        filename_label = QLabel(filename); filename_label.setFont(QFont("Arial", 10)); filename_label.setStyleSheet(f"color: {self.colors['text_primary']};")
        metadata_label = QLabel(metadata); metadata_label.setFont(QFont("Arial", 9)); metadata_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
        info_layout.addWidget(filename_label); info_layout.addWidget(metadata_label); item_layout.addWidget(info_widget, 1)
        download_button = QPushButton(); download_button.setIcon(get_icon(QStyle.SP_ArrowDown)); download_button.setIconSize(QSize(16, 16)); download_button.setFixedSize(30, 30); download_button.setCursor(Qt.PointingHandCursor); download_button.setToolTip(f"Download {filename}")
        download_button.setStyleSheet(f""" QPushButton {{ background-color: transparent; border: none; border-radius: 4px; padding: 0px; }} QPushButton:hover {{ background-color: {self.colors['download_btn_hover']}; }} QPushButton:pressed {{ background-color: {self.colors['download_btn_pressed']}; }} """)
        download_button.clicked.connect(lambda checked=False, fn=filename: self.handle_recent_download(fn)) # Connect to internal handler
        item_layout.addWidget(download_button)
        return item_widget

    def set_export_details(self, filename, filesize_bytes):
        """Updates the main download row details."""
        self._main_download_filename = filename # Store for download button signal
        if self._download_filename_label:
            self._download_filename_label.setText(os.path.basename(filename)) # Show only filename
        if self._download_filesize_label:
            # Convert bytes to human-readable format
            if filesize_bytes < 1024:
                size_str = f"{filesize_bytes} B"
            elif filesize_bytes < 1024**2:
                size_str = f"{filesize_bytes/1024:.1f} KB"
            elif filesize_bytes < 1024**3:
                size_str = f"{filesize_bytes/1024**2:.1f} MB"
            else:
                size_str = f"{filesize_bytes/1024**3:.1f} GB"
            self._download_filesize_label.setText(size_str)

    # --- Internal Handlers Emitting Signals ---
    def handle_return(self):
        """Emits signal to return to previous view or dashboard."""
        print("Complete Widget: Emitting return_requested")
        self.return_requested.emit()

    def handle_main_download(self):
        """Emits signal to download the file that was just exported."""
        if self._main_download_filename:
            print(f"Complete Widget: Emitting download_requested for {self._main_download_filename}")
            self.download_requested.emit(self._main_download_filename)
        else:
            print("Complete Widget: Error - Main download filename not set.")

    def handle_recent_download(self, filename):
        """Emits signal to download a file from the recent list."""
        print(f"Complete Widget: Emitting recent_download_requested for {filename}")
        self.recent_download_requested.emit(filename)


# --- Main execution block (for testing the widget independently) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_win = QWidget()
    test_win.setWindowTitle("Test ExportCompleteWidget")
    layout = QVBoxLayout(test_win)
    complete_widget = ExportCompleteWidget()
    # Simulate setting details
    complete_widget.set_export_details("/path/to/some/Export_File_Name_123.csv", 15200 * 1024) # Example 15.2 MB
    layout.addWidget(complete_widget)
    test_win.setStyleSheet("background-color: #e0e0e0;")
    test_win.resize(700, 550)

    # Example connecting signals
    complete_widget.return_requested.connect(lambda: print("TEST: Return Requested!"))
    complete_widget.download_requested.connect(lambda fn: print(f"TEST: Main Download Requested: {fn}"))
    complete_widget.recent_download_requested.connect(lambda fn: print(f"TEST: Recent Download Requested: {fn}"))

    test_win.show()
    sys.exit(app.exec_())