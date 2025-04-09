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
from PyQt5.QtCore import Qt, QSize

# Helper function to get standard icons
def get_icon(standard_icon):
    """Gets a standard Qt icon."""
    return QApplication.style().standardIcon(standard_icon)

class ExportFileWindow(QWidget):
    """
    A QWidget window for confirming export details and initiating a file export.
    Allows format selection and shows what data will be included.
    """
    def __init__(self, parent=None):
        """
        Initializes the ExportFileWindow.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Export File Confirmation") # More specific title
        # Set a fixed size or minimum size based on the design
        self.setMinimumSize(550, 400) # Adjusted size
        # self.setFixedSize(550, 400) # Optionally fix the size

        # Define color scheme
        self.colors = {
            "bg_main": "#f8f9fa",
            "bg_card": "#ffffff",
            "border": "#dee2e6", # Slightly darker border
            "shadow": QColor(0, 0, 0, 30),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_list_item": "#495057", # Slightly darker secondary
            "button_dark_bg": "#212529",
            "button_dark_text": "#ffffff",
            "button_dark_hover": "#343a40",
            "button_light_bg": "#ffffff",
            "button_light_text": "#495057",
            "button_light_border": "#ced4da",
            "button_light_hover_bg": "#f8f9fa",
            "details_frame_bg": "#f8f9fa", # Light background for inset
            "details_frame_border": "#e9ecef",
        }

        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

        # --- Main Layout ---
        # This layout centers the card vertically and horizontally
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.addStretch(1) # Push card to center horizontally

        # Vertical layout to hold the card and footer, allows centering the card
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addStretch(1) # Push card down

        # --- Main Content Card ---
        self.main_card = self._create_main_card()
        center_layout.addWidget(self.main_card)

        center_layout.addStretch(1) # Push footer down / center card vertically

        outer_layout.addLayout(center_layout)
        outer_layout.addStretch(1) # Push card to center horizontally


        # --- Footer (Outside the card) ---
        footer_label = QLabel("© 2025 Motor Unit Analysis System. All rights reserved.")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setFont(QFont("Arial", 8))
        footer_label.setStyleSheet(f"color: {self.colors['text_secondary']}; padding-top: 15px; border: none;")
        # Add footer to the outer layout if needed, or keep it separate if window is fixed size
        # For centering, it's better inside the center_layout but after the card stretch
        center_layout.addWidget(footer_label, 0, Qt.AlignCenter) # Add after bottom stretch


    def _create_main_card(self):
        """Creates the central white card container."""
        card = QFrame()
        card.setObjectName("mainCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            #mainCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
                padding: 25px; /* Generous padding inside the card */
            }}
            /* Prevent style inheritance */
            #mainCard > QWidget, #mainCard > QLayout::item {{
                background-color: transparent;
                border: none;
            }}
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(self.colors['shadow'])
        shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)

        # Layout for card content
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0) # Padding is handled by the card's stylesheet
        card_layout.setSpacing(20) # Space between elements inside the card

        # Add sections to card layout
        card_layout.addLayout(self._create_header())
        card_layout.addLayout(self._create_format_selection())
        card_layout.addWidget(self._create_file_details())
        card_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Pushes buttons down
        card_layout.addLayout(self._create_action_buttons())

        return card

    def _create_header(self):
        """Creates the header layout with title and subtitle."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title_label = QLabel("Export Results")
        title_label.setFont(QFont("Arial", 16, QFont.Bold)) # Slightly smaller than previous example
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;")

        subtitle_label = QLabel("Export motor unit firing patterns to your preferred format")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        return header_layout

    def _create_format_selection(self):
        """Creates the file format selection layout."""
        format_layout = QVBoxLayout()
        format_layout.setSpacing(5)

        format_label = QLabel("Select File Format")
        format_label.setFont(QFont("Arial", 9))
        format_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;")

        self.format_combo = QComboBox()
        self.format_combo.setFont(QFont("Arial", 10))
        # Add formats - set CSV as the default shown
        self.format_combo.addItem("CSV (Comma Separated Values)")
        self.format_combo.addItem("MAT (MATLAB Data File)")
        self.format_combo.addItem("XLSX (Excel Spreadsheet)")
        self.format_combo.setMinimumHeight(38) # Taller combo box
        self.format_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 8px 12px; /* Adjusted padding */
                background-color: {self.colors['bg_card']};
                color: {self.colors['text_primary']};
            }}
            QComboBox:focus {{
                 border: 1px solid {self.colors['button_dark_bg']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px; /* Wider dropdown */
                border-left-width: 1px;
                border-left-color: {self.colors['border']};
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: transparent;
            }}
            QComboBox::down-arrow {{
                 image: url(:/qt-project.org/styles/commonstyle/images/down_arrow-16.png);
                 width: 12px;
                 height: 12px;
                 margin-right: 5px; /* Adjust arrow position */
            }}
             QComboBox QAbstractItemView {{
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['bg_card']};
                selection-background-color: {self.colors['button_dark_hover']};
                selection-color: {self.colors['button_dark_text']};
                color: {self.colors['text_primary']};
                padding: 4px;
            }}
        """)
        # Connect signal to update details when format changes (optional)
        # self.format_combo.currentIndexChanged.connect(self.update_export_details)

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        return format_layout

    def _create_file_details(self):
        """Creates the inset frame showing export filename and contents."""
        details_frame = QFrame()
        details_frame.setObjectName("detailsFrame")
        details_frame.setStyleSheet(f"""
            #detailsFrame {{
                background-color: {self.colors['details_frame_bg']};
                border: 1px solid {self.colors['details_frame_border']};
                border-radius: 5px;
                padding: 15px;
            }}
            #detailsFrame > QLabel {{
                background-color: transparent;
                border: none;
            }}
        """)

        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(0, 0, 0, 0) # Padding handled by frame stylesheet
        details_layout.setSpacing(12) # Spacing between filename row and list

        # Filename row (Icon + Text)
        filename_layout = QHBoxLayout()
        filename_layout.setSpacing(8)

        icon_label = QLabel()
        icon_pixmap = get_icon(QStyle.SP_FileIcon).pixmap(QSize(18, 18))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(18, 18))
        icon_label.setStyleSheet("margin-top: 1px; border: none;")

        # Store filename label for potential updates
        self.filename_label = QLabel("motor_unit_patterns_2025.csv")
        self.filename_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.filename_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;")

        filename_layout.addWidget(icon_label)
        filename_layout.addWidget(self.filename_label)
        filename_layout.addStretch(1)
        details_layout.addLayout(filename_layout)

        # "File will include:" label
        include_label = QLabel("File will include:")
        include_label.setFont(QFont("Arial", 9))
        include_label.setStyleSheet(f"color: {self.colors['text_secondary']}; margin-top: 5px; border: none;")
        details_layout.addWidget(include_label)

        # List of included data
        list_layout = QVBoxLayout()
        list_layout.setSpacing(4)
        list_layout.setContentsMargins(10, 0, 0, 0) # Indent the list items

        items_to_include = [
            "Motor unit firing timestamps",
            "Pattern analysis data",
            "Recording metadata"
        ]
        # Store these labels if they need to be updated dynamically
        self.include_item_labels = []
        for item_text in items_to_include:
            item_label = QLabel(f"• {item_text}") # Use bullet point character
            item_label.setFont(QFont("Arial", 9))
            item_label.setStyleSheet(f"color: {self.colors['text_list_item']}; border: none;")
            list_layout.addWidget(item_label)
            self.include_item_labels.append(item_label)

        details_layout.addLayout(list_layout)
        details_layout.addStretch(1) # Push list items up if frame is tall

        return details_frame


    def _create_action_buttons(self):
        """Creates the layout for the Export and Cancel buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 10, 0, 0) # Add some top margin

        export_button = QPushButton("Export File")
        export_button.setFont(QFont("Arial", 10, QFont.Bold))
        export_button.setIcon(get_icon(QStyle.SP_DialogSaveButton)) # Save/Export icon
        export_button.setIconSize(QSize(16, 16))
        export_button.setMinimumHeight(36)
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['button_dark_bg']};
                color: {self.colors['button_dark_text']};
                border: none;
                border-radius: 5px;
                padding: 8px 18px; /* Adjusted padding */
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_dark_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['button_dark_bg']};
            }}
        """)
        export_button.clicked.connect(self.handle_export)

        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(QFont("Arial", 10))
        cancel_button.setMinimumHeight(36)
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['button_light_bg']};
                color: {self.colors['button_light_text']};
                border: 1px solid {self.colors['button_light_border']};
                border-radius: 5px;
                padding: 8px 18px; /* Adjusted padding */
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_light_hover_bg']};
                border-color: #adb5bd; /* Darker border on hover */
            }}
            QPushButton:pressed {{
                background-color: #e9ecef; /* Slightly darker background when pressed */
            }}
        """)
        cancel_button.clicked.connect(self.handle_cancel)

        button_layout.addWidget(export_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch(1) # Push buttons to the left

        return button_layout

    # --- Placeholder Slots ---

    def handle_export(self):
        """Placeholder slot for the 'Export File' button click."""
        selected_format = self.format_combo.currentText()
        filename = self.filename_label.text()
        print(f"Initiating export for '{filename}' in format: {selected_format}")
        # ----> Add your actual file export logic here <----
        print("Export process started (placeholder).")
        # Optionally close the window after starting export
        # self.close()

    def handle_cancel(self):
        """Placeholder slot for the 'Cancel' button click."""
        print("Export cancelled.")
        self.close() # Close the export window

    # --- Optional Update Logic ---
    def update_export_details(self):
        """(Optional) Updates filename and included items based on format selection."""
        selected_text = self.format_combo.currentText()
        base_filename = "motor_unit_patterns_2025" # Example base name

        if "CSV" in selected_text:
            new_ext = ".csv"
            # Update included items if they differ for CSV
            # self.include_item_labels[0].setText("• Item A for CSV")
            # ...
        elif "MAT" in selected_text:
            new_ext = ".mat"
            # Update included items if they differ for MAT
            # self.include_item_labels[0].setText("• Item X for MAT")
            # ...
        elif "XLSX" in selected_text:
            new_ext = ".xlsx"
            # Update included items if they differ for XLSX
            # ...
        else:
            new_ext = ".dat" # Default extension

        self.filename_label.setText(base_filename + new_ext)
        print(f"Export details updated for format: {selected_text}")


# --- Main execution block (for testing the window independently) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle("Fusion") # Optional: Set a style

    export_dialog = ExportFileWindow()
    export_dialog.show()

    sys.exit(app.exec_())