import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

# Import UI setup function
from ui.ImportDataWindowUI import setup_ui

# Ensure the current and project directories are in the system path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(current_dir)

# Import needed functions from other modules
from core.utils.config_and_input.open_otb import open_otb
from core.EmgDecomposition import offline_EMG as EMG_offline_EMG
from workers.SaveMatWorker import SaveMatWorker


class ImportDataWindow(QWidget):
    # Signal to notify the main window to return to dashboard
    return_to_dashboard_requested = pyqtSignal()

    # Signal to request showing decomposition view with data
    decomposition_requested = pyqtSignal(object, str, str, object)

    # Signal to notify other windows when a file is imported (if needed)
    fileImported = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize file loading variables
        self.filename = None
        self.pathname = None
        self.imported_signal = None  # Will store the imported signal data
        self.threads = []  # Keep reference to worker threads
        self.file_size_bytes = None  # Store file size in bytes

        # Create EMG object using the appropriate class
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.emg_obj = EMG_offline_EMG(save_dir=temp_dir, to_filter=True)

        # Sample recent files list (could be loaded from settings/history)
        self.recent_files = []

        # Set up the UI using our improved UI setup
        setup_ui(self)

        # Set up drag and drop events for the dropzone
        self.dropzone.setAcceptDrops(True)
        self.dropzone.dragEnterEvent = self.dragEnterEvent
        self.dropzone.dropEvent = self.dropEvent

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for file drops."""
        if event.mimeData().hasUrls():  # type:ignore
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events for files."""
        if event.mimeData().hasUrls():  # type:ignore
            url = event.mimeData().urls()[0]  # type:ignore
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.filename = os.path.basename(file_path)
                self.pathname = os.path.dirname(file_path) + "/"

                # Update UI to show selected file
                self.file_info_label.setText(f"Selected: {self.filename}")
                self.file_info_label.setVisible(True)
                self.footer_file_info.setText(f"File: {self.filename}")

                # Update file size and format
                file_size = os.path.getsize(file_path)
                file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")

                if file_size < 1024:
                    size_str = f"{file_size} bytes"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"

                self.size_info.setText(f"Size: {size_str}")
                self.format_info.setText(f"Format: {file_format}")

                # Load the file
                self.load_file(self.pathname, self.filename)

    def select_file(self):
        """Open file dialog to select a file."""
        file, _ = QFileDialog.getOpenFileName(
            self, "Select HDEMG File", "", "All Files (*.*);; CSV Files (*.csv);; OTB+ Files (*.otb+)"
        )

        if not file:
            return

        self.filename = os.path.basename(file)
        self.pathname = os.path.dirname(file) + "/"

        # Update UI to show selected file
        self.file_info_label.setText(f"Selected: {self.filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {self.filename}")

        # Get file size in bytes
        file_size = os.path.getsize(file)
        file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")

        # Format file size for display
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/(1024*1024):.1f} MB"

        self.size_info.setText(f"Size: {size_str}")
        self.format_info.setText(f"Format: {file_format}")

        # Load the file (passing the whole path)
        self.load_file(self.pathname, self.filename)
        
        # Pass file size in original units (bytes)
        self.file_size_bytes = file_size

    def load_recent_file(self, filename):
        """Load a file from the recent files list."""
        self.filename = filename
        self.pathname = "./"  # This would be the actual path in a real implementation

        # Update UI to show selected file
        self.file_info_label.setText(f"Selected: {self.filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {self.filename}")

        # In a real implementation, we would get actual file size
        self.size_info.setText("Size: 2.4 MB")
        self.format_info.setText(f"Format: {os.path.splitext(filename)[1].upper().replace('.', '')}")

        # Show preview message
        self.preview_message.setText(f"Preview of {filename}\n(Simulated data for demonstration)")

        # Enable the next button
        self.next_btn.setEnabled(True)

    def load_file(self, path, file):
        """Load and process a file."""
        self.preview_message.setText("Loading file...")
        ext = os.path.splitext(file)[1].lower()

        if ext == ".otb+":
            try:
                # Construct the full file path
                full_path = os.path.join(path, file)

                # Create a new EMG object for this file
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                self.emg_obj = EMG_offline_EMG(save_dir=temp_dir, to_filter=True)

                # Call the open_otb function with the correct parameters
                open_otb(self.emg_obj, full_path)

                # Get the signal from the EMG object
                signal = self.emg_obj.signal_dict

                # Store the imported signal
                self.imported_signal = signal

                # Create a default save name for .mat files
                savename = os.path.join(path, file + "_processed.mat")

                # Save the data as a .mat file in the background
                if signal:
                    self.save_mat_in_background(savename, {"signal": signal}, True)

                # Update the UI
                self.preview_message.setText(
                    f"Successfully loaded {file}\nFile contains EMG data with {signal['data'].shape[0]} channels"
                )
                self.next_btn.setEnabled(True)

                # Signal that we've imported a file with more details
                file_info = {
                    "filename": file,
                    "pathname": path,
                    "signal": signal,
                    "filesize": os.path.getsize(full_path)  # Get actual file size
                }
                
                self.fileImported.emit(file_info)

            except Exception as e:
                self.preview_message.setText(f"Error loading file: {str(e)}")
                print(f"Error loading OTB+ file: {e}")
                traceback.print_exc()
                self.next_btn.setEnabled(False)
        else:
            self.preview_message.setText(f"File type {ext} not supported in this demo.\nPlease select an OTB+ file.")
            self.next_btn.setEnabled(False)

    def save_mat_in_background(self, filename, data, compression=True):
        """Save data as .mat file in a background thread."""
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)

        worker.finished.connect(lambda: self.on_save_finished(worker))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))

        worker.start()

    def on_save_finished(self, worker):
        """Handle completion of background save."""
        print("Data saved successfully")
        self.cleanup_thread(worker)

    def on_save_error(self, worker, error_msg):
        """Handle error in background save."""
        print(f"Error saving data: {error_msg}")
        self.cleanup_thread(worker)

    def cleanup_thread(self, worker):
        """Remove completed worker from threads list."""
        if worker in self.threads:
            self.threads.remove(worker)

    def go_back(self):
        """Go back to previous screen (dashboard)."""
        self.return_to_dashboard_requested.emit()

    def go_to_algorithm_screen(self):
        """Signal to the dashboard to show the decomposition view."""
        if not self.filename or not self.emg_obj:
            return

        try:
            # Save data as .mat file (for compatibility with other parts of the pipeline)
            if self.pathname and self.filename:
                savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
                self.save_mat_in_background(savename, {"signal": self.imported_signal}, True)

            # Emit signal to request showing decomposition view
            self.decomposition_requested.emit(self.emg_obj, self.filename, self.pathname, self.imported_signal)

        except Exception as e:
            print(f"Error requesting decomposition view: {e}")
            traceback.print_exc()

    def showEvent(self, event):
        """Event triggered when the widget is shown."""
        # Update sidebar with recent files section using UI function
        if hasattr(self, "update_sidebar_with_recent_files"):
            self.update_sidebar_with_recent_files()

        # Call the parent method
        super().showEvent(event)

    def hideEvent(self, event):
        """Event triggered when the widget is hidden."""
        # Remove recent files section from sidebar using UI function
        if hasattr(self, "restore_sidebar"):
            self.restore_sidebar()

        # Call the parent method
        super().hideEvent(event)


# For testing the window independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportDataWindow()
    window.show()
    sys.exit(app.exec_())
