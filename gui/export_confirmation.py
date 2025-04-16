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
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QStyle,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal # Import pyqtSignal

# Helper function to get standard icons
def get_icon(standard_icon):
    """Gets a standard Qt icon."""
    return QApplication.style().standardIcon(standard_icon)

# Renamed from ExportFileWindow
class ExportConfirmWidget(QWidget):
    """
    A QWidget containing the export confirmation elements.
    Designed to be placed inside another window or layout.
    """
    # Signals to communicate back to the parent window
    export_confirmed = pyqtSignal(str, str) # Emits format and filename
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initializes the ExportConfirmWidget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # Removed: setWindowTitle, setMinimumSize, outer layouts, top-level stylesheet

        # Define color scheme (can be inherited or redefined)
        self.colors = {
            "bg_main": "#f8f9fa", # Will likely be overridden by container
            "bg_card": "#ffffff",
            "border": "#dee2e6",
            "shadow": QColor(0, 0, 0, 30),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_list_item": "#495057",
            "button_dark_bg": "#212529",
            "button_dark_text": "#ffffff",
            "button_dark_hover": "#343a40",
            "button_light_bg": "#ffffff",
            "button_light_text": "#495057",
            "button_light_border": "#ced4da",
            "button_light_hover_bg": "#f8f9fa",
            "details_frame_bg": "#f8f9fa",
            "details_frame_border": "#e9ecef",
        }

        # --- Main Layout for THIS widget ---
        # Contains only the central card now
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins, card handles padding

        # --- Main Content Card ---
        self.main_card = self._create_main_card()
        main_layout.addWidget(self.main_card)

        # Removed footer, belongs to the main container window if needed

    def _create_main_card(self):
        """Creates the central white card container."""
        card = QFrame()
        card.setObjectName("mainConfirmCard") # Unique name
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            #mainConfirmCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
                padding: 25px;
                /* Min/Max width can help control size within stacked widget */
                min-width: 480px;
                max-width: 520px;
            }}
            #mainConfirmCard > QWidget, #mainConfirmCard > QLayout::item {{
                background-color: transparent;
                border: none;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20); shadow.setColor(self.colors['shadow']); shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(20)
        card_layout.addLayout(self._create_header())
        card_layout.addLayout(self._create_format_selection())
        card_layout.addWidget(self._create_file_details())
        card_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Expanding))
        card_layout.addLayout(self._create_action_buttons())
        return card

    def _create_header(self):
        """Creates the header layout with title and subtitle."""
        header_layout = QVBoxLayout(); header_layout.setSpacing(4)
        title_label = QLabel("Confirm Export"); title_label.setFont(QFont("Arial", 16, QFont.Bold)); title_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;")
        subtitle_label = QLabel("Review the details before exporting."); subtitle_label.setFont(QFont("Arial", 10)); subtitle_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;")
        header_layout.addWidget(title_label); header_layout.addWidget(subtitle_label)
        return header_layout

    def _create_format_selection(self):
        """Creates the file format selection layout."""
        format_layout = QVBoxLayout(); format_layout.setSpacing(5)
        format_label = QLabel("Selected File Format"); format_label.setFont(QFont("Arial", 9)); format_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;")
        # Use a QLabel here instead of QComboBox, as the format is already chosen
        self.format_display_label = QLabel("CSV (Comma Separated Values)") # Placeholder
        self.format_display_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.format_display_label.setMinimumHeight(38)
        self.format_display_label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 8px 12px;
                background-color: #e9ecef; /* Indicate it's read-only */
                color: {self.colors['text_primary']};
            }}
        """)
        format_layout.addWidget(format_label); format_layout.addWidget(self.format_display_label)
        return format_layout

    def _create_file_details(self):
        """Creates the inset frame showing export filename and contents."""
        details_frame = QFrame(); details_frame.setObjectName("detailsFrameConfirm") # Unique name
        details_frame.setStyleSheet(f"""
            #detailsFrameConfirm {{
                background-color: {self.colors['details_frame_bg']};
                border: 1px solid {self.colors['details_frame_border']};
                border-radius: 5px; padding: 15px;
            }}
            #detailsFrameConfirm > QLabel {{ background-color: transparent; border: none; }}
        """)
        details_layout = QVBoxLayout(details_frame); details_layout.setContentsMargins(0, 0, 0, 0); details_layout.setSpacing(12)
        filename_layout = QHBoxLayout(); filename_layout.setSpacing(8)
        icon_label = QLabel(); icon_pixmap = get_icon(QStyle.SP_FileIcon).pixmap(QSize(18, 18)); icon_label.setPixmap(icon_pixmap); icon_label.setFixedSize(QSize(18, 18)); icon_label.setStyleSheet("margin-top: 1px; border: none;")
        self.filename_label = QLabel("motor_unit_patterns_2025.csv"); self.filename_label.setFont(QFont("Arial", 10, QFont.Bold)); self.filename_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;")
        filename_layout.addWidget(icon_label); filename_layout.addWidget(self.filename_label); filename_layout.addStretch(1)
        details_layout.addLayout(filename_layout)
        include_label = QLabel("File will include:"); include_label.setFont(QFont("Arial", 9)); include_label.setStyleSheet(f"color: {self.colors['text_secondary']}; margin-top: 5px; border: none;")
        details_layout.addWidget(include_label)
        list_layout = QVBoxLayout(); list_layout.setSpacing(4); list_layout.setContentsMargins(10, 0, 0, 0)
        items_to_include = ["Motor unit firing timestamps", "Pattern analysis data", "Recording metadata"]
        self.include_item_labels = []
        for item_text in items_to_include:
            item_label = QLabel(f"• {item_text}"); item_label.setFont(QFont("Arial", 9)); item_label.setStyleSheet(f"color: {self.colors['text_list_item']}; border: none;")
            list_layout.addWidget(item_label); self.include_item_labels.append(item_label)
        details_layout.addLayout(list_layout); details_layout.addStretch(1)
        return details_frame
    
    def _create_action_buttons(self):
        """Creates the layout for the Export and Cancel buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)
        button_layout.setContentsMargins(0, 20, 0, 0)

        # Confirm and Export button (Primary)
        export_button = QPushButton("✔ Confirm and Export")
        export_button.setFont(QFont("Segoe UI", 10))
        export_button.setIconSize(QSize(20, 20))
        export_button.setMinimumHeight(42)
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #1d3557;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #457b9d;
            }
            QPushButton:pressed {
                background-color: #1d3557;
            }
        """)
        export_button.clicked.connect(self.handle_export)

        # Cancel / Back button (Secondary)
        cancel_button = QPushButton("🡸 Back")
        cancel_button.setFont(QFont("Segoe UI", 10))
        cancel_button.setMinimumHeight(42)
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #1d3557;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #457b9d;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #1d3557;
            }
        """)
        cancel_button.clicked.connect(self.handle_cancel)

        # Add spacing and align
        button_layout.addStretch(1)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(export_button)
        return button_layout
    
    def set_export_details(self, selected_format_text, filename):
        """Sets the display labels based on details from the previous screen."""
        self.format_display_label.setText(selected_format_text)
        self.filename_label.setText(filename)
        # You could potentially update the "included items" list here too if needed

    # --- Internal Handlers that Emit Signals ---
    def handle_export(self):
        """Emits the export_confirmed signal."""
        selected_format = self.format_display_label.text() # Get format from label
        filename = self.filename_label.text()
        print(f"Confirmation Widget: Emitting export_confirmed for '{filename}', format '{selected_format}'")
        self.export_confirmed.emit(selected_format, filename)

    def handle_cancel(self):
        """Emits the cancel_requested signal."""
        print("Confirmation Widget: Emitting cancel_requested")
        self.cancel_requested.emit()

# --- Main execution block (for testing the widget independently) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Test container window
    test_win = QWidget()
    test_win.setWindowTitle("Test ExportConfirmWidget")
    layout = QVBoxLayout(test_win)
    confirm_widget = ExportConfirmWidget()
    confirm_widget.set_export_details("CSV (Test Format)", "test_file_2025.csv") # Example call
    layout.addWidget(confirm_widget)
    test_win.setStyleSheet("background-color: #e0e0e0;") # Give test window a background
    test_win.resize(600, 500)

    # Example connecting signals for testing
    confirm_widget.export_confirmed.connect(lambda fmt, fn: print(f"TEST: Export Confirmed! Format: {fmt}, Filename: {fn}"))
    confirm_widget.cancel_requested.connect(lambda: print("TEST: Cancel Requested!"))

    test_win.show()
    sys.exit(app.exec_())