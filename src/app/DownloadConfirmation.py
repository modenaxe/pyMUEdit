import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

# Import the UI setup function
from ui.DownloadConfirmationUI import setup_ui


class DownloadConfirmation(QWidget):
    """
    A QWidget displaying confirmation of a successful export,
    providing a direct download link and showing recent exports.
    """

    # Signals
    return_requested = pyqtSignal()
    download_requested = pyqtSignal(str)  # Emits filename to download
    recent_download_requested = pyqtSignal(str)  # Emits filename from recent list

    def __init__(self, parent=None):
        """
        Initializes the DownloadConfirmation.
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)

        # Set up the UI using the imported setup_ui function
        setup_ui(self)

    def set_export_details(self, filename, filesize_bytes):
        """Updates the main download row details."""
        self._main_download_filename = filename  # Store for download button signal
        if self._download_filename_label:
            self._download_filename_label.setText(os.path.basename(filename))  # Show only filename
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
    test_win.setWindowTitle("Test DownloadConfirmation")
    layout = QVBoxLayout(test_win)
    complete_widget = DownloadConfirmation()

    # Simulate setting details
    complete_widget.set_export_details("/path/to/some/Export_File_Name_123.csv", 15200 * 1024)  # Example 15.2 MB
    layout.addWidget(complete_widget)
    test_win.setStyleSheet("background-color: #e0e0e0;")
    test_win.resize(700, 550)

    # Example connecting signals
    complete_widget.return_requested.connect(lambda: print("TEST: Return Requested!"))
    complete_widget.download_requested.connect(lambda fn: print(f"TEST: Main Download Requested: {fn}"))
    complete_widget.recent_download_requested.connect(lambda fn: print(f"TEST: Recent Download Requested: {fn}"))

    test_win.show()
    sys.exit(app.exec_())
