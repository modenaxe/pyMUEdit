import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Import UI setup function
from ui.ExportResultsUI import setup_ui, create_export_setup_widget, get_icon

# --- Import Widgets ---
from ExportConfirm import ExportConfirm
from DownloadConfirmation import DownloadConfirmation


class ExportResultsWindow(QWidget):
    """Main window for the export process, using QStackedWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setWindowTitle("Export Results")
        self.setMinimumSize(600, 550)  # Adjusted size
        self.setWindowIcon(get_icon("SP_DialogSaveButton"))

        # Set up the UI from the imported setup_ui function
        setup_ui(self)

        # --- Create Views ---
        self.setup_view = create_export_setup_widget(self)
        self.confirmation_view = ExportConfirm()
        self.complete_view = DownloadConfirmation()

        # --- Add Views to Stack ---
        self.stacked_widget.addWidget(self.setup_view)
        self.stacked_widget.addWidget(self.confirmation_view)
        self.stacked_widget.addWidget(self.complete_view)

        # --- Connect Signals ---
        self.setup_view.handle_export_request = self.handle_export_request

        if isinstance(self.confirmation_view, ExportConfirm):
            self.confirmation_view.cancel_requested.connect(self.show_setup_view)
            self.confirmation_view.export_confirmed.connect(self.execute_final_export)

        if isinstance(self.complete_view, DownloadConfirmation):
            self.complete_view.return_requested.connect(self.show_setup_view)
            self.complete_view.download_requested.connect(self.handle_complete_download)
            self.complete_view.recent_download_requested.connect(self.handle_complete_recent_download)

        # --- Initial View ---
        self.show_setup_view()

    def handle_export_request(self):
        """Handle the export request from the setup view."""
        selected_format = self.setup_view.format_combo.currentText()
        if self.setup_view.format_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Format Required", "Please select a file format before exporting.")
            return
        print(f"Setup Widget: Requesting export with format: {selected_format}")
        self.show_confirmation_view(selected_format)

    def show_setup_view(self):
        """Switch to the setup view."""
        print("Switching to Setup View")
        self.stacked_widget.setCurrentWidget(self.setup_view)
        self.setWindowTitle("Export Results")
        self.main_title_label.setText("Export Results")
        self.main_subtitle_label.setText("Export your motor unit firing patterns data")
        self.main_subtitle_label.show()
        self.footer_label.show()  # Make sure footer is visible
        self.resize(600, 550)  # Reset size

    def show_confirmation_view(self, selected_format):
        """Switch to the confirmation view with the selected format."""
        if not isinstance(self.confirmation_view, ExportConfirm):
            print("Error: Confirmation view not loaded.")
            return

        print(f"Switching to Confirmation View. Format: {selected_format}")
        base_filename = "firing_patterns_export"
        ext = ".dat"  # Default

        if "CSV" in selected_format:
            ext = ".csv"
        elif "MAT" in selected_format:
            ext = ".mat"
        elif "XLSX" in selected_format:
            ext = ".xlsx"
        elif "TXT" in selected_format:
            ext = ".txt"

        filename = f"{base_filename}{ext}"
        self.confirmation_view.set_export_details(selected_format, filename)
        self.stacked_widget.setCurrentWidget(self.confirmation_view)
        self.setWindowTitle("Confirm Export")
        self.main_title_label.setText("Confirm Export")
        self.main_subtitle_label.setText("Review the details before exporting.")
        self.main_subtitle_label.show()
        self.footer_label.show()

        # Adjust size dynamically based on confirmation view's hint + padding
        conf_hint = self.confirmation_view.sizeHint()
        self.resize(conf_hint.width() + 40, conf_hint.height() + 120)

    def show_complete_view(self, saved_filepath, saved_filesize_bytes):
        """Switch to the Export Complete view."""
        if not isinstance(self.complete_view, DownloadConfirmation):
            print("Error: Cannot switch to complete view, it was not loaded.")
            self.show_setup_view()  # Fallback
            return

        print(f"Switching to Complete View for file: {saved_filepath}")
        self.complete_view.set_export_details(saved_filepath, saved_filesize_bytes)
        self.stacked_widget.setCurrentWidget(self.complete_view)
        self.setWindowTitle("Export Complete")
        self.main_title_label.setText("Export Complete!")
        self.main_subtitle_label.hide()  # Hide subtitle on complete screen
        self.footer_label.hide()  # Hide footer on complete screen
        self.resize(700, 550)  # Set size for complete view

    def execute_final_export(self, file_format, filename):
        """Handle file dialog and saving of the export."""
        print(f"--- FINAL EXPORT TRIGGERED --- Format: {file_format}, Suggested Filename: {filename}")
        options = QFileDialog.Options()
        suggested_path = os.path.join(os.path.expanduser("~"), filename)

        if "CSV" in file_format:
            file_filter = "CSV Files (*.csv);;All Files (*)"
        elif "MAT" in file_format:
            file_filter = "MATLAB Files (*.mat);;All Files (*)"
        elif "XLSX" in file_format:
            file_filter = "Excel Files (*.xlsx);;All Files (*)"
        elif "TXT" in file_format:
            file_filter = "Text Files (*.txt);;All Files (*)"
        else:
            file_filter = "All Files (*)"

        filePath, _ = QFileDialog.getSaveFileName(
            self, "Save Exported File", suggested_path, file_filter, options=options
        )

        if filePath:
            print(f"   User chose path: {filePath}")
            try:
                # --- !!! Replace with your ACTUAL data saving logic !!! ---
                print("   (Simulating file save...)")
                file_size = 0
                with open(filePath, "w") as f:
                    f.write(f"Exported Data\nFormat: {file_format}\nSuggested Name: {filename}\n")
                    # Simulate some content size
                    dummy_content = "Dummy content " * 5000
                    f.write(dummy_content)
                    file_size = f.tell()  # Get approximate size after writing
                print(f"   (Simulated save complete)")
                # --- !!! End of saving logic placeholder !!! ---

                # Get actual file size if simulation wasn't accurate
                if file_size == 0:  # Fallback if tell() didn't work as expected
                    file_size = os.path.getsize(filePath)

                print(f"--- Successfully saved data to {filePath} (Size: {file_size} bytes) ---")
                self.show_complete_view(filePath, file_size)

            except Exception as e:
                print(f"!!!!! ERROR during file save: {e}")
                traceback.print_exc()
                QMessageBox.critical(self, "Export Error", f"Could not save file to:\n{filePath}\n\nError: {e}")
        else:
            print("   File save cancelled by user.")

    def handle_complete_download(self, filename):
        """Handle request to download the primary exported file again."""
        print(f"Handling main download request for: {filename}")
        QMessageBox.information(
            self, "Download", f"Download requested for:\n{filename}\n\n(Add actual download/copy logic here)"
        )

    def handle_complete_recent_download(self, filename):
        """Handle request to download a file from the recent list shown on complete screen."""
        print(f"Handling recent download request for: {filename}")
        QMessageBox.information(
            self,
            "Download Recent",
            f"Download requested for recent file:\n{filename}\n\n(Add actual download/copy logic here)",
        )

    def closeEvent(self, event):
        """Override close event to hide instead of close."""
        print("ExportResultsWindow: Hiding instead of closing.")
        self.hide()
        event.ignore()


# --- Main execution block ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    export_window = ExportResultsWindow()
    export_window.show()
    sys.exit(app.exec_())
