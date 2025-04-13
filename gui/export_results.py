import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,  # Changed from QMainWindow as it's likely a secondary window
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
from PyQt5.QtCore import Qt, QSize

# Helper function to get standard icons - can be kept here or moved to a utility module
def get_icon(standard_icon):
    """Gets a standard Qt icon."""
    return QApplication.style().standardIcon(standard_icon)

class ExportResultsWindow(QWidget):
    """
    A QWidget window for configuring and viewing data exports.
    Provides options for file format selection and lists recent exports.
    """
    def __init__(self, parent=None):
        """
        Initializes the ExportResultsWindow.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Export Results")
        # Adjust size as needed, or let the layout manage it
        # self.setGeometry(100, 100, 650, 600)
        self.setMinimumWidth(600) # Set a minimum width

        # Define color scheme (simplified for this example)
        self.colors = {
            "bg_main": "#f8f9fa", # Slightly off-white background
            "bg_card": "#ffffff",
            "border": "#e0e0e0",
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "button_dark_bg": "#212529", # Dark button background
            "button_dark_text": "#ffffff", # Dark button text
            "button_dark_hover": "#343a40", # Dark button hover
            "icon_box_bg": "#e9ecef",
            "icon_box_border": "#ced4da",
            "icon_box_text": "#495057",
            "item_row_bg": "#f8f9fa",
            "item_row_hover": "#f1f3f5",
            "download_btn_hover": "#dee2e6",
            "download_btn_pressed": "#ced4da",
            "selected_data_bg": "#fdfdfd",
            "selected_data_border": "#eeeeee",
        }

        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30) # Add padding around the window
        main_layout.setSpacing(25) # Space between main sections

        # --- Header ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        title_label = QLabel("Export Results")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;") # Ensure no border

        subtitle_label = QLabel("Export your motor unit firing patterns data")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;") # Ensure no border

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addLayout(header_layout)

        # --- Export Configuration Section ---
        main_layout.addWidget(self._create_export_config_section())

        # --- Recent Exports Section ---
        main_layout.addWidget(self._create_recent_exports_section())

        # --- Footer ---
        footer_label = QLabel("Last export: January 15, 2025 at 14:30")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setFont(QFont("Arial", 9))
        footer_label.setStyleSheet(f"color: {self.colors['text_secondary']}; margin-top: 10px; border: none;") # Ensure no border
        main_layout.addWidget(footer_label)

        main_layout.addStretch(1) # Push content upwards


    def _create_styled_card(self):
        """Creates a basic styled QFrame card."""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel) # Use StyledPanel for the border effect from stylesheet
        card.setObjectName("cardFrame") # Set object name for specific styling
        card.setStyleSheet(f"""
            #cardFrame {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
            }}
            /* Prevent style inheritance to direct children unless specifically targeted */
            #cardFrame > QWidget, #cardFrame > QLayout::item {{
                background-color: transparent;
                border: none;
            }}
        """)
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect(self) # Parent shadow to card
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30)) # Black shadow with low opacity
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20) # Padding inside the card
        card_layout.setSpacing(15) # Spacing between elements inside the card
        return card, card_layout

    def _create_export_config_section(self):
        """Creates the top section for export configuration."""
        config_card, config_layout = self._create_styled_card()

        # Select File Format
        format_label = QLabel("Select File Format")
        format_label.setFont(QFont("Arial", 10))
        format_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")
        config_layout.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.setFont(QFont("Arial", 10))
        # Add placeholder or actual formats
        self.format_combo.addItem("Select format...") # Placeholder item
        self.format_combo.addItem(".csv (Comma Separated Values)")
        self.format_combo.addItem(".mat (MATLAB Data File)")
        self.format_combo.addItem(".xlsx (Excel Spreadsheet)")
        self.format_combo.setMinimumHeight(35)
        self.format_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 5px 10px;
                background-color: {self.colors['bg_card']}; /* Match card bg */
                color: {self.colors['text_primary']};
                min-height: 25px; /* Ensure height consistency */
            }}
            QComboBox:focus {{
                 border: 1px solid {self.colors['button_dark_bg']}; /* Highlight on focus */
            }}
            QComboBox::drop-down {{
                /* Styling the dropdown button */
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {self.colors['border']};
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: transparent;
            }}
            QComboBox::down-arrow {{
                /* Using a standard icon for the arrow */
                 image: url(:/qt-project.org/styles/commonstyle/images/down_arrow-16.png);
                 width: 12px;
                 height: 12px;
            }}
             QComboBox QAbstractItemView {{ /* Style the dropdown list items */
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['bg_card']};
                selection-background-color: {self.colors['button_dark_hover']};
                selection-color: {self.colors['button_dark_text']};
                color: {self.colors['text_primary']};
                padding: 2px;
            }}
        """)
        # Apply delegate for potentially better cross-platform styling consistency
        # self.format_combo.setItemDelegate(QStyledItemDelegate(self.format_combo))

        config_layout.addWidget(self.format_combo)

        # Spacer
        config_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Selected Data Details Area
        selected_data_frame = QFrame()
        selected_data_frame.setObjectName("selectedDataFrame")
        selected_data_frame.setStyleSheet(f"""
            #selectedDataFrame {{
                background-color: {self.colors['selected_data_bg']};
                border: 1px solid {self.colors['selected_data_border']};
                border-radius: 5px;
                padding: 15px;
            }}
            #selectedDataFrame > QLabel, #selectedDataFrame > QLayout::item {{
                background-color: transparent;
                border: none;
            }}
        """)
        selected_data_layout = QVBoxLayout(selected_data_frame)
        selected_data_layout.setContentsMargins(10, 10, 10, 10)
        selected_data_layout.setSpacing(10)

        data_title_label = QLabel("Selected Data")
        data_title_label.setFont(QFont("Arial", 10, QFont.Bold))
        data_title_label.setStyleSheet(f"color: {self.colors['text_primary']}; margin-bottom: 5px; background: transparent; border: none;")
        selected_data_layout.addWidget(data_title_label)

        # Add data detail rows using helper
        selected_data_layout.addLayout(self._create_data_detail_row(
            QStyle.SP_FileIcon, # Standard icon for document/file
            "Motor Unit Firing Patterns"
        ))
        selected_data_layout.addLayout(self._create_data_detail_row(
            QStyle.SP_MediaSeekForward, # Standard icon suggesting time/duration
            "Recording Duration: 120s"
        ))
        selected_data_layout.addLayout(self._create_data_detail_row(
            QStyle.SP_ComputerIcon, # Standard icon for system/units
            "Units Detected: 12"
        ))

        config_layout.addWidget(selected_data_frame)

        # Spacer
        config_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Export Button
        export_button = QPushButton("Export Data")
        export_button.setFont(QFont("Arial", 10, QFont.Bold))
        export_button.setIcon(get_icon(QStyle.SP_DialogSaveButton)) # Save/Export icon
        # export_button.setIcon(get_icon(QStyle.SP_ArrowDown)) # Alternative: Download icon
        export_button.setIconSize(QSize(16, 16))
        export_button.setMinimumHeight(40)
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['button_dark_bg']};
                color: {self.colors['button_dark_text']};
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_dark_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['button_dark_bg']};
            }}
        """)
        export_button.clicked.connect(self.handle_export) # Connect to export function placeholder
        config_layout.addWidget(export_button)

        return config_card

    def _create_data_detail_row(self, icon_enum, text):
        """Helper to create a row with an icon and text for the details section."""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        row_layout.setContentsMargins(0,0,0,0) # No extra margins for the row itself

        icon_label = QLabel()
        icon_pixmap = get_icon(icon_enum).pixmap(QSize(16, 16))
        # Optional: Color the icon - requires QPainter or SVG manipulation
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(16, 16))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("margin-top: 2px; background: transparent; border: none;") # Align icon slightly better

        text_label = QLabel(text)
        text_label.setFont(QFont("Arial", 10))
        text_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")

        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_label)
        row_layout.addStretch(1) # Push content to the left

        return row_layout

    def _create_recent_exports_section(self):
        """Creates the bottom section listing recent exports."""
        recent_card, recent_layout = self._create_styled_card()

        title_label = QLabel("Recent Exports")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; margin-bottom: 10px; background: transparent; border: none;")
        recent_layout.addWidget(title_label)

        # Add recent export items using helper
        recent_layout.addWidget(self._create_recent_export_item(
            "csv", # Icon type hint
            "firing_patterns_2025.01.15.csv",
            "2.4 MB • Completed"
        ))
        recent_layout.addWidget(self._create_recent_export_item(
            "mat", # Icon type hint
            "firing_patterns_2025.01.14.mat",
            "3.1 MB • Completed"
        ))
        # Add more items here if needed:
        # recent_layout.addWidget(self._create_recent_export_item(
        #     "xlsx",
        #     "analysis_summary_2025.01.10.xlsx",
        #     "0.8 MB • Completed"
        # ))

        recent_layout.addStretch(1) # Push items to the top if the card is taller

        return recent_card

    def _create_recent_export_item(self, icon_type, filename, metadata):
        """Creates a widget representing a single recent export item."""
        item_widget = QFrame()
        item_widget.setObjectName("recentItem")
        item_widget.setCursor(Qt.PointingHandCursor) # Indicate the row is interactive (optional)
        item_widget.setStyleSheet(f"""
            #recentItem {{
                background-color: {self.colors['item_row_bg']};
                border: 1px solid {self.colors['item_row_bg']}; /* Use bg color for seamless look */
                border-radius: 4px;
                padding: 10px 15px; /* Padding within the item row */
            }}
            #recentItem:hover {{
                 background-color: {self.colors['item_row_hover']}; /* Lighter hover */
                 border: 1px solid {self.colors['border']}; /* Show border on hover */
            }}
            /* Ensure children don't inherit the background inappropriately */
             #recentItem > QLabel, #recentItem > QLayoutWidget {{
                 background-color: transparent;
                 border: none;
             }}
        """)
        # Add a tooltip to the whole item
        item_widget.setToolTip(f"Click to interact with {filename}")

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0) # Margins handled by padding in stylesheet
        item_layout.setSpacing(12)

        # File Type Icon
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24) # Icon size
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Arial", 7, QFont.Bold)) # Smaller font for text icon
        icon_label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {self.colors['icon_box_border']};
                border-radius: 4px;
                background-color: {self.colors['icon_box_bg']};
                color: {self.colors['icon_box_text']};
            }}
        """)
        if icon_type.lower() == "csv":
            icon_label.setText("CSV")
        elif icon_type.lower() == "mat":
             icon_label.setText("MAT")
        elif icon_type.lower() == "xlsx":
             icon_label.setText("XLSX")
        else:
             # Fallback to a generic document icon
             icon_label.setPixmap(get_icon(QStyle.SP_FileIcon).pixmap(QSize(18,18)))
             icon_label.setText("") # Clear text if using pixmap
             icon_label.setStyleSheet("border: none; background: transparent;") # Remove box style for pixmap

        item_layout.addWidget(icon_label)

        # File Info (Filename and Metadata) - Use a layout container
        info_widget = QWidget() # Container prevents stretch issues
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(2)

        filename_label = QLabel(filename)
        filename_label.setFont(QFont("Arial", 10, QFont.Normal))
        filename_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent; border: none;")
        filename_label.setToolTip(filename) # Show full name if truncated

        metadata_label = QLabel(metadata)
        metadata_label.setFont(QFont("Arial", 9))
        metadata_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")

        info_layout.addWidget(filename_label)
        info_layout.addWidget(metadata_label)
        item_layout.addWidget(info_widget) # Add the container widget

        item_layout.addStretch(1) # Push download button to the right

        # Download Button
        download_button = QPushButton()
        download_button.setIcon(get_icon(QStyle.SP_ArrowDown))
        download_button.setIconSize(QSize(18, 18))
        download_button.setFixedSize(32, 32) # Make it square-ish and slightly larger
        download_button.setCursor(Qt.PointingHandCursor)
        download_button.setToolTip(f"Download {filename}")
        download_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px; /* Rounded corners on hover */
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['download_btn_hover']};
            }}
             QPushButton:pressed {{
                background-color: {self.colors['download_btn_pressed']};
            }}
        """)
        # Use lambda to pass the filename to the handler
        download_button.clicked.connect(lambda checked=False, fn=filename: self.handle_download(fn))
        item_layout.addWidget(download_button)

        return item_widget

    # --- Placeholder Slots for Button Clicks ---

    def handle_export(self):
        """Placeholder slot for the 'Export Data' button click."""
        selected_index = self.format_combo.currentIndex()
        selected_format_text = self.format_combo.currentText()

        if selected_index == 0: # Check if the placeholder "Select format..." is selected
             print("Please select a file format.")
             # Optionally show a message box to the user
             # from PyQt5.QtWidgets import QMessageBox
             # QMessageBox.warning(self, "No Format Selected", "Please select a file format before exporting.")
             return

        print(f"Exporting data in format: {selected_format_text}")
        # ----> Add your actual data export logic here <----
        # Example: export_data_function(format=selected_format_text.split(' ')[0])
        print("Export process initiated (placeholder).")


    def handle_download(self, filename):
        """Placeholder slot for the download button click on a recent export item."""
        print(f"Downloading file: {filename}")
        # ----> Add your actual file download/retrieval logic here <----
        # Example: download_file(filename)
        print(f"Download requested for {filename} (placeholder).")


# --- Main execution block (for testing the window independently) ---
if __name__ == "__main__":
    # Create application instance
    app = QApplication(sys.argv)

    # Set a style that might provide better standard icons/widgets
    # Available styles depend on the OS and PyQt installation
    # Common options: "Fusion", "Windows", "WindowsVista" (Windows), "macOS" (Mac)
    # app.setStyle("Fusion")

    # Create and show the window
    export_window = ExportResultsWindow()
    export_window.show()

    # Start the application event loop
    sys.exit(app.exec_())