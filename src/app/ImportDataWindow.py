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
from core.utils.config_and_input.filesize_formatter import filesize_formatter
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

        self.recent_visualizations = []
        self.recent_datasets = []

        self.load_saved_states()

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

    def select_mu_edit_subpage(self, index:int):
        if hasattr(self, "mu_edit_stack"):
            self.mu_edit_stack.setCurrentIndex(index)

    def initialize_external_widgets(self):
        """Initialize external widgets if their modules are available."""
        # Initialize MU Analysis page
        if MUAnalysis:
            self.mu_analysis_page = MUAnalysis()
            self.mu_analysis_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
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

            if hasattr(import_page, "return_to_dashboard_requested"):
                import_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
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
            if hasattr(manual_edit_app, "return_to_dashboard_requested"):
                manual_edit_app.return_to_dashboard_requested.connect(self.show_dashboard_view)

            # Add to layout
            # wrapper_layout.addWidget(manual_edit_app)

            # Replace the placeholder with our real manual editing view
            self.manual_editing_page = manual_edit_app

            # Add the wrapper to the stacked widget
            self.central_stacked_widget.addWidget(manual_edit_app)

        except Exception as e:
            print(f"Error creating manual editing view: {e}")
            traceback.print_exc()

    def create_decomposition_view(self, emg_obj, filename, pathname, imported_signal, config):
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

    # def connect_signals(self):
    #     """Connect UI signals to slot methods."""
    #     # Connect sidebar buttons
    #     self.sidebar_buttons["dashboard"].clicked.connect(self.show_dashboard_view)
    #     self.sidebar_buttons["mu_analysis"].clicked.connect(self.show_mu_analysis_view)
    #     self.sidebar_buttons["decomposition"].clicked.connect(self.show_decomposition_view)
    #     self.sidebar_buttons["manual_edit"].clicked.connect(self.show_manual_editing_view)
    #     self.sidebar_buttons["import"].clicked.connect(self.show_import_data_view)

    #     if not MUAnalysis:
    #         self.sidebar_buttons["mu_analysis"].setEnabled(False)

    #     # Connect "New Analysis" button on the dashboard
    #     new_viz_btn = None
    #     content_widget = self.dashboard_page.widget()
    #     if content_widget and content_widget.layout():
    #         for layout_idx in range(content_widget.layout().count()):
    #             item = content_widget.layout().itemAt(layout_idx)
    #             if item and isinstance(item.layout(), QHBoxLayout):
    #                 for i in range(item.layout().count()):
    #                     layout_item = item.layout().itemAt(i)
    #                     if layout_item and layout_item.widget():
    #                         widget = layout_item.widget()
    #                         if isinstance(widget, QPushButton) and widget.text() == "+ New Analysis":
    #                             new_viz_btn = widget
    #                             break
    #             if new_viz_btn:
    #                 break

    #     if new_viz_btn and ImportDataWindow:
    #         new_viz_btn.clicked.connect(self.show_import_data_view)

    # Navigation methods
    def show_dashboard_view(self):
        """Switches the central widget to the dashboard page."""
        print("Switching to Dashboard View")

        # Store the current index of the dashboard page
        old_dashboard = self.dashboard_page
        old_index = self.central_stacked_widget.indexOf(old_dashboard)

        # Create a new dashboard page
        from ui.HDEMGDashboardUI import _create_dashboard_page
        self.dashboard_page = _create_dashboard_page(self)

        # Replace the old dashboard with the new one
        if old_index >= 0:
            self.central_stacked_widget.removeWidget(old_dashboard)
            self.central_stacked_widget.insertWidget(old_index, self.dashboard_page)
        else:
            self.central_stacked_widget.addWidget(self.dashboard_page)

        # Show the new dashboard
        self.central_stacked_widget.setCurrentWidget(self.dashboard_page)

        # Update sidebar selection
        from ui.HDEMGDashboardUI import update_sidebar_selection
        update_sidebar_selection(self, "dashboard")

        # Schedule old dashboard for deletion to avoid memory leaks
        if old_dashboard is not None and old_dashboard != self.dashboard_page:
            old_dashboard.deleteLater()

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

    def open_visualization(self, title):
        """Handles clicks on visualization cards."""
        print(f"Clicked visualization/analysis card: {title}")
        # Map visualization titles to corresponding views
        if "HDEMG Analysis" in title and hasattr(self, "mu_analysis_page") and self.mu_analysis_page:
            self.show_mu_analysis_view()
        else:
            print(f"No specific action defined for card '{title}'. Staying on Dashboard.")

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

    def load_saved_states(self):
        """
        Load saved decomposition states into recent visualizations.
        Called during initialization to populate the dashboard with saved visualizations.
        """
        from core.utils.decomposition_state import DecompositionState

        # Get saved states
        try:
            saved_states = DecompositionState.list_saved_states()

            # Convert to visualization data format
            self.recent_visualizations = []
            for i, state in enumerate(saved_states[:5]):  # Limit to 5 most recent
                timestamp = datetime.datetime.fromtimestamp(state['timestamp'])
                date_str = timestamp.strftime("Last modified: %b %d, %Y")

                self.recent_visualizations.append({
                    'title': state.get('title', f"Analysis {i+1}"),
                    'date': date_str,
                    'type': 'hdemg',
                    'icon': 'visualization_icon',
                    'state_path': state['state_path'],
                    'motor_units_count': state.get('motor_units_count', '?'),
                })
        except Exception as e:
            print(f"Error loading saved states: {e}")
            import traceback
            traceback.print_exc()
            self.recent_visualizations = []

    def add_recent_visualization(self, state_meta):
        """
        Add a new visualization to the dashboard's recent list.
        Called by DecompositionApp when decomposition completes.
        """
        # Get timestamp in user-friendly format
        timestamp = datetime.datetime.fromtimestamp(state_meta['timestamp'])
        date_str = timestamp.strftime("Last modified: %b %d, %Y")

        # Create visualization metadata
        viz_data = {
            'title': state_meta['title'],
            'date': date_str,
            'type': 'hdemg',
            'icon': 'visualization_icon',
            'state_path': state_meta['state_path'],
            'motor_units_count': state_meta['motor_units_count'],
        }

        # Add to recent visualizations list
        if not hasattr(self, 'recent_visualizations'):
            self.recent_visualizations = []

        # Insert at the beginning and limit to 5 items
        self.recent_visualizations.insert(0, viz_data)
        self.recent_visualizations = self.recent_visualizations[:5]

        # Update the UI if dashboard is visible
        if hasattr(self, 'central_stacked_widget') and self.central_stacked_widget.currentWidget() == self.dashboard_page:
            self.show_dashboard_view()  # Refresh to show the new visualization

    def on_visualization_card_clicked(self, card_index):
        """
        Handle clicks on visualization cards in the dashboard.

        Args:
            card_index: Index of the clicked card in recent_visualizations list
        """
        print(f"Visualization card clicked: index={card_index}")
        if hasattr(self, 'recent_visualizations') and 0 <= card_index < len(self.recent_visualizations):
            viz_data = self.recent_visualizations[card_index]
            if 'state_path' in viz_data and os.path.exists(viz_data['state_path']):
                self.load_visualization(viz_data['state_path'])
            else:
                # Fallback to original behavior
                self.open_visualization(viz_data.get('title', ''))

    def load_visualization(self, state_path):
        """
        Load a saved visualization state and display it.

        Args:
            state_path: Path to the saved state file
        """
        from core.utils.decomposition_state import DecompositionState
        import pyqtgraph as pg
        from PyQt5.QtWidgets import QWidget, QVBoxLayout
        from core.EmgDecomposition import offline_EMG

        try:
            # Load the state
            state = DecompositionState.load_state(state_path)

            # Create a new DecompositionApp instance
            from app.DecompositionApp import DecompositionApp
            decomp_app = DecompositionApp(parent=self)

            # Set data from the state
            decomp_app.filename = state['filename']
            decomp_app.pathname = state['pathname']
            decomp_app.ui_params = state['ui_params']
            decomp_app.decomposition_result = state.get('decomposition_result')

            # Reconstruct EMG object for channel viewer if data is available
            if state.get('emg_data') and state['emg_data'].get('data') is not None:
                try:
                    # Create a minimal EMG object for channel viewer
                    emg_data = state['emg_data']
                    decomp_app.emg_obj = offline_EMG(save_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp"), to_filter=True)
                    decomp_app.emg_obj.signal_dict = {
                        'data': emg_data['data'],
                        'fsamp': emg_data['fsamp'],
                        'nChan': emg_data['nChan'],
                        'electrodes': emg_data['electrodes'],
                    }
                    print(f"Restored EMG data for channel viewer: shape={emg_data['data'].shape}")
                except Exception as e:
                    print(f"Warning: Failed to restore EMG object: {e}")

            # Update file info display
            if hasattr(decomp_app, 'update_ui_with_loaded_data'):
                decomp_app.update_ui_with_loaded_data()

            # Update UI elements
            decomp_app.edit_field.setText("Restored previous decomposition")
            decomp_app.save_output_button.setEnabled(True)
            decomp_app.next_button.setEnabled(True)
            decomp_app.status_text.setText("Complete")
            decomp_app.status_progress.setValue(100)

            if state.get('motor_units_count'):
                decomp_app.motor_units_label.setText(f"Motor Units: {state['motor_units_count']}")
            if state.get('sil_value'):
                decomp_app.sil_value_label.setText(f"SIL: {state['sil_value']}")
            if state.get('cov_value'):
                decomp_app.cov_value_label.setText(f"CoV: {state['cov_value']}")

            # ======== Reconstruct the plots from the saved state ========

            # Current plot data for any callbacks that might need it
            if state.get('current_plot_data'):
                decomp_app.current_plot_data = state['current_plot_data']

            # Reconstruct plot data from saved state
            plot_data = state.get('plot_data', {})

            # Reconstruct reference plot
            if 'reference' in plot_data and plot_data['reference']:
                self._reconstruct_plot(decomp_app.ui_plot_reference, plot_data['reference'])

            # Reconstruct pulse train plot
            if 'pulsetrain' in plot_data and plot_data['pulsetrain']:
                self._reconstruct_plot(decomp_app.ui_plot_pulsetrain, plot_data['pulsetrain'])

            # Enable buttons
            decomp_app.start_button.setEnabled(True)

            # Create a wrapper widget to hold the DecompositionApp
            wrapper = QWidget()
            wrapper.setObjectName("decomposition_wrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.addWidget(decomp_app)

            # Store the wrapper as the decomposition page
            self.decomposition_page = wrapper

            # Add it to the stacked widget if needed
            if hasattr(self, 'central_stacked_widget'):
                # Remove old decomposition page if it exists
                for i in range(self.central_stacked_widget.count()):
                    widget = self.central_stacked_widget.widget(i)
                    if widget and widget.objectName() == "decomposition_wrapper":
                        self.central_stacked_widget.removeWidget(widget)
                        break

                # Add the new one
                self.central_stacked_widget.addWidget(wrapper)

                # Switch to it
                self.show_decomposition_view()

            print(f"Successfully loaded visualization from {state_path}")
        except Exception as e:
            print(f"Error loading visualization: {e}")
            import traceback
            traceback.print_exc()

    def _reconstruct_plot(self, plot_widget, plot_data):
        """
        Reconstructs a plot from saved plot data

        Args:
            plot_widget: PyQtGraph PlotWidget to populate
            plot_data: Dictionary of plot data from the state
        """
        import pyqtgraph as pg
        from PyQt5.QtCore import Qt

        # Clear the plot
        plot_widget.clear()

        # Set plot title if available
        if plot_data.get('title'):
            plot_widget.setTitle(plot_data['title'])

        # Reconstruct each item in the plot
        for item in plot_data.get('items', []):
            item_type = item.get('type')

            if item_type == 'plot':
                # Recreate line plot
                x_data = item.get('x_data')
                y_data = item.get('y_data')

                if x_data is not None and y_data is not None:
                    # Create pen from saved settings
                    pen_data = item.get('pen', {})

                    try:
                        # Get the color, defaulting to black
                        color = pen_data.get('color', '#000000')
                        if color is None:
                            color = '#000000'  # Force black if None was saved

                        width = pen_data.get('width', 1)
                        if width is None:
                            width = 1  # Force width 1 if None was saved

                        # Create the pen
                        pen = pg.mkPen(color=color, width=width)

                        # Add style if it was saved
                        if pen_data.get('style') == 'dash':
                            pen.setStyle(Qt.PenStyle.DashLine)
                    except Exception as e:
                        print(f"Error creating pen, using default black: {e}")
                        # Default to simple black pen
                        pen = pg.mkPen(color='k', width=1)

                    # Create the plot item
                    plot_widget.plot(x_data, y_data, pen=pen)

            elif item_type == 'infinite_line':
                # Recreate vertical or horizontal line (plateau markers)
                pos = item.get('pos')
                angle = item.get('angle', 90)

                if pos is not None:
                    # Create pen from saved settings
                    pen_data = item.get('pen', {})

                    # Use a more compatible way to create the pen
                    try:
                        # Method 1: Create pen with color and width
                        color = pen_data.get('color', '#FF0000')
                        width = pen_data.get('width', 2)

                        # Ensure width is not None
                        if width is None:
                            width = 2

                        pen = pg.mkPen(color=color, width=width)
                    except Exception as e:
                        print(f"Error creating pen, using default: {e}")
                        pen = pg.mkPen(color='r', width=2)  # Default to simple red pen

                    # Create the line
                    line = pg.InfiniteLine(pos=pos, angle=angle, pen=pen)
                    plot_widget.addItem(line)

            elif item_type == 'scatter':
                # Recreate scatter plot (spikes)
                x_data = item.get('x_data')
                y_data = item.get('y_data')

                if x_data is not None and y_data is not None and len(x_data) == len(y_data):
                    try:
                        # Create the scatter plot safely
                        size = item.get('size', 10)
                        brush_color = item.get('brush', '#FF0000')

                        scatter = pg.ScatterPlotItem(
                            x=x_data,
                            y=y_data,
                            size=size,
                            pen=None,  # No border pen
                            brush=pg.mkBrush(brush_color)
                        )
                    except Exception as e:
                        print(f"Error creating scatter plot, using simplified version: {e}")
                        # Fallback to simpler construction
                        scatter = pg.ScatterPlotItem(pos=list(zip(x_data, y_data)))
                    plot_widget.addItem(scatter)

        # Set axis ranges if available
        if plot_data.get('x_range'):
            plot_widget.setXRange(*plot_data['x_range'])

        if plot_data.get('y_range'):
            plot_widget.setYRange(*plot_data['y_range'])

    def _reconstruct_plot(self, plot_widget, plot_data):
        """
        Reconstructs a plot from saved plot data

        Args:
            plot_widget: PyQtGraph PlotWidget to populate
            plot_data: Dictionary of plot data from the state
        """
        import pyqtgraph as pg
        from PyQt5.QtCore import Qt

        # Clear the plot
        plot_widget.clear()

        # Set plot title if available
        if plot_data.get('title'):
            plot_widget.setTitle(plot_data['title'])

        # Reconstruct each item in the plot
        for item in plot_data.get('items', []):
            item_type = item.get('type')

            if item_type == 'plot':
                # Recreate line plot
                x_data = item.get('x_data')
                y_data = item.get('y_data')

                if x_data is not None and y_data is not None:
                    # Create pen from saved settings
                    pen_data = item.get('pen', {})

                    try:
                        # Get the color, defaulting to black
                        color = pen_data.get('color', '#000000')
                        if color is None:
                            color = '#000000'  # Force black if None was saved

                        width = pen_data.get('width', 1)
                        if width is None:
                            width = 1  # Force width 1 if None was saved

                        # Create the pen
                        pen = pg.mkPen(color=color, width=width)

                        # Add style if it was saved
                        if pen_data.get('style') == 'dash':
                            pen.setStyle(Qt.PenStyle.DashLine)
                    except Exception as e:
                        print(f"Error creating pen, using default black: {e}")
                        # Default to simple black pen
                        pen = pg.mkPen(color='k', width=1)

                    # Create the plot item
                    plot_widget.plot(x_data, y_data, pen=pen)

            elif item_type == 'infinite_line':
                # Recreate vertical or horizontal line (plateau markers)
                pos = item.get('pos')
                angle = item.get('angle', 90)

                if pos is not None:
                    # Create pen from saved settings
                    pen_data = item.get('pen', {})

                    # Use a more compatible way to create the pen
                    try:
                        # Method 1: Create pen with color and width
                        color = pen_data.get('color', '#FF0000')
                        width = pen_data.get('width', 2)

                        # Ensure width is not None
                        if width is None:
                            width = 2

                        pen = pg.mkPen(color=color, width=width)
                    except Exception as e:
                        print(f"Error creating pen, using default: {e}")
                        pen = pg.mkPen(color='r', width=2)  # Default to simple red pen

                    # Create the line
                    line = pg.InfiniteLine(pos=pos, angle=angle, pen=pen)
                    plot_widget.addItem(line)

            elif item_type == 'scatter':
                # Recreate scatter plot (spikes)
                x_data = item.get('x_data')
                y_data = item.get('y_data')

                if x_data is not None and y_data is not None and len(x_data) == len(y_data):
                    try:
                        # Create the scatter plot safely
                        size = item.get('size', 10)
                        brush_color = item.get('brush', '#FF0000')

                        scatter = pg.ScatterPlotItem(
                            x=x_data,
                            y=y_data,
                            size=size,
                            pen=None,  # No border pen
                            brush=pg.mkBrush(brush_color)
                        )
                    except Exception as e:
                        print(f"Error creating scatter plot, using simplified version: {e}")
                        # Fallback to simpler construction
                        scatter = pg.ScatterPlotItem(pos=list(zip(x_data, y_data)))
                    plot_widget.addItem(scatter)

        # Set axis ranges if available
        if plot_data.get('x_range'):
            plot_widget.setXRange(*plot_data['x_range'])

        if plot_data.get('y_range'):
            plot_widget.setYRange(*plot_data['y_range'])

    def add_recent_dataset(self, filename, pathname, filesize_bytes=None):
        """
        Add a dataset to the recent datasets list.
        """
        # Format the filesize for display
        if filesize_bytes is not None:
            if filesize_bytes < 1024:
                size_str = f"{filesize_bytes} B"
            elif filesize_bytes < 1024**2:
                size_str = f"{filesize_bytes/1024:.1f} KB"
            elif filesize_bytes < 1024**3:
                size_str = f"{filesize_bytes/1024**2:.1f} MB"
            else:
                size_str = f"{filesize_bytes/1024**3:.1f} GB"
        else:
            size_str = "Unknown size"

        # Current timestamp for "today" display
        import datetime
        now = datetime.datetime.now()
        date_str = f"• Added {now.strftime('%d %b %Y')}"

        # Create dataset metadata
        dataset_info = {
            "filename": filename,
            "pathname": pathname,
            "metadata": f"{size_str} {date_str}",
            "timestamp": now.timestamp()  # Store timestamp for sorting
        }

        # Check if this dataset already exists in the list
        existing_index = -1
        for i, dataset in enumerate(self.recent_datasets):
            if dataset.get("filename") == filename and dataset.get("pathname") == pathname:
                existing_index = i
                break

        # If it exists, remove it so we can add it to the top
        if existing_index >= 0:
            self.recent_datasets.pop(existing_index)

        # Add to the beginning of the list
        self.recent_datasets.insert(0, dataset_info)

        # Limit to maximum 5 recent datasets
        self.recent_datasets = self.recent_datasets[:5]

        # If dashboard is currently visible, refresh it
        if hasattr(self, 'central_stacked_widget') and self.central_stacked_widget.currentWidget() == self.dashboard_page:
            self.show_dashboard_view()  # Refresh to show the new dataset

    def open_dataset(self, dataset):
        """
        Open a dataset from the recent datasets list.

        Args:
            dataset: Dictionary with dataset information
        """
        print(f"Opening dataset: {dataset['filename']}")

        # Extract file information
        filename = dataset.get("filename")
        pathname = dataset.get("pathname", "")

        # Check if the file exists
        full_path = os.path.join(pathname, filename)
        if not os.path.exists(full_path):
            # Show an error message
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file {filename} could not be found at {pathname}.\n\nIt may have been moved or deleted.",
                QMessageBox.Ok
            )

            # Remove the file from recent datasets
            for i, d in enumerate(self.recent_datasets):
                if d.get("filename") == filename and d.get("pathname") == pathname:
                    self.recent_datasets.pop(i)
                    break

            # Refresh the dashboard view
            self.show_dashboard_view()
            return

        # Switch to import view and load the file
        self.show_import_data_view()

        # Use QTimer to ensure the import view is fully loaded before loading the file
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._load_dataset_in_import_view(pathname, filename))

    def _load_dataset_in_import_view(self, pathname, filename):
        """
        Helper method to load a dataset in the import view.

        Args:
            pathname: Path to the file
            filename: Name of the file
        """
        if hasattr(self, "import_data_page") and self.import_data_page:
            # Set file information
            self.import_data_page.filename = filename
            self.import_data_page.pathname = pathname

            # Update UI elements
            self.import_data_page.file_info_label.setText(f"Selected: {filename}")
            self.import_data_page.file_info_label.setVisible(True)
            self.import_data_page.footer_file_info.setText(f"File: {filename}")

            # Get file size
            try:
                full_path = os.path.join(pathname, filename)
                file_size = os.path.getsize(full_path)
                file_format = os.path.splitext(filename)[1].upper().replace(".", "")

                # Format file size
                if file_size < 1024:
                    size_str = f"{file_size} bytes"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"

                self.import_data_page.size_info.setText(f"Size: {size_str}")
                self.import_data_page.format_info.setText(f"Format: {file_format}")

                # Load the file
                self.import_data_page.load_file(pathname, filename)

            except Exception as e:
                print(f"Error loading file: {e}")
                import traceback
                traceback.print_exc()

                # Show error in preview
                self.import_data_page.preview_message.setText(f"Error loading file: {str(e)}")


# For testing the window independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportDataWindow()
    window.show()
    sys.exit(app.exec_())
