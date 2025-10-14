import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import numpy as np
import pandas as pd
import pyqtgraph as pg

# Import UI setup function
from core.utils.io.filesize_formatter import filesize_formatter
from ui.ImportDataWindowUI import setup_ui
from ui.components.SegmentSessionPage import SegmentSessionPage
from ui.components.VisualisationPage import VisualisationPage

# Ensure the current and project directories are in the system path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(current_dir)

# Import needed functions from other modules
from core.EmgDecomposition import offline_EMG as EMG_offline_EMG
from workers.SaveMatWorker import SaveMatWorker
from enum import Enum

class PreviewElement(Enum):
    LABEL = 0
    GRAPH = 1


class ImportDataWindow(QMainWindow):
    # Signal to notify the main window to return to dashboard
    return_to_dashboard_requested = pyqtSignal()

    # Signal to request showing decomposition view with data
    decomposition_requested = pyqtSignal(object, str, str, object, object)

    # Signal to notify other windows when a file is imported (if needed)
    fileImported = pyqtSignal(dict)

    def __init__(self, emg_obj=None, filename=None, pathname=None, imported_signal=None, parent=None):
        super().__init__()

        # Initialize file loading variables
        self.emg_obj = emg_obj
        self.filename = filename
        self.pathname = pathname
        self.imported_signal = imported_signal  # Will store the imported signal data
        self.threads = []  # Keep reference to worker threads
        self.file_size_bytes = None  # Store file size in bytes
        self.config = None # will be used to store configuration

        # Config popup windows
        self.visualisation_page = None
        self.segment_session = None
        self.config_panel = None

        # Create EMG object using the appropriate class
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.emg_obj = EMG_offline_EMG(save_dir=temp_dir, to_filter=True)

        # Sample recent files list (could be loaded from settings/history)
        self.recent_files = []

        # Set up the UI using our improved UI setup
        setup_ui(self)

        # Connect signals for configration buttons
        self.connect_signals()

        # Set up drag and drop events for the dropzone
        self.dropzone.setAcceptDrops(True)
        self.dropzone.dragEnterEvent = self.dragEnterEvent
        self.dropzone.dropEvent = self.dropEvent

    def dragEnterEvent(self, a0: QDragEnterEvent | None):
        """Handle drag enter events for file drops."""
        if a0 and a0.mimeData().hasUrls():  # type:ignore
            a0.acceptProposedAction()

    def dropEvent(self, a0: QDropEvent | None):
        """Handle drop events for files."""
        if a0.mimeData().hasUrls():  # type:ignore
            url = a0.mimeData().urls()[0]  # type:ignore
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.filename = os.path.basename(file_path)
                self.pathname = os.path.dirname(file_path) + "/"

                # Update UI to show selected file
                self.file_info_label.setText(f"Selected: {self.filename}")
                self.file_info_label.setVisible(True)
                self.footer_file_info.setText(f"File: {self.filename}")

                # Update file size and format
                size_str = filesize_formatter(file_path)
                file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")

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

        file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")
        size_str = filesize_formatter(file)

        self.size_info.setText(f"Size: {size_str}")
        self.format_info.setText(f"Format: {file_format}")

        # Load the file (passing the whole path)
        self.load_file(self.pathname, self.filename)

        # Pass file size in original units (bytes)
        self.file_size_bytes = os.path.getsize(file)

    def load_recent_file(self, filename):
        """Load a file from the recent files list."""
        self.filename = os.path.basename(filename)
        self.pathname = os.path.dirname(filename) + "/"

        # Update UI to show selected file
        self.file_info_label.setText(f"Selected: {self.filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {self.filename}")

        # Get file size in bytes
        size_str = filesize_formatter(filename)
        file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")

        self.size_info.setText(f"Size: {size_str}")
        self.format_info.setText(f"Format: {file_format}")

        # Load the file (passing the whole path)
        self.load_file(self.pathname, self.filename)

        # Pass file size in original units (bytes)
        self.file_size_bytes = os.path.getsize(filename)

    def load_file(self, path, file):
        """Load and process a file."""
        self.preview_message.setText("Loading file...")
        ext = os.path.splitext(file)[1].lower()

        # Reset failure messages
        self.failure_message.setVisible(False)
        
        if ext == ".otb+" or ext == ".mat":
            try:
                # Construct the full file path
                full_path = os.path.join(path, file)

                # Create a new EMG object for this file
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                self.emg_obj = EMG_offline_EMG(save_dir=temp_dir, to_filter=True)

                if ext == ".otb+":
                    # Call the open_otb_plus function with the correct parameters
                    self.emg_obj.open_otb_plus(full_path, self)

                    # Create a default save name for .mat files
                    savename = os.path.join(path, file + "_processed.mat")

                    # Save the data as a .mat file in the background
                    if self.emg_obj.signal_dict:
                        self.save_mat_in_background(savename, {"signal": self.emg_obj.signal_dict}, True, True)
                elif ext == '.mat':
                    # Call the open_otb_plus function with the correct parameters
                    self.emg_obj.open_mat(full_path)

                # Store the imported signal
                signal = self.emg_obj.signal_dict
                self.imported_signal = signal

                # Load file data into the plot
                if "data" in signal and "fsamp" in signal:
                    try:
                        self.cur_electrode_preview_idx = 0
                        # Plot channels for previews
                        self.update_preview_plot()
                        self.update_buttons()
                    except Exception as e:
                        print(f"Error creating preview plot: {e}")
                else:
                    print("Error cannot display data")

                # Resize app window to show the plot properly, then display the plot in the preview pane
                self.preview_stacked_frame.setCurrentIndex(PreviewElement.GRAPH.value)
                self.next_btn.setEnabled(True)

                # Signal that we've imported a file with more details
                file_info = {
                    "filename": file,
                    "pathname": path,
                    "signal": signal,
                    "filesize": os.path.getsize(full_path)  # Get actual file size
                }

                self.fileImported.emit(file_info)

                self.channel_view_button.setEnabled(True)

                self.visualisation_page = VisualisationPage(emg_obj=self.emg_obj, import_window=self)

                self.add_file_to_recent_files(full_path)
                self.update_recent_files()

                if ext == ".mat":
                    self.segment_session = SegmentSessionPage(full_path, self.add_file_to_recent_files, self.update_recent_files)
                    self.segment_session_button.setEnabled(True)
                    self.set_configuration_button.setEnabled(False)
                else:
                    self.set_configuration_button.setEnabled(True)
                # Change file label to green if success
                self.file_info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

            except Exception as e:
                self.preview_stacked_frame.setCurrentIndex(PreviewElement.LABEL.value)
                self.preview_message.setText(f"Error loading file: {str(e)}")
                print(f"Error loading OTB+ file: {e}")
                traceback.print_exc()
                self.next_btn.setEnabled(False)
                # Change file label to red if failure
                self.file_info_label.setText(f"Failed uploading: {self.filename}")
                self.file_info_label.setStyleSheet(f"color: #FA0000; font-weight: bold;")
        else:
            self.preview_stacked_frame.setCurrentIndex(PreviewElement.LABEL.value)
            self.preview_message.setText(f"File type {ext} not supported in this demo.\nPlease select an OTB+ file.")
            self.next_btn.setEnabled(False)
            self.file_info_label.setText(f"Failed uploading: {self.filename}")
            self.file_info_label.setStyleSheet(f"color: #FA0000; font-weight: bold;")
            self.failure_message.setVisible(True)

    def update_preview_plot(self):
        signal = self.emg_obj.signal_dict
        data = signal["data"]
        chans_per_electrode = self.get_n_chans_per_electrode()
        fsamp = signal["fsamp"]

        self.preview_plot.clear()

        # Get selected electrode index
        selected_electrode_idx = self.cur_electrode_preview_idx
        if selected_electrode_idx >= len(chans_per_electrode):
            self.preview_plot.setTitle("Invalid electrode selected")
            return

        electrode_grid_name = self.emg_obj.signal_dict["gridname"][selected_electrode_idx]
        # Determine channel indices for selected electrode
        start_index = sum(chans_per_electrode[:self.cur_electrode_preview_idx])
        end_index = start_index + chans_per_electrode[self.cur_electrode_preview_idx]
        all_indices = list(range(start_index, end_index))

        # Get valid channels
        valid_indices = [i for i in range(data.shape[0]) if i not in self.emg_obj.rejected_channel_indices and i in all_indices]
        if not valid_indices:
            print("No valid channels to process.")
            return

        # Prepare temporary array for smoothed data
        tmp = np.zeros((len(valid_indices), data.shape[1]))

        # Smooth each valid channel
        for i, idx in enumerate(valid_indices):
            abs_signal = np.abs(data[idx, :])
            abs_df = pd.DataFrame(abs_signal)
            tmp[i, :] = abs_df.rolling(window=fsamp, center=True).mean().to_numpy().flatten()

        mean_trace = np.nanmean(tmp, axis=0)

        # Convert the time to seconds
        t = np.arange(len(mean_trace)) / fsamp

        # Plot the average signal
        self.preview_plot.plot(t, mean_trace, pen=pg.mkPen(color="r", width=2))

        self.preview_plot.setTitle(f"Mean HD-EMG Signal Amplitude | Electrode Grid: {selected_electrode_idx + 1} | Electrode Grid Name: {electrode_grid_name} | {len(valid_indices)} valid channels")

    def get_n_chans_per_electrode(self):
        grid_names = self.emg_obj.signal_dict["gridname"]
        chans_per_electrode = []
        for i in range(self.emg_obj.signal_dict["ngrid"]):
            if grid_names[i] == "GR04MM1305" or \
               grid_names[i] == "ELSCH064NM2" or \
               grid_names[i] == "GR08MM1305" or \
               grid_names[i] == "GR10MM0808" or \
               grid_names[i] == "other":
                chans_per_electrode.append(64)
            elif grid_names[i] == "Thin film":
                chans_per_electrode.append(40)
            elif grid_names[i] == "4-wire needle":
                chans_per_electrode.append(16)
            elif grid_names[i] == "Myomatrix Monopolar":
                chans_per_electrode.append(32)
            else:
                chans_per_electrode.append(16)

        return chans_per_electrode

    def leftClicked(self):
        new_index = self.cur_electrode_preview_idx - 1
        if new_index >= 0:
            self.cur_electrode_preview_idx = new_index
            self.update_preview_plot()
        self.update_buttons()

    def rightClicked(self):
        new_index = self.cur_electrode_preview_idx + 1
        if new_index < self.emg_obj.signal_dict["ngrid"]:
            self.cur_electrode_preview_idx = new_index
            self.update_preview_plot()
        self.update_buttons()

    def update_buttons(self):
        if self.cur_electrode_preview_idx == 0:
            self.left_button.setEnabled(False)
        else:
            self.left_button.setEnabled(True)

        if self.cur_electrode_preview_idx == self.emg_obj.signal_dict["ngrid"] - 1:
            self.right_button.setEnabled(False)
        else:
            self.right_button.setEnabled(True)

    def save_mat_in_background(self, filename, data, compression=True, processing=False):
        """Save data as .mat file in a background thread."""
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)

        worker.finished.connect(lambda: self.on_save_finished(worker))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))

        if processing:
            # Ensure segment session cannot be accessed while this happens
            self.segment_session_button.setEnabled(False)
            worker.finished.connect(self.enable_segment_session)

        worker.start()

    def on_save_finished(self, worker):
        """Handle completion of background save."""
        print("Data saved successfully")
        self.cleanup_thread(worker)

    def enable_segment_session(self):
        if self.segment_session_button and self.pathname and self.filename:
            filename = os.path.join(self.pathname, self.filename) + "_processed.mat"
            self.segment_session = SegmentSessionPage(filename, self.add_file_to_recent_files, self.update_recent_files)

            self.segment_session_button.setEnabled(True)

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
            self.decomposition_requested.emit(self.emg_obj, self.filename, self.pathname, self.imported_signal, self.config)

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

    def connect_signals(self):
        """Connect all UI signals to their handlers."""
        # Left panel connections
        self.set_configuration_button.clicked.connect(self.set_configuration_button_pushed)
        self.segment_session_button.clicked.connect(self.segment_session_button_pushed)
        self.channel_view_button.clicked.connect(self.open_channel_viewer)

    def open_channel_viewer(self):
        """Open the Channel Viewer window with the current EMG data"""
        if not self.emg_obj or "data" not in self.emg_obj.signal_dict:
            print("No EMG data loaded for channel viewer.")
            return

        try:
            # Handle persistance - if channel viewer has already been opened,
            # open the same viewer (not a new instance)
            if self.visualisation_page is not None:
                self.visualisation_page.show()
            else:
                self.visualisation_page = VisualisationPage(emg_obj=self.emg_obj, import_window=self)
                self.visualisation_page.show()
        except Exception as e:
            print(f"Failed to load channel viewer: {e}")

    def config_callback(self, signal):
        if self.pathname and self.filename and self.emg_obj:
            filename = os.path.join(self.pathname, self.filename) + "_processed.mat"

            # Update emg object and signal
            self.emg_obj.signal_dict = signal
            self.imported_signal = self.emg_obj.signal_dict

            # Update channel viewer
            self.visualisation_page = VisualisationPage(emg_obj=self.emg_obj, import_window=self)

            # Create new processed data file
            self.save_mat_in_background(filename, {"signal": self.imported_signal}, True, True)

    def set_configuration_button_pushed(self):
        if self.config_panel:
            try:
                self.config_panel.set_config_callback(self.config_callback)

                # Show the dialog
                self.config_panel.show()
            except Exception as e:
                print(f"Error showing configuration dialog: {e}")
                traceback.print_exc()
        else:
            print("No configuration dialog available")

    def segment_session_button_pushed(self):
        if not self.emg_obj or "data" not in self.emg_obj.signal_dict or not self.pathname or not self.filename:
            self.edit_field.setText("No EMG data loaded for segment session.")
            return

        try:
            # Handle persistance - if segment session has already been opened,
            # open the same panel (not a new instance)
            if self.segment_session is not None:
                self.segment_session.show()
        except Exception as e:
            self.edit_field.setText(f"Failed to load segment session: {e}")

    def add_file_to_recent_files(self, filename):
        if filename not in self.recent_files:
            self.recent_files.append(filename)
        else:
            self.recent_files.remove(filename)
            self.recent_files = [filename] + self.recent_files

    def update_recent_files(self):
        if hasattr(self, "update_sidebar_with_recent_files"):
            self.update_sidebar_with_recent_files()


# For testing the window independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportDataWindow()
    window.show()
    sys.exit(app.exec_())
