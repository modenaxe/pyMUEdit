import json
from pathlib import Path
import sys
import os
import traceback
import zipfile
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtMultimedia import QSound
import numpy as np
import pandas as pd
import pyqtgraph as pg

# Import UI setup function
from core.database.database import create_new_session, get_fileid_by_path, get_or_create_session_for_file, get_session_files, insert_files, upsert_file_versions
from core.utils.io.filesize_formatter import filesize_formatter
from core.utils.session.convert_h5 import load_from_h5, save_as_h5
from core.utils.io.filesize_formatter import filesize_formatter
from ui.ImportDataWindowUI import setup_ui, update_sidebar_selection
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

####import from dashboard.py
import sys
import traceback
import os
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QPushButton, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

# Import for external windows/widgets
from app.ExportResults import ExportResultsWindow
from app.DecompositionApp import DecompositionApp
from ui.MUAnalysisUI import MUAnalysis
from MUeditManual import MUeditManual  # Import MUeditManual class

class PreviewElement(Enum):
    LABEL = 0
    GRAPH = 1


class ImportDataWindow(QMainWindow):
    # Signal to notify the main window to return to dashboard
    return_to_dashboard_requested = pyqtSignal()

    # Signal to request showing decomposition view with data
    decomposition_requested = pyqtSignal(object, str, str, object, object, int)

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

        self.raw_fileid = None
        self.sessionid = None
        # Config popup windows
        self.visualisation_page = None
        self.segment_session = None
        self.config_panel = None

        self.recent_visualizations = []
        self.recent_datasets = []

        self.initialize_external_widgets()

        # Create EMG object using the appropriate class
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.emg_obj = EMG_offline_EMG(save_dir=temp_dir, to_filter=True)

        # Sample recent files list (could be loaded from settings/history)
        self.recent_files = []

        # Set up the UI using our improved UI setup
        self.import_data_ui = setup_ui(self)

         # Now create the manual editing view
        self.create_manual_editing_view()

        # Connect signals for configration buttons
        self.connect_signals()

        self.show_import_data_view()
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


    def export_session(self):
        if not self.sessionid:
            print("Warning: No session has been initialised")
            return False

        session_files = get_session_files(self.sessionid)
        print(session_files)
        if not session_files:
            print("No files in this session to export")
            return False

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path, _ = QFileDialog.getSaveFileName(
            None,
            "Export Session",
            f"Session_{timestamp}.zip",
            "Zip Files (*.zip);;All Files (*)"
        )

        if save_path:
            file_paths_to_zip = []
            for file in session_files:
                for version in file.get("versions", []):
                    version_path = version.get("version_filepath")
                    if version_path and os.path.exists(version_path):
                        file_paths_to_zip.append(version_path)

            if not file_paths_to_zip:
                print("No valid files found to zip")
                return False

            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filepath in file_paths_to_zip:
                    arcname = os.path.basename(filepath)
                    zipf.write(filepath, arcname)
                    print(f"Added {filepath} as {arcname}")

            print(f"Session exported successfully to {save_path}")
            return True
        else:
            print("Export cancelled")

    def load_session(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select session .zip File", "", "ZIP Files (*.zip)"
        )

        zip_path = Path(file)
        zip_name = zip_path.stem

        extract_dir = Path("..") / "loaded_sessions" / zip_name
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

            readin_name = None
            decomp_name = None

            for name in zip_ref.namelist():
                if name.endswith("_readin.h5"):
                    readin_name = name
                elif name.endswith("_decomp.h5"):
                    decomp_name = name

            if readin_name:
                readin_path = extract_dir / readin_name
                self.update_ui_for_file(readin_path, readin_name)

            if decomp_name:
                decomp_path = extract_dir / decomp_name
                signal_dict, raw_filepath, config_dict = load_from_h5(str(decomp_path))
                self.decomposition_requested.emit(self.emg_obj, self.filename, self.pathname, self.imported_signal, config_dict, self.raw_fileid)
                self.decomp_app.on_decomposition_complete_2(signal_dict)

            print(f"Files extracted to: {extract_dir}")

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

    def play_error_popup(self, title, message):
        try:
            QApplication.beep()
        except Exception:
            pass
        QMessageBox.critical(self, title, message, QMessageBox.Ok)

    def load_file(self, path, file):
        """Load and process a file."""
        self.preview_message.setText("Loading file...")
        ext = os.path.splitext(file)[1].lower()

        # Reset failure messages
        self.failure_message.setVisible(False)

        if ext == ".otb+" or ext == ".mat" or ext == ".h5":
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

                    base_name = os.path.splitext(file)[0]

                    # Create a default save name for .mat files
                    savename = os.path.join(path, f"{base_name}_processed.mat")
                    h5_readin_savename = os.path.join(path, f"{base_name}_readin.h5")

                    # Save the data as a .mat file in the background
                    if self.emg_obj.signal_dict:
                        self.save_mat_in_background(savename, {"signal": self.emg_obj.signal_dict}, True, True)
                        save_as_h5(self.emg_obj.signal_dict, h5_readin_savename, raw_filepath=full_path)

                elif ext == '.mat':
                    # Call the open_otb_plus function with the correct parameters
                    self.emg_obj.open_mat(full_path)

                    base_name = os.path.splitext(file)[0]
                    savename = os.path.join(path, f"{base_name}_processed.mat")
                    h5_readin_savename = os.path.join(path, f"{base_name}_readin.h5")

                    try:
                        if self.emg_obj.signal_dict:
                            save_as_h5(self.emg_obj.signal_dict, h5_readin_savename)
                    except Exception as e:
                        print(f"Error saving .h5 file: {e}")

                elif ext == ".h5":
                    full_path = os.path.join(path, file)
                    try:
                        signal_dict, raw_filepath, config_dict = load_from_h5(full_path)
                        self.emg_obj.signal_dict = signal_dict
                        self.imported_signal = signal_dict
                        self.raw_file_path = raw_filepath

                        if "data" in signal_dict and "fsamp" in signal_dict:
                            self.cur_electrode_preview_idx = 0
                            self.update_preview_plot()
                            self.update_buttons()

                        self.file_info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                        self.next_btn.setEnabled(True)

                    except Exception as e:
                        self.preview_stacked_frame.setCurrentIndex(PreviewElement.LABEL.value)
                        self.preview_message.setText(f"Error loading H5 file: {str(e)}")
                        self.play_error_popup("Error loading file", str(e))
                        traceback.print_exc()
                        self.next_btn.setEnabled(False)
                        self.file_info_label.setStyleSheet(f"color: #FA0000; font-weight: bold;")

                    fileid = None # temp
                # Store the imported signal
                signal = self.emg_obj.signal_dict
                self.imported_signal = signal
                print(signal)

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
                    "filesize": os.path.getsize(full_path),  # Get actual file size
                    "fileid": self.raw_fileid
                }

                self.fileImported.emit(file_info)

                self.channel_view_button.setEnabled(True)

                self.add_file_to_recent_files(full_path)
                self.update_recent_files()

                if ext == ".mat":
                    self.segment_session = SegmentSessionPage(full_path, self.add_file_to_recent_files, self.update_recent_files, self.raw_fileid)
                    self.segment_session_button.setEnabled(True)
                    self.set_configuration_button.setEnabled(False)
                else:
                    self.set_configuration_button.setEnabled(True)

                # Change file label to green if success
                self.file_info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

                # Get or create session for this dataset
                if ext != ".h5": # temporary dont create session with h5 for now due to using load_file for loading a session
                    sessionid = get_or_create_session_for_file(full_path)
                    self.sessionid = sessionid
                    fileid = get_fileid_by_path(full_path)
                    if not fileid:
                        fileid = insert_files(full_path, file, sessionid)

                    upsert_file_versions(h5_readin_savename, fileid, "readin")

                self.raw_fileid = fileid

            except Exception as e:
                self.preview_stacked_frame.setCurrentIndex(PreviewElement.LABEL.value)
                self.preview_message.setText(f"Error loading file: {str(e)}")
                self.play_error_popup("Error loading file", str(e))
                print(f"Error loading OTB+ file: {e}")
                traceback.print_exc()
                self.next_btn.setEnabled(False)
                # Change file label to red if failure
                self.file_info_label.setText(f"Failed uploading: {self.filename}")
                self.file_info_label.setStyleSheet(f"color: #FA0000; font-weight: bold;")
        else:
            self.preview_stacked_frame.setCurrentIndex(PreviewElement.LABEL.value)
            self.preview_message.setText(f"File type {ext} not supported in this demo.\nPlease select an OTB+ file.")
            self.play_error_popup(f"File type error", f"File type {ext} not supported in this demo.\nPlease select an OTB+ file.")
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
            base_name = os.path.splitext(self.filename)[0]
            filename = os.path.join(self.pathname, f"{base_name}_processed.mat")
            self.segment_session = SegmentSessionPage(filename, self.add_file_to_recent_files, self.update_recent_files, self.raw_fileid)

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
            self.decomposition_requested.emit(self.emg_obj, self.filename, self.pathname, self.imported_signal, self.config, self.raw_fileid)

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

        # Connect sidebar buttons
        self.sidebar_buttons["mu_analysis"].clicked.connect(self.show_mu_analysis_view)
        self.sidebar_buttons["decomposition"].clicked.connect(self.show_decomposition_view)
        self.sidebar_buttons["manual_edit"].clicked.connect(self.show_manual_editing_view)
        self.sidebar_buttons["import"].clicked.connect(self.show_import_data_view)

        if not MUAnalysis:
            self.sidebar_buttons["mu_analysis"].setEnabled(False)

        self.decomposition_requested.connect(self.create_decomposition_view)

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

    def select_mu_edit_subpage(self, index:int):
        if hasattr(self, "mu_edit_stack"):
            self.mu_edit_stack.setCurrentIndex(index)

    def initialize_external_widgets(self):
        """Initialize external widgets if their modules are available."""
        # Initialize MU Analysis page
        if MUAnalysis:
            self.mu_analysis_page = MUAnalysis()
            self.mu_analysis_page.return_to_dashboard_requested.connect(self.show_import_data_view)
            if hasattr(self.mu_analysis_page, "set_export_window_opener"):
                self.mu_analysis_page.set_export_window_opener(self.open_export_results_window)
            else:
                print("WARNING: MotorUnitAnalysisWidget does not have 'set_export_window_opener' method.")

        if DecompositionApp:
            self.decomposition_page = DecompositionApp()
            self.decomposition_page.setWindowFlags(getattr(Qt.WindowType, "Widget"))


        # Note: Manual Editing page is now created after setup_ui in __init__

    def handle_file_imported(self, file_info):
        """
        Handle the fileImported signal from the ImportDataWindow
        """
        print(f"Dashboard received fileImported signal for {file_info.get('filename')}")
        # Extract information from the signal
        filename = file_info.get("filename", "Unknown file")
        pathname = file_info.get("pathname", "")
        filesize = file_info.get("filesize", None)

        # Add to recent datasets
        self.add_recent_dataset(filename, pathname, filesize)

    def create_import_view(self):
        try:
            # Create a wrapper widget to hold the import view
            wrapper = QWidget()
            wrapper.setObjectName("import_data_page_wrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)

            # Initialize Import Data page
            import_page = ImportDataWindow(parent=self)

            # Set window flags to make it a widget instead of a window
            import_page.setWindowFlags(Qt.WindowType.Widget)

            # Connect the new signal for decomposition
            if hasattr(import_page, "decomposition_requested"):
                import_page.decomposition_requested.connect(self.create_decomposition_view)
            # Connect the fileImported signal to our recent datasets function
            if hasattr(import_page, "fileImported"):
                import_page.fileImported.connect(self.handle_file_imported)

            # Add to layout
            wrapper_layout.addWidget(import_page)

            # Replace the placeholder with our real import view
            self.import_data_page = wrapper

            # Add the wrapper to the stacked widget
            self.central_stacked_widget.addWidget(wrapper)

        except Exception as e:
            print(f"Error creating import view: {e}")
            traceback.print_exc()

    def create_manual_editing_view(self):
        """Creates a manual editing view and adds it to the stacked widget."""
        try:
            print("Creating manual editing view")

            # Create a wrapper widget to hold the MUeditManual
            # wrapper = QWidget()
            # wrapper.setObjectName("manual_editing_wrapper")
            # wrapper_layout = QVBoxLayout(wrapper)
            # wrapper_layout.setContentsMargins(0, 0, 0, 0)
            # wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

            # Create MUeditManual instance
            manual_edit_app = MUeditManual()

            # Set window flags to make it a widget instead of a window
            # manual_edit_app.setWindowFlags(Qt.WindowType.Widget)

            self.mu_edit_tabs = manual_edit_app.tabs
            # Connect return signal if available
            # if hasattr(manual_edit_app, "return_to_dashboard_requested"):
            #     manual_edit_app.return_to_dashboard_requested.connect(self.show_dashboard_view)

            # Add to layout
            # wrapper_layout.addWidget(manual_edit_app)

            # Replace the placeholder with our real manual editing view
            self.manual_editing_page = manual_edit_app

            # Add the wrapper to the stacked widget
            self.central_stacked_widget.addWidget(manual_edit_app)

        except Exception as e:
            print(f"Error creating manual editing view: {e}")
            traceback.print_exc()

    def create_decomposition_view(self, emg_obj, filename, pathname, imported_signal, config, raw_fileid):
        """Creates a decomposition view with the provided data and adds it to the stacked widget."""
        try:
            print("Creating decomposition view with provided data")

            # Create a wrapper widget to hold the DecompositionApp
            wrapper = QWidget()
            wrapper.setObjectName("decomposition_wrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)

            # Create DecompositionApp instance
            self.decomp_app = DecompositionApp(
                emg_obj=emg_obj,
                filename=filename,
                pathname=pathname,
                imported_signal=imported_signal,
                config=config,
                raw_fileid=raw_fileid,
                parent=self,  # Set parent for proper widget hierarchy
            )

            # Set window flags to make it a widget instead of a window
            self.decomp_app.setWindowFlags(Qt.WindowType.Widget)

            # Add to layout
            wrapper_layout.addWidget(self.decomp_app)

            # Connect back button to show import view
            if hasattr(self.decomp_app, "back_to_import_btn"):
                self.decomp_app.back_to_import_btn.clicked.connect(self.show_import_data_view)

            # Replace the placeholder with our real decomposition view
            self.decomposition_page = wrapper

            # Remove the old placeholder if it exists
            for i in range(self.central_stacked_widget.count()):
                widget = self.central_stacked_widget.widget(i)
                if widget and (
                    widget.objectName() == "decomposition_placeholder"
                    or (hasattr(widget, "objectName") and widget.objectName() == "decomposition_placeholder")
                ):
                    self.central_stacked_widget.removeWidget(widget)
                    break

            # Add the wrapper to the stacked widget
            self.central_stacked_widget.addWidget(wrapper)

            # Show the decomposition view
            self.show_decomposition_view()

        except Exception as e:
            print(f"Error creating decomposition view: {e}")
            traceback.print_exc()

    def show_mu_analysis_view(self):
        """Switches the central widget to the MU Analysis page."""
        if hasattr(self, "mu_analysis_page") and self.mu_analysis_page:
            print("Switching to MU Analysis View")
            self.central_stacked_widget.setCurrentWidget(self.mu_analysis_page)
            update_sidebar_selection(self, "mu_analysis")
        else:
            print("MU Analysis view is not available.")

    def show_import_data_view(self):
        """Switches the central widget to the Import Data page."""
        print("Switching to Import Data view")
        if hasattr(self, "import_data_page") and self.import_data_page:
            self.central_stacked_widget.setCurrentWidget(self.import_data_page)
            update_sidebar_selection(self, "import")
        else:
            print("ImportDataWindow not available.")

    def show_manual_editing_view(self):
        """Switches to Manual Editing view."""
        print("Switching to Manual Editing View")
        if hasattr(self, "manual_editing_page") and self.manual_editing_page:
            self.central_stacked_widget.setCurrentWidget(self.manual_editing_page)
            update_sidebar_selection(self, "manual_edit")
        else:
            print("Manual Editing view widget not found.")

    def show_decomposition_view(self):
        """Switches to Decomposition view."""
        print("Switching to Decomposition View")
        if hasattr(self, "decomposition_page") and self.decomposition_page:
            self.central_stacked_widget.setCurrentWidget(self.decomposition_page)
            update_sidebar_selection(self, "decomposition")
        else:
            print("Decomposition view widget not found.")

    def open_export_results_window(self):
        """Opens the Export Results window, creating it if necessary."""
        print(">>> Main Window: Request received to open Export Results window.")
        if ExportResultsWindow is None:
            print("ERROR: ExportResultsWindow class is not available (check import).")
            return

        window_exists = False
        if self.export_results_window:
            try:
                # Check if the window still exists and hasn't been closed/deleted
                if self.export_results_window.isVisible() or not self.export_results_window.isHidden():
                    window_exists = True
                    print(">>> Main Window: Existing ExportResultsWindow instance seems valid.")
                else:
                    print(
                        ">>> Main Window: Existing window reference present but window is hidden/closed; will create new."
                    )
                    self.export_results_window = None  # Force recreation
                    window_exists = False
            except RuntimeError:  # Window was likely deleted
                print(">>> Main Window: Existing window reference invalid (RuntimeError); will create new.")
                self.export_results_window = None
                window_exists = False
            except Exception as e:  # Catch other potential issues
                print(f">>> Main Window: Error checking existing window ({type(e).__name__}); will create new.")
                self.export_results_window = None
                window_exists = False

        if not window_exists:
            try:
                print(">>> Main Window: Creating NEW ExportResultsWindow instance.")
                # Ensure it's created as a top-level window (parent=None)
                self.export_results_window = ExportResultsWindow(parent=None)
                # Position it relative to the main window for convenience
                main_geo = self.geometry()
                new_x = main_geo.x() + 100
                new_y = main_geo.y() + 100
                width = 600  # Define desired size
                height = 550
                self.export_results_window.setGeometry(new_x, new_y, width, height)
                print(f">>> Set geometry for new window to ({new_x}, {new_y}, {width}, {height})")
            except Exception as e:
                print(f"FATAL ERROR during ExportResultsWindow creation: {e}")
                traceback.print_exc()
                self.export_results_window = None  # Ensure it's None if creation failed
                return  # Stop execution here

        # After potentially creating or confirming existence, try to show/activate
        if self.export_results_window:
            try:
                print(">>> Main Window: Attempting to show and activate ExportResultsWindow.")
                self.export_results_window.show()
                self.export_results_window.raise_()  # Bring to front
                self.export_results_window.activateWindow()  # Give focus
                QApplication.processEvents()  # Ensure UI updates
                print(">>> ExportResultsWindow shown and activated.")
            except RuntimeError:  # Catch if window was deleted between check and show
                print(">>> Error: ExportResultsWindow was deleted before it could be shown.")
                self.export_results_window = None
            except Exception as e:
                print(f"Error displaying/activating ExportResultsWindow: {e}")
                traceback.print_exc()
        else:
            print("ERROR - self.export_results_window is None even after creation attempt.")

    def update_ui_for_file(self, full_path, filename):
        self.filename = filename
        self.pathname = os.path.dirname(full_path) + "/"

        self.file_info_label.setText(f"Selected: {filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {filename}")

        try:
            size_str = filesize_formatter(full_path)
            self.size_info.setText(f"Size: {size_str}")
        except:
            self.size_info.setText("Size: --")
        ext = os.path.splitext(filename)[1].upper().replace('.', '')
        self.format_info.setText(f"Format: {ext}")

        self.load_file(os.path.dirname(full_path), filename)

# For testing the window independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportDataWindow()
    window.show()
    sys.exit(app.exec_())
