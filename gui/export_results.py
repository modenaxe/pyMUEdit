import sys
import os
import traceback # Make sure traceback is imported
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QComboBox, QSpacerItem,
    QSizePolicy, QStyle, QStackedWidget # Import QStackedWidget
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal

# --- Import the refactored confirmation widget ---
try:
    from export_confirmation import ExportConfirmWidget
except ImportError:
    print("Warning: Could not import ExportConfirmWidget from export_confirmation.py")
    ExportConfirmWidget = None
# ---

# Helper function to get standard icons
def get_icon(standard_icon):
    return QApplication.style().standardIcon(standard_icon)

# --- Create a widget for the initial setup view ---
class ExportSetupWidget(QWidget):
    """Contains the initial export setup controls and recent list."""
    # Signal emitted when user clicks "Export Data"
    export_requested = pyqtSignal(str) # Emits the selected format text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = { # Define colors needed for this part
            "bg_main": "#fdfdfd", # Used for background of this widget?
            "bg_card": "#ffffff",
            "border_light": "#e0e0e0",
            "text_primary": "#333333",
            "text_secondary": "#777777",
            "button_dark_bg": "#212529",
            "button_dark_text": "#ffffff",
            "button_dark_hover": "#343a40",
            "item_bg_hover": "#f0f0f0",
        }

        # Main layout for this setup widget
        setup_layout = QVBoxLayout(self)
        setup_layout.setContentsMargins(0, 0, 0, 0) # Let container handle margins
        setup_layout.setSpacing(20)

        # Create and add the sections
        setup_layout.addWidget(self._create_export_setup_section())
        setup_layout.addWidget(self._create_recent_exports_section())
        setup_layout.addStretch(1) # Push footer down if needed within this view

        # Keep footer separate or move to main window? Moved to main for consistency.
        # setup_layout.addWidget(self._create_footer())

    # --- Methods moved from ExportResultsWindow ---
    def _create_export_setup_section(self):
        setup_card = QFrame(); setup_card.setObjectName("setupCard"); setup_card.setFrameShape(QFrame.StyledPanel)
        setup_card.setStyleSheet(f""" #setupCard {{ background-color: {self.colors['bg_card']}; border: 1px solid {self.colors['border_light']}; border-radius: 8px; padding: 15px; }} QLabel {{ border: none; background: transparent; }} QComboBox {{ border: 1px solid {self.colors['border_light']}; border-radius: 4px; padding: 6px 10px; background-color: {self.colors['bg_card']}; color: {self.colors['text_primary']}; font-size: 9pt; min-height: 20px; }} QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left: 1px solid {self.colors['border_light']}; }} QComboBox::down-arrow {{ image: url(:/qt-project.org/styles/commonstyle/images/down_arrow-16.png); width: 12px; height: 12px; }} """)
        card_layout = QVBoxLayout(setup_card); card_layout.setContentsMargins(0, 0, 0, 0); card_layout.setSpacing(15)
        format_label = QLabel("Select File Format"); format_label.setFont(QFont("Arial", 9, QFont.Bold)); format_label.setStyleSheet(f"color: {self.colors['text_primary']}; margin-bottom: -5px;"); card_layout.addWidget(format_label)
        self.format_combo = QComboBox(); self.format_combo.addItems([".csv (Comma Separated Values)", ".mat (MATLAB)", ".xlsx (Excel Spreadsheet)", ".txt (Text File)"]); self.format_combo.setPlaceholderText("Choose an export format..."); self.format_combo.setCurrentIndex(-1)
        card_layout.addWidget(self.format_combo)
        data_details_frame = QFrame(); data_details_layout = QVBoxLayout(data_details_frame); data_details_layout.setContentsMargins(0, 5, 0, 5); data_details_layout.setSpacing(8)
        data_title_label = QLabel("Selected Data"); data_title_label.setFont(QFont("Arial", 9, QFont.Bold)); data_title_label.setStyleSheet(f"color: {self.colors['text_primary']};"); data_details_layout.addWidget(data_title_label)
        data_details_layout.addWidget(self._create_info_item(get_icon(QStyle.SP_FileIcon), "Motor Unit Firing Patterns"))
        data_details_layout.addWidget(self._create_info_item(get_icon(QStyle.SP_DialogApplyButton), "Recording Duration: 120s"))
        data_details_layout.addWidget(self._create_info_item(get_icon(QStyle.SP_ComputerIcon), "Units Detected: 12"))
        card_layout.addWidget(data_details_frame)
        export_button = QPushButton("Export Data"); export_button.setFont(QFont("Arial", 10, QFont.Bold)); export_button.setIcon(get_icon(QStyle.SP_ArrowDown)); export_button.setIconSize(QSize(16, 16)); export_button.setMinimumHeight(40); export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet(f""" QPushButton {{ background-color: {self.colors['button_dark_bg']}; color: {self.colors['button_dark_text']}; border: none; border-radius: 4px; padding: 8px 15px; }} QPushButton:hover {{ background-color: {self.colors['button_dark_hover']}; }} """)
        export_button.clicked.connect(self._handle_export_request) # Connect to internal handler
        card_layout.addWidget(export_button)
        return setup_card

    def _create_info_item(self, icon, text):
        item_widget = QWidget(); item_layout = QHBoxLayout(item_widget); item_layout.setContentsMargins(0, 0, 0, 0); item_layout.setSpacing(8)
        icon_label = QLabel(); icon_label.setPixmap(icon.pixmap(QSize(16, 16))); icon_label.setFixedSize(QSize(18, 18)); icon_label.setAlignment(Qt.AlignCenter)
        text_label = QLabel(text); text_label.setFont(QFont("Arial", 9)); text_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
        item_layout.addWidget(icon_label); item_layout.addWidget(text_label); item_layout.addStretch(1)
        return item_widget

    def _create_recent_exports_section(self):
        recent_card = QFrame(); recent_card.setObjectName("recentCardSetup"); recent_card.setFrameShape(QFrame.StyledPanel) # Unique name
        recent_card.setStyleSheet(f""" #recentCardSetup {{ background-color: {self.colors['bg_card']}; border: 1px solid {self.colors['border_light']}; border-radius: 8px; padding: 15px; }} #recentCardSetup > QLabel {{ color: {self.colors['text_primary']}; font-size: 11pt; font-weight: bold; border: none; background: transparent; margin-bottom: 5px; }} """)
        card_layout = QVBoxLayout(recent_card); card_layout.setContentsMargins(0, 0, 0, 0); card_layout.setSpacing(5)
        title_label = QLabel("Recent Exports"); card_layout.addWidget(title_label)
        recent_exports_data = [ {"icon": get_icon(QStyle.SP_DialogHelpButton), "filename": "firing_patterns_2025.01.15.csv", "metadata": "2.4 MB • Completed"}, {"icon": get_icon(QStyle.SP_DriveHDIcon), "filename": "firing_patterns_2025.01.14.mat", "metadata": "3.1 MB • Completed"}, ]
        if not recent_exports_data: no_exports_label = QLabel("No recent exports found."); no_exports_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-style: italic; padding: 10px;"); no_exports_label.setAlignment(Qt.AlignCenter); card_layout.addWidget(no_exports_label)
        else:
            for export_data in recent_exports_data: card_layout.addWidget(self._create_recent_export_item(export_data["icon"], export_data["filename"], export_data["metadata"]))
        return recent_card

    def _create_recent_export_item(self, icon, filename, metadata):
        item_frame = QFrame(); item_frame.setObjectName("recentItemSetup"); item_frame.setMinimumHeight(50); item_frame.setCursor(Qt.PointingHandCursor) # Unique name
        item_frame.setStyleSheet(f""" QFrame#recentItemSetup {{ background-color: transparent; border-radius: 4px; border: 1px solid transparent; padding: 5px 0px; }} QFrame#recentItemSetup:hover {{ background-color: {self.colors['item_bg_hover']}; border: 1px solid {self.colors['border_light']}; }} QLabel {{ background-color: transparent; border: none; }} QPushButton#downloadBtnSetup {{ background-color: transparent; border: none; padding: 5px; border-radius: 15px; qproperty-iconSize: 18px 18px; }} QPushButton#downloadBtnSetup:hover {{ background-color: {self.colors['border_light']}; }} """)
        item_layout = QHBoxLayout(item_frame); item_layout.setContentsMargins(10, 5, 10, 5); item_layout.setSpacing(10)
        icon_label = QLabel(); icon_label.setPixmap(icon.pixmap(QSize(20, 20))); icon_label.setFixedSize(QSize(24, 24)); icon_label.setAlignment(Qt.AlignCenter); item_layout.addWidget(icon_label)
        text_layout = QVBoxLayout(); text_layout.setContentsMargins(0,0,0,0); text_layout.setSpacing(1)
        filename_label = QLabel(filename); filename_label.setFont(QFont("Arial", 9, QFont.Bold)); filename_label.setStyleSheet(f"color: {self.colors['text_primary']};")
        metadata_label = QLabel(metadata); metadata_label.setFont(QFont("Arial", 8)); metadata_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
        text_layout.addWidget(filename_label); text_layout.addWidget(metadata_label); item_layout.addLayout(text_layout, 1)
        download_button = QPushButton(); download_button.setObjectName("downloadBtnSetup") # Unique name
        download_button.setIcon(get_icon(QStyle.SP_ArrowDown)); download_button.setFixedSize(QSize(30, 30)); download_button.setCursor(Qt.PointingHandCursor); download_button.setProperty("filename", filename); download_button.clicked.connect(self._handle_download_recent)
        item_layout.addWidget(download_button)
        return item_frame

    # --- Internal handler for export button ---
    def _handle_export_request(self):
        selected_format = self.format_combo.currentText()
        if self.format_combo.currentIndex() < 0:
            print("Please select an export format.")
            # Consider showing a message box to the user here
            # from PyQt5.QtWidgets import QMessageBox
            # QMessageBox.warning(self, "Format Required", "Please select a file format before exporting.")
            return
        print(f"Setup Widget: Emitting export_requested signal with format: {selected_format}")
        self.export_requested.emit(selected_format)

    def _handle_download_recent(self):
        sender_button = self.sender()
        if sender_button:
            filename = sender_button.property("filename")
            print(f"Setup Widget: Download requested for recent file: {filename}")
            # Add logic to download/open the specific file
        else:
            print("Setup Widget: Could not determine which download button was clicked.")
