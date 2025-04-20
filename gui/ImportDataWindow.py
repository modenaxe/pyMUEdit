import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtCore import pyqtSignal

# Import UI setup function
from ui.ImportDataWindowUI import setup_ui

# Ensure the current and project directories are in the system path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(current_dir)

# Import needed functions from other modules
from utils.config_and_input.open_otb import open_otb
from EmgDecomposition import offline_EMG as EMG_offline_EMG
from SaveMatWorker import SaveMatWorker

# Import DecompositionApp for passing data
from DecompositionApp import DecompositionApp


class ImportDataWindow(QWidget):
    # Signal to notify the main window to return to dashboard
    return_to_dashboard_requested = pyqtSignal()

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
        self.decomp_app = None  # Reference to DecompositionApp window

        # Create EMG object using the appropriate class
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.emg_obj = EMG_offline_EMG(save_dir=temp_dir, to_filter=True)  # Use the imported class

        # Define color scheme
        self.colors = {
            "bg_main": "#ffffff",
            "bg_sidebar": "#f8f8f8",
            "bg_dropzone": "#f8f8f8",
            "text_primary": "#333333",
            "text_secondary": "#777777",
            "border": "#e0e0e0",
            "accent": "#000000",
            "button_bg": "#222222",
            "button_text": "#ffffff",
        }

        # Sample recent files list
        self.recent_files = ["HDEMG_data_001.csv", "HDEMG_data_002.csv", "HDEMG_data_003.csv"]

        # Set up the UI (imported from import_data_window_ui.py)
        setup_ui(self)

        # Set up drag and drop events
        self.dropzone.setAcceptDrops(True)
        self.dropzone.dragEnterEvent = self.dragEnterEvent
        self.dropzone.dropEvent = self.dropEvent

    def select_file(self):
        """Open file dialog to select a file."""
        file, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
        if not file:
            return

        self.filename = os.path.basename(file)
        self.pathname = os.path.dirname(file) + "/"

        self.file_info_label.setText(f"Selected: {self.filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {self.filename}")

        file_size = os.path.getsize(file)
        file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/(1024*1024):.1f} MB"
        self.size_info.setText(f"Size: {size_str}")
        self.format_info.setText(f"Format: {file_format}")

        self.load_file(self.pathname, self.filename)

    def load_recent_file(self, filename):
        """Load a file from the recent files list."""
        self.filename = filename
        self.pathname = "./"
        self.file_info_label.setText(f"Selected: {self.filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {self.filename}")
        self.size_info.setText("Size: 2.4 MB")
        self.format_info.setText(f"Format: {os.path.splitext(filename)[1].upper().replace('.', '')}")
        self.preview_message.setText(f"Preview of {filename}\n(Simulated data for demonstration)")
        self.next_btn.setEnabled(True)

    def load_file(self, path, file):
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
            except Exception as e:
                self.preview_message.setText(f"Error loading file: {str(e)}")
                print(f"Error loading OTB+ file: {e}")
                traceback.print_exc()
                self.next_btn.setEnabled(False)
        else:
            self.preview_message.setText(f"File type {ext} not supported in this demo.\nPlease select an OTB+ file.")
            self.next_btn.setEnabled(False)

    def save_mat_in_background(self, filename, data, compression=True):
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)
        worker.finished.connect(lambda: self.on_save_finished(worker))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))
        worker.start()

    def on_save_finished(self, worker):
        print("Data saved successfully")
        self.cleanup_thread(worker)

    def on_save_error(self, worker, error_msg):
        print(f"Error saving data: {error_msg}")
        self.cleanup_thread(worker)

    def cleanup_thread(self, worker):
        if worker in self.threads:
            self.threads.remove(worker)

    def go_back(self):
        """Go back to previous screen."""
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

    def show_import_window(self):
        """Show this window again when returning from DecompositionApp."""
        self.show()
        if self.decomp_app:
            self.decomp_app.hide()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.filename = os.path.basename(file_path)
                self.pathname = os.path.dirname(file_path) + "/"
                self.file_info_label.setText(f"Selected: {self.filename}")
                self.file_info_label.setVisible(True)
                self.footer_file_info.setText(f"File: {self.filename}")
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
                self.load_file(self.pathname, self.filename)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportDataWindow()
    window.show()
    sys.exit(app.exec_())
