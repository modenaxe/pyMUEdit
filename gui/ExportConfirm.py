import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import pyqtSignal

# Import the UI setup function
from ui.ExportConfirmUI import setup_ui


class ExportConfirm(QWidget):
    """
    A QWidget containing the export confirmation elements.
    Designed to be placed inside another window or layout.
    """

    # Signals to communicate back to the parent window
    export_confirmed = pyqtSignal(str, str)  # Emits format and filename
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initializes the ExportConfirmWidget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)

        # Set up the UI (calls the setup_ui function from ExportConfirmUI.py)
        setup_ui(self)

    def set_export_details(self, selected_format_text, filename):
        """Sets the display labels based on details from the previous screen."""
        self.format_display_label.setText(selected_format_text)
        self.filename_label.setText(filename)

    # --- Internal Handlers that Emit Signals ---
    def handle_export(self):
        """Emits the export_confirmed signal."""
        selected_format = self.format_display_label.text()  # Get format from label
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
    test_win.setWindowTitle("Test ExportConfirm")
    test_win.setStyleSheet("background-color: #e0e0e0;")  # Give test window a background

    # Create the layout for the test window
    from PyQt5.QtWidgets import QVBoxLayout

    layout = QVBoxLayout(test_win)

    # Create our confirmation widget
    confirm_widget = ExportConfirm()
    confirm_widget.set_export_details("CSV (Test Format)", "test_file_2025.csv")  # Example call
    layout.addWidget(confirm_widget)

    # Example connecting signals for testing
    confirm_widget.export_confirmed.connect(
        lambda fmt, fn: print(f"TEST: Export Confirmed! Format: {fmt}, Filename: {fn}")
    )
    confirm_widget.cancel_requested.connect(lambda: print("TEST: Cancel Requested!"))

    test_win.resize(600, 500)
    test_win.show()
    sys.exit(app.exec_())