# --- End ExportSetupWidget ---


# --- Main Window Class (Container) ---
class ExportResultsWindow(QWidget):
    """
    Main window for the export process, using QStackedWidget
    to switch between setup and confirmation views.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, False) # Keep instance alive
        self.setWindowTitle("Export Results") # Initial title
        self.setMinimumSize(550, 500)
        self.setWindowIcon(get_icon(QStyle.SP_DialogSaveButton))

        self.colors = { # Main window colors
            "bg_main": "#fdfdfd",
            "text_secondary": "#777777",
        }
        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15) # Spacing between title area and stacked widget

        # --- Title Area (Optional - can be part of setup widget) ---
        # If you want the title static above the stacked widget
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        self.main_title_label = QLabel("Export Results") # Store reference to change it
        self.main_title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.main_title_label.setStyleSheet("color: #333333; border: none;")
        self.main_subtitle_label = QLabel("Export your motor unit firing patterns data") # Store reference
        self.main_subtitle_label.setFont(QFont("Arial", 10))
        self.main_subtitle_label.setStyleSheet("color: #777777; border: none; margin-bottom: 5px;")
        title_layout.addWidget(self.main_title_label)
        title_layout.addWidget(self.main_subtitle_label)
        main_layout.addLayout(title_layout)
        # --- End Title Area ---


        # --- Stacked Widget ---
        self.stacked_widget = QStackedWidget(self)
        main_layout.addWidget(self.stacked_widget, 1) # Allow stack to stretch

        # --- Create Views ---
        self.setup_view = ExportSetupWidget()
        self.confirmation_view = None # Create when needed or check import
        if ExportConfirmWidget:
            self.confirmation_view = ExportConfirmWidget()
        else:
            # Handle case where import failed - maybe show an error label?
            print("ERROR: ExportConfirmWidget could not be created.")


        # --- Add Views to Stack ---
        self.stacked_widget.addWidget(self.setup_view)
        if self.confirmation_view:
            self.stacked_widget.addWidget(self.confirmation_view)
        else:
            error_label = QLabel("Error: Confirmation view failed to load.")
            error_label.setAlignment(Qt.AlignCenter)
            self.stacked_widget.addWidget(error_label)


        # --- Footer ---
        # Place footer below the stacked widget
        self.footer_label = QLabel("Last export: January 15, 2025 at 14:30") # Static text from image
        self.footer_label.setFont(QFont("Arial", 9))
        self.footer_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none; padding-top: 10px;")
        self.footer_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.footer_label)


        # --- Connect Signals ---
        self.setup_view.export_requested.connect(self.show_confirmation_view)
        if self.confirmation_view:
            self.confirmation_view.cancel_requested.connect(self.show_setup_view)
            self.confirmation_view.export_confirmed.connect(self.execute_final_export)

        # --- Initial View ---
        self.show_setup_view() # Start on the setup screen


    def show_setup_view(self):
        """Switches the stacked widget to the setup view."""
        print("Switching to Setup View")
        self.stacked_widget.setCurrentWidget(self.setup_view)
        # Update window title and potentially subtitle
        self.setWindowTitle("Export Results")
        self.main_title_label.setText("Export Results")
        self.main_subtitle_label.setText("Export your motor unit firing patterns data")
        self.main_subtitle_label.show() # Ensure subtitle is visible
        self.resize(self.minimumSizeHint()) # Adjust size if needed


    def show_confirmation_view(self, selected_format):
        """Switches the stacked widget to the confirmation view."""
        if not self.confirmation_view:
            print("Error: Cannot switch to confirmation view, it was not loaded.")
            return

        print(f"Switching to Confirmation View. Format selected: {selected_format}")

        # --- Generate filename based on format (Example) ---
        # You might want more sophisticated naming logic
        base_filename = "firing_patterns_export"
        if "CSV" in selected_format: ext = ".csv"
        elif "MAT" in selected_format: ext = ".mat"
        elif "XLSX" in selected_format: ext = ".xlsx"
        elif "TXT" in selected_format: ext = ".txt"
        else: ext = ".dat"
        filename = f"{base_filename}{ext}"
        # ---

        # Pass the selected details to the confirmation view BEFORE showing it
        self.confirmation_view.set_export_details(selected_format, filename)

        self.stacked_widget.setCurrentWidget(self.confirmation_view)
        # Update window title and potentially hide subtitle
        self.setWindowTitle("Confirm Export")
        self.main_title_label.setText("Confirm Export")
        self.main_subtitle_label.setText("Review the details before exporting.") # Update subtitle
        # self.main_subtitle_label.hide() # Or hide it
        self.resize(self.minimumSizeHint()) # Adjust size

    def execute_final_export(self, file_format, filename):
        """Placeholder for the actual file saving logic."""
        print(f"--- FINAL EXPORT TRIGGERED ---")
        print(f"   Format: {file_format}")
        print(f"   Filename: {filename}")
        print(f"   (Add code here to open QFileDialog.getSaveFileName and save data)")

        # Example: Open save dialog
        from PyQt5.QtWidgets import QFileDialog
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog # Uncomment if native dialog causes issues
        suggested_path = os.path.join(os.path.expanduser("~"), filename) # Suggest home directory

        # Determine filter based on format text
        if "CSV" in file_format: file_filter = "CSV Files (*.csv);;All Files (*)"
        elif "MAT" in file_format: file_filter = "MATLAB Files (*.mat);;All Files (*)"
        elif "XLSX" in file_format: file_filter = "Excel Files (*.xlsx);;All Files (*)"
        elif "TXT" in file_format: file_filter = "Text Files (*.txt);;All Files (*)"
        else: file_filter = "All Files (*)"

        filePath, _ = QFileDialog.getSaveFileName(self,
                                                  "Save Exported File",
                                                  suggested_path,
                                                  file_filter,
                                                  options=options)

        if filePath:
            print(f"   User chose path: {filePath}")
            # --- !!! Add your data saving logic here !!! ---
            try:
                with open(filePath, 'w') as f: # Example: just write dummy data
                     f.write(f"Exported Data\n")
                     f.write(f"Format: {file_format}\n")
                     f.write(f"Original Filename Suggestion: {filename}\n")
                print(f"--- Successfully saved dummy data to {filePath} ---")
                # Optionally show success message
                # from PyQt5.QtWidgets import QMessageBox
                # QMessageBox.information(self, "Export Complete", f"Data successfully exported to:\n{filePath}")

                # Close the window after successful export?
                # self.close() # Or hide() if managed by main window
                self.hide() # Hide instead of close to keep instance if needed

            except Exception as e:
                print(f"!!!!! ERROR during file save: {e}")
                traceback.print_exc()
                # Show error message to user
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Export Error", f"Could not save file to:\n{filePath}\n\nError: {e}")
        else:
            print("   File save cancelled by user.")


    def closeEvent(self, event):
        """Override close event to hide instead of delete."""
        print("ExportResultsWindow: Hiding instead of closing.")
        self.hide()
        event.ignore()

# --- Main execution block (for testing this window standalone) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    export_window = ExportResultsWindow()
    export_window.show()
    sys.exit(app.exec_())
