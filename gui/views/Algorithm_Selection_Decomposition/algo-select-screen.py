import sys
import os
import traceback
import numpy as np
import scipy.io as sio
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QLineEdit, QProgressBar, 
    QFrame, QGridLayout, QCheckBox, QRadioButton, QSpinBox,
    QDoubleSpinBox, QScrollArea, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import pyqtgraph for visualization
import pyqtgraph as pg

# Import workers from the root directory
from SaveMatWorker import SaveMatWorker
from DecompositionWorker import DecompositionWorker
from HDEMGdecomposition import prepare_parameters

# Import UI related modules from utils
from utils.config_and_input.openOTBplus import openOTBplus
from utils.config_and_input.segmentsession import SegmentSession

# Import MUeditManual for editing mode
from MUeditManual import MUeditManual

# Import our recent datasets manager
try:
    from gui.recent_datasets_manager import RecentDatasetsManager
except ImportError:
    try:
        from recent_datasets_manager import RecentDatasetsManager
    except ImportError:
        print("Warning: recent_datasets_manager.py not found.")
        # Create a simple placeholder if the module is not found
        class RecentDatasetsManager:
            def __init__(self, max_entries=10):
                self.recent_datasets = []
            def get_recent_datasets(self, count=None):
                return self.recent_datasets
            def add_dataset(self, filepath, dataset_type="", filesize=None, row_count=None):
                pass
            def remove_dataset(self, filepath):
                pass


class DecompositionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Algorithm Selection & Decomposition")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create recent datasets manager
        self.recent_datasets_manager = RecentDatasetsManager()
        
        # Initialize variables
        self.filename = None
        self.pathname = None
        self.filename2 = None
        self.pathname2 = None
        self.MUdecomp = {"config": None}
        self.Configuration = None
        self.MUedition = None
        self.Backup = {"lock": 0}
        self.graphstart = None
        self.graphend = None
        self.roi = None
        self.threads = []
        self.iteration_counter = 0
        self.decomposition_result = None  # Store the decomposition result
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Create the left panel for settings
        self.setup_left_panel()
        
        # Create the center panel for visualization
        self.setup_center_panel()
        
        # Create the right panel for status and results
        self.setup_right_panel()
        
    def setup_left_panel(self):
        left_panel = QWidget()
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        # Algorithm Selection
        algo_label = QLabel("Algorithm Selection")
        self.algo_combo = QComboBox()
        self.algo_combo.addItem("Fast ICA")
        self.algo_combo.addItem("Other Algorithm 1")
        self.algo_combo.addItem("Other Algorithm 2")
        
        # File Selection
        self.select_file_button = QPushButton("Select File")
        self.select_file_button.clicked.connect(self.select_file_button_pushed)
        
        self.edit_field_saving_3 = QLineEdit()
        self.edit_field_saving_3.setReadOnly(True)
        
        # Processing Options
        processing_label = QLabel("Processing Options")
        
        # Check EMG Quality
        check_emg_label = QLabel("Check EMG Quality")
        self.check_emg_dropdown = QComboBox()
        self.check_emg_dropdown.addItem("Yes")
        self.check_emg_dropdown.addItem("No")
        
        # COV Filter
        cov_filter_label = QLabel("COV Filter")
        self.cov_filter_dropdown = QComboBox()
        self.cov_filter_dropdown.addItem("Yes")
        self.cov_filter_dropdown.addItem("No")
        
        # Reference
        reference_label = QLabel("Reference")
        self.reference_dropdown = QComboBox()
        self.reference_dropdown.addItem("EMG amplitude")
        self.reference_dropdown.addItem("Target")
        
        # Set Configuration Button
        self.set_configuration_button = QPushButton("Set Configuration")
        self.set_configuration_button.clicked.connect(self.set_configuration_button_pushed)
        self.set_configuration_button.setEnabled(False)
        
        # Segment Session
        self.segment_session_button = QPushButton("Segment Session")
        self.segment_session_button.clicked.connect(self.segment_session_button_pushed)
        
        # Contrast Function
        contrast_label = QLabel("Contrast Function")
        self.contrast_function_dropdown = QComboBox()
        self.contrast_function_dropdown.addItem("Skew")
        self.contrast_function_dropdown.addItem("Logcosh")
        self.contrast_function_dropdown.addItem("Kurtosis")
        
        # Initialisation
        init_label = QLabel("Initialisation")
        self.initialisation_dropdown = QComboBox()
        self.initialisation_dropdown.addItem("EMG max")
        self.initialisation_dropdown.addItem("Random")
        
        # Peel Off
        peel_label = QLabel("Peel Off")
        self.peeloff_dropdown = QComboBox()
        self.peeloff_dropdown.addItem("Yes")
        self.peeloff_dropdown.addItem("No")
        
        # Refine Motor Units
        refine_label = QLabel("Refine Motor Units")
        self.refine_mus_dropdown = QComboBox()
        self.refine_mus_dropdown.addItem("Yes")
        self.refine_mus_dropdown.addItem("No")
        
        # Iterations and Windows
        iter_layout = QHBoxLayout()
        iter_label = QLabel("Iterations")
        self.number_iterations_field = QSpinBox()
        self.number_iterations_field.setValue(75)
        self.number_iterations_field.setRange(1, 1000)
        
        windows_label = QLabel("Windows")
        self.number_windows_field = QSpinBox()
        self.number_windows_field.setValue(1)
        self.number_windows_field.setRange(1, 100)
        
        iter_layout.addWidget(iter_label)
        iter_layout.addWidget(self.number_iterations_field)
        iter_layout.addWidget(windows_label)
        iter_layout.addWidget(self.number_windows_field)
        
        # Threshold Target
        threshold_label = QLabel("Threshold Target")
        self.threshold_target_field = QDoubleSpinBox()
        self.threshold_target_field.setValue(0.8)
        self.threshold_target_field.setRange(0, 1)
        self.threshold_target_field.setSingleStep(0.1)
        
        # Duplicate Threshold
        duplicate_label = QLabel("Duplicate Threshold")
        self.duplicate_threshold_field = QDoubleSpinBox()
        self.duplicate_threshold_field.setValue(0.3)
        self.duplicate_threshold_field.setRange(0, 1)
        self.duplicate_threshold_field.setSingleStep(0.1)
        
        # SIL Threshold
        sil_label = QLabel("SIL Threshold")
        self.sil_threshold_field = QDoubleSpinBox()
        self.sil_threshold_field.setValue(0.9)
        self.sil_threshold_field.setRange(0, 1)
        self.sil_threshold_field.setSingleStep(0.1)
        
        # COV Threshold
        cov_threshold_label = QLabel("COV Threshold")
        self.cov_threshold_field = QDoubleSpinBox()
        self.cov_threshold_field.setValue(0.5)
        self.cov_threshold_field.setRange(0, 1)
        self.cov_threshold_field.setSingleStep(0.1)
        
        # Nb of extended channels
        channels_label = QLabel("Nb of extended channels")
        self.nb_extended_channels_field = QSpinBox()
        self.nb_extended_channels_field.setValue(1000)
        self.nb_extended_channels_field.setRange(10, 5000)
        
        # Add all widgets to left layout
        left_layout.addWidget(algo_label)
        left_layout.addWidget(self.algo_combo)
        left_layout.addWidget(self.select_file_button)
        left_layout.addWidget(self.edit_field_saving_3)
        left_layout.addWidget(processing_label)
        left_layout.addWidget(check_emg_label)
        left_layout.addWidget(self.check_emg_dropdown)
        left_layout.addWidget(cov_filter_label)
        left_layout.addWidget(self.cov_filter_dropdown)
        left_layout.addWidget(reference_label)
        left_layout.addWidget(self.reference_dropdown)
        left_layout.addWidget(self.set_configuration_button)
        left_layout.addWidget(self.segment_session_button)
        left_layout.addWidget(contrast_label)
        left_layout.addWidget(self.contrast_function_dropdown)
        left_layout.addWidget(init_label)
        left_layout.addWidget(self.initialisation_dropdown)
        left_layout.addWidget(peel_label)
        left_layout.addWidget(self.peeloff_dropdown)
        left_layout.addWidget(refine_label)
        left_layout.addWidget(self.refine_mus_dropdown)
        left_layout.addLayout(iter_layout)
        left_layout.addWidget(threshold_label)
        left_layout.addWidget(self.threshold_target_field)
        left_layout.addWidget(duplicate_label)
        left_layout.addWidget(self.duplicate_threshold_field)
        left_layout.addWidget(sil_label)
        left_layout.addWidget(self.sil_threshold_field)
        left_layout.addWidget(cov_threshold_label)
        left_layout.addWidget(self.cov_threshold_field)
        left_layout.addWidget(channels_label)
        left_layout.addWidget(self.nb_extended_channels_field)
        left_layout.addStretch()
        
        self.main_layout.addWidget(left_panel)
        
    def setup_center_panel(self):
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # Status display field
        self.edit_field = QLineEdit()
        self.edit_field.setReadOnly(True)
        self.edit_field.setText("Ready")
        
        # Decomposition Controls section
        controls_layout = QHBoxLayout()
        decomp_label = QLabel("Decomposition Controls")
        decomp_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.start_button = QPushButton("▶ Start Decomposition")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px;")
        self.start_button.clicked.connect(self.start_button_pushed)
        
        controls_layout.addWidget(decomp_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.start_button)
        
        # Signal Processing Visualization section
        signal_label = QLabel("Signal Processing Visualization")
        signal_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Signal visualization area using pyqtgraph
        self.ui_plot_reference = pg.PlotWidget()
        self.ui_plot_reference.setBackground('w')  # White background
        self.ui_plot_reference.setLabel('left', 'Amplitude')
        self.ui_plot_reference.setLabel('bottom', 'Time (s)')
        self.ui_plot_reference.showGrid(x=True, y=True)
        
        # Motor Unit Outputs section
        motor_unit_label = QLabel("Motor Unit Outputs")
        motor_unit_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Motor unit visualization area using pyqtgraph
        self.ui_plot_pulsetrain = pg.PlotWidget()
        self.ui_plot_pulsetrain.setBackground('w')  # White background
        self.ui_plot_pulsetrain.setLabel('left', 'Amplitude')
        self.ui_plot_pulsetrain.setLabel('bottom', 'Time (s)')
        self.ui_plot_pulsetrain.showGrid(x=True, y=True)
        
        # Add all widgets to center layout
        center_layout.addWidget(self.edit_field)
        center_layout.addLayout(controls_layout)
        center_layout.addWidget(signal_label)
        center_layout.addWidget(self.ui_plot_reference, stretch=3)
        center_layout.addWidget(motor_unit_label)
        center_layout.addWidget(self.ui_plot_pulsetrain, stretch=2)
        
        self.main_layout.addWidget(center_panel, stretch=3)
        
    def setup_right_panel(self):
        right_panel = QWidget()
        right_panel.setMaximumWidth(250)
        right_layout = QVBoxLayout(right_panel)
        
        # Processing Status section
        status_label = QLabel("Processing Status")
        
        self.status_progress = QProgressBar()
        self.status_progress.setValue(0)
        
        self.status_text = QLabel("Ready")
        
        # Analysis Results section
        results_label = QLabel("Analysis Results")
        results_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.motor_units_label = QLabel("Motor Units: --")
        
        self.sil_value_label = QLabel("SIL: --")
        
        self.cov_value_label = QLabel("CoV: --")
        
        # Save Output button
        self.save_output_button = QPushButton("💾 Save Output")
        self.save_output_button.setEnabled(False)
        self.save_output_button.clicked.connect(self.save_output_to_location)
        
        # Navigation section
        nav_label = QLabel("Navigation")
        nav_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.edit_mode_btn = QPushButton("✏️ Editing Mode")
        self.edit_mode_btn.clicked.connect(self.open_editing_mode)
        self.edit_mode_btn.setEnabled(False)
        
        self.analysis_mode_btn = QPushButton("📊 Analysis Mode")
        
        self.export_btn = QPushButton("📤 Export")
        
        # Add all widgets to right layout
        right_layout.addWidget(status_label)
        right_layout.addWidget(self.status_progress)
        right_layout.addWidget(self.status_text)
        right_layout.addSpacing(20)
        right_layout.addWidget(results_label)
        right_layout.addWidget(self.motor_units_label)
        right_layout.addWidget(self.sil_value_label)
        right_layout.addWidget(self.cov_value_label)
        right_layout.addWidget(self.save_output_button)
        right_layout.addSpacing(20)
        right_layout.addWidget(nav_label)
        right_layout.addWidget(self.edit_mode_btn)
        right_layout.addWidget(self.analysis_mode_btn)
        right_layout.addWidget(self.export_btn)
        right_layout.addStretch()
        
        self.main_layout.addWidget(right_panel)
    
    def open_editing_mode(self):
        """Open the MUeditManual window for editing motor units"""
        if not self.pathname or not self.filename:
            self.edit_field.setText("No file selected for editing")
            return
            
        try:
            # First check if the output file exists
            output_filename = os.path.join(self.pathname, self.filename + "_output_decomp.mat")
            if not os.path.exists(output_filename):
                self.edit_field.setText(f"Output file {output_filename} not found")
                return
                
            # Load the data first to fix the structure
            data = sio.loadmat(output_filename)
            if "signal" not in data:
                self.edit_field.setText("Invalid file format: 'signal' field not found")
                return
                
            signal = data["signal"]
            
            # Create the proper data structure for MUeditManual
            edition_data = {
                "time": np.linspace(0, signal[0, 0]["data"].shape[1] / signal[0, 0]["fsamp"][0, 0], signal[0, 0]["data"].shape[1]),
                "Pulsetrain": [],
                "Dischargetimes": {},
                "silval": {},
                "silvalcon": {}
            }
            
            # Format the Pulsetrain data correctly
            # MUeditManual expects a list of 2D arrays (one per electrode)
            # Each 2D array should have shape (n_motor_units, signal_length)
            if "Pulsetrain" in signal[0, 0].dtype.names:
                pulsetrain_data = signal[0, 0]["Pulsetrain"][0]
                
                for i in range(len(pulsetrain_data)):
                    # Get the pulse train for this electrode
                    electrode_pulses = pulsetrain_data[i]
                    
                    # Check if it's already 2D
                    if electrode_pulses.ndim == 2:
                        edition_data["Pulsetrain"].append(electrode_pulses)
                    elif electrode_pulses.ndim == 1:
                        # Convert 1D array to 2D with one row
                        edition_data["Pulsetrain"].append(electrode_pulses.reshape(1, -1))
                    else:
                        # Skip empty or invalid arrays
                        edition_data["Pulsetrain"].append(np.zeros((0, signal[0, 0]["data"].shape[1])))
            
            # Format the Dischargetimes data correctly
            # MUeditManual expects a dictionary with (array_idx, mu_idx) tuple keys
            if "Dischargetimes" in signal[0, 0].dtype.names:
                dischargetimes_data = signal[0, 0]["Dischargetimes"]
                
                for i in range(dischargetimes_data.shape[0]):
                    for j in range(dischargetimes_data.shape[1]):
                        # Get the discharge times array
                        dt = dischargetimes_data[i, j]
                        
                        # Skip empty arrays
                        if isinstance(dt, np.ndarray) and dt.size > 0:
                            # Store with tuple key (array_idx, mu_idx)
                            edition_data["Dischargetimes"][(i, j)] = dt.flatten()
            
            # Create a new .mat file with the fixed structure
            fixed_filename = os.path.join(self.pathname, self.filename + "_fixed_for_editing.mat")
            
            # Create the structure expected by MUeditManual
            fixed_data = {
                "signal": signal,  # Original signal data
                "edition": edition_data  # Properly formatted edition data
            }
            
            # Use existing save_mat_in_background function to save the fixed data
            self.save_mat_in_background(fixed_filename, fixed_data, True)
            
            # Update UI
            self.edit_field.setText(f"Preparing data for editing and opening editor...")
            
            # Create the MUeditManual window
            self.mu_edit_window = MUeditManual()
            
            # Show the window without preloading
            self.mu_edit_window.show()
            
            # Suggest the file to open
            self.edit_field.setText(f"Editor opened. Please select {fixed_filename}")
            
            # Add the edited file to recent datasets
            row_count = 0
            if "Pulsetrain" in signal[0, 0].dtype.names:
                try:
                    for electrode_pulses in signal[0, 0]["Pulsetrain"][0]:
                        if hasattr(electrode_pulses, "shape") and electrode_pulses.ndim == 2:
                            row_count += electrode_pulses.shape[0]
                except:
                    pass
                    
            # Add to recent datasets with row count = number of motor units
            if hasattr(self.recent_datasets_manager, 'add_dataset'):
                self.recent_datasets_manager.add_dataset(
                    fixed_filename,
                    dataset_type="Edited Decomposition Data",
                    row_count=row_count
                )
            
        except Exception as e:
            self.edit_field.setText(f"Error opening editing mode: {str(e)}")
            traceback.print_exc()
    
    # Event handlers
    def select_file_button_pushed(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
        if not file:
            return

        self.filename = os.path.basename(file)
        self.pathname = os.path.dirname(file) + "/"
        self.edit_field_saving_3.setText(self.filename)

        # Keep start button styling but reset others to default
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px;")
        QApplication.processEvents()

        # Load files
        ext = os.path.splitext(self.filename)[1]
        if ext == ".otb+":  # OT Biolab+
            try:
                self.MUdecomp["config"], signal, savename = openOTBplus(self.pathname, self.filename, 1)
                if self.MUdecomp["config"]:
                    self.MUdecomp["config"].hide()
                    self.set_configuration_button.setEnabled(True)

                if savename:
                    self.save_mat_in_background(savename, {"signal": signal}, True)
                    
                    # Add to recent datasets
                    if hasattr(self.recent_datasets_manager, 'add_dataset'):
                        self.recent_datasets_manager.add_dataset(
                            savename,
                            dataset_type="Imported OTB+ Data",
                            filesize=os.path.getsize(savename) if os.path.exists(savename) else None
                        )
                    
                self.reference_dropdown.blockSignals(True)
                self.reference_dropdown.clear()

                # Update the list of signals for reference
                if "auxiliaryname" in signal:
                    self.reference_dropdown.addItem("EMG amplitude")
                    for name in signal["auxiliaryname"]:
                        self.reference_dropdown.addItem(name)
                elif "target" in signal:
                    path_data = signal["path"]
                    target_data = signal["target"]

                    if isinstance(path_data, np.ndarray) and isinstance(target_data, np.ndarray):
                        path_reshaped = path_data.reshape(1, -1) if path_data.ndim == 1 else path_data
                        target_reshaped = target_data.reshape(1, -1) if target_data.ndim == 1 else target_data
                        signal["auxiliary"] = np.vstack((path_reshaped, target_reshaped))
                    else:
                        signal["auxiliary"] = np.vstack((np.array([path_data]), np.array([target_data])))

                    signal["auxiliaryname"] = ["Path", "Target"]
                    self.reference_dropdown.addItem("EMG amplitude")
                    for name in signal["auxiliaryname"]:
                        self.reference_dropdown.addItem(name)
                else:
                    self.reference_dropdown.addItem("EMG amplitude")
                
                self.reference_dropdown.blockSignals(False)
                
            except Exception as e:
                self.edit_field.setText(f"Error loading file: {str(e)}")
                return

        savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
        self.save_mat_in_background(savename, {"signal": signal}, True)

    def save_mat_in_background(self, filename, data, compression=True):
        self.edit_field.setText("Saving data in background...")

        # Create and configure the worker thread
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)

        worker.finished.connect(lambda: self.on_save_finished(worker, filename))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))

        worker.start()

    def on_save_finished(self, worker, filename):
        self.edit_field.setText(f"Data saved successfully to {filename}")
        self.cleanup_thread(worker)

    def on_save_error(self, worker, error_msg):
        self.edit_field.setText(f"Error saving data: {error_msg}")
        self.cleanup_thread(worker)

    def cleanup_thread(self, worker):
        if worker in self.threads:
            self.threads.remove(worker)

    def set_configuration_button_pushed(self):
        if "config" in self.MUdecomp and self.MUdecomp["config"]:
            try:
                if self.pathname is not None and self.filename is not None:
                    savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
                    self.MUdecomp["config"].pathname.setText(savename)

                # Show the dialog
                self.MUdecomp["config"].show()
            except Exception as e:
                print(f"Error showing configuration dialog: {e}")
                traceback.print_exc()
        else:
            print("No configuration dialog available")

    def segment_session_button_pushed(self):
        self.segment_session = SegmentSession()

        if self.pathname is not None and self.filename is not None:
            self.segment_session.pathname.setText(self.pathname + self.filename + "_decomp.mat")

        # Setup the dropdown contents before setting the current item
        self.segment_session.reference_dropdown.clear()
        for i in range(self.reference_dropdown.count()):
            self.segment_session.reference_dropdown.addItem(self.reference_dropdown.itemText(i))

        try:
            if self.segment_session.pathname.text():
                self.segment_session.file = sio.loadmat(self.segment_session.pathname.text())
        except Exception as e:
            print(f"Warning: Could not load file: {e}")

        # Set current text after file is loaded
        self.segment_session.reference_dropdown.setCurrentText(self.reference_dropdown.currentText())
        self.segment_session.initialize_with_file()
        self.segment_session.show()

    def start_button_pushed(self):
        if not self.pathname or not self.filename:
            self.edit_field.setText("Please select a file first")
            return
            
        # Get UI parameters
        ui_params = {
            "check_emg": self.check_emg_dropdown.currentText(),
            "peeloff": self.peeloff_dropdown.currentText(),
            "cov_filter": self.cov_filter_dropdown.currentText(),
            "initialization": self.initialisation_dropdown.currentText(),
            "refine_mu": self.refine_mus_dropdown.currentText(),
            "duplicates_bgrids": "Yes",  # Set default value
            "contrast_function": self.contrast_function_dropdown.currentText(),
            "iterations": self.number_iterations_field.value(),
            "windows": self.number_windows_field.value(),
            "threshold_target": self.threshold_target_field.value(),
            "extended_channels": self.nb_extended_channels_field.value(),
            "duplicates_threshold": self.duplicate_threshold_field.value(),
            "sil_threshold": self.sil_threshold_field.value(),
            "cov_threshold": self.cov_threshold_field.value(),
        }

        # Store UI params for later use when saving results
        self.ui_params = ui_params

        # Reset iteration counter at the start of a new decomposition
        self.iteration_counter = 0

        # Convert UI parameters to algorithm parameters
        parameters = prepare_parameters(ui_params)

        # Load signal data
        try:
            savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
            file = sio.loadmat(savename)
            signal = file["signal"]

            # Disable the start button during processing
            self.start_button.setEnabled(False)
            self.edit_field.setText("Starting decomposition...")
            self.status_text.setText("Processing...")
            self.status_progress.setValue(10)
            
            # Create and configure the worker thread
            self.decomp_worker = DecompositionWorker(signal, parameters)
            self.threads.append(self.decomp_worker)  # Keep a reference to prevent garbage collection

            # Connect signals
            self.decomp_worker.progress.connect(self.update_progress)
            self.decomp_worker.plot_update.connect(self.update_plots)
            self.decomp_worker.finished.connect(self.on_decomposition_complete)
            self.decomp_worker.error.connect(self.on_decomposition_error)

            # Start the worker thread
            self.decomp_worker.start()
        except Exception as e:
            self.edit_field.setText(f"Error starting decomposition: {str(e)}")
            self.start_button.setEnabled(True)
            traceback.print_exc()

    def on_decomposition_complete(self, result):
        """Handle successful completion of decomposition"""
        if self.pathname and self.filename:
            savename = os.path.join(self.pathname, self.filename + "_output_decomp.mat")

            # Format the result structure properly for MATLAB compatibility
            formatted_result = result

            # Ensure Pulsetrain and Dischargetimes are properly formatted as cell arrays
            # This will make them appear as NxM cell in MATLAB instead of struct
            if "Pulsetrain" in formatted_result and isinstance(formatted_result["Pulsetrain"], dict):
                max_electrode = max(formatted_result["Pulsetrain"].keys()) if formatted_result["Pulsetrain"] else 0

                pulse_list = [[] for _ in range(max_electrode + 1)]
                for electrode, pulse in formatted_result["Pulsetrain"].items():
                    pulse_list[electrode] = pulse

                formatted_result["Pulsetrain"] = pulse_list

            # Do the same for Dischargetimes
            if "Dischargetimes" in formatted_result and isinstance(formatted_result["Dischargetimes"], dict):
                max_electrode = 0
                max_mu = 0
                for key in formatted_result["Dischargetimes"].keys():
                    if isinstance(key, tuple) and len(key) == 2:
                        electrode, mu = key
                        max_electrode = max(max_electrode, electrode)
                        max_mu = max(max_mu, mu)

                # Create properly sized cell array (2D list)
                discharge_list = [[[] for _ in range(max_mu + 1)] for _ in range(max_electrode + 1)]

                # Fill with data
                for key, value in formatted_result["Dischargetimes"].items():
                    if isinstance(key, tuple) and len(key) == 2:
                        electrode, mu = key
                        discharge_list[electrode][mu] = value

                formatted_result["Dischargetimes"] = discharge_list

            # Save with parameters
            parameters = prepare_parameters(self.ui_params) if hasattr(self, "ui_params") else {}
            self.save_mat_in_background(savename, {"signal": formatted_result, "parameters": parameters}, True)

            # Store the decomposition result
            self.decomposition_result = formatted_result
            
            # Add to recent datasets
            if hasattr(self.recent_datasets_manager, 'add_dataset'):
                # Count total MUs
                total_mus = 0
                if "Pulsetrain" in result:
                    if isinstance(result["Pulsetrain"], dict):
                        for electrode, pulses in result["Pulsetrain"].items():
                            if hasattr(pulses, "shape"):
                                total_mus += pulses.shape[0]
                    elif isinstance(result["Pulsetrain"], list):
                        for electrode_pulses in result["Pulsetrain"]:
                            if hasattr(electrode_pulses, "shape"):
                                total_mus += electrode_pulses.shape[0]
                
                # Add to recent datasets with informative metadata
                self.recent_datasets_manager.add_dataset(
                    savename,
                    dataset_type="Decomposition Result",
                    row_count=total_mus
                )

        self.edit_field.setText("Decomposition complete")
        self.status_text.setText("Complete")
        self.status_progress.setValue(100)
        self.start_button.setEnabled(True)
        self.save_output_button.setEnabled(True)
        self.edit_mode_btn.setEnabled(True)

        # Count total motor units
        total_mus = 0
        if "Pulsetrain" in result:
            if isinstance(result["Pulsetrain"], dict):
                for electrode, pulses in result["Pulsetrain"].items():
                    if hasattr(pulses, "shape"):
                        total_mus += pulses.shape[0]
            elif isinstance(result["Pulsetrain"], list):
                for electrode_pulses in result["Pulsetrain"]:
                    if hasattr(electrode_pulses, "shape"):
                        total_mus += electrode_pulses.shape[0]
                
        self.motor_units_label.setText(f"Motor Units: {total_mus}")

        if hasattr(self, "decomp_worker") and self.decomp_worker in self.threads:
            self.threads.remove(self.decomp_worker)
            
    def on_decomposition_error(self, error_msg):
        """Handle errors during decomposition"""
        self.edit_field.setText(f"Error in decomposition: {error_msg}")
        self.status_text.setText("Error")
        self.status_progress.setValue(0)
        self.start_button.setEnabled(True)

        if hasattr(self, "decomp_worker") and self.decomp_worker in self.threads:
            self.threads.remove(self.decomp_worker)

    def update_progress(self, message, progress=None):
        """Update progress information during decomposition"""
        self.edit_field.setText(message)
        self.status_text.setText(message.split("-")[0] if "-" in message else message)
        
        if progress is not None and isinstance(progress, (int, float)):
            self.status_progress.setValue(int(progress))
        elif "Iteration" in message and "of" in message:
            # Try to extract iteration info
            try:
                parts = message.split("Iteration")[1].split("of")
                current = int(parts[0].strip())
                total = int(parts[1].split("-")[0].strip())
                self.status_progress.setValue(int(current / total * 100))
            except:
                pass
                
    def update_plots(self, time, target, plateau_coords, icasig=None, spikes=None, time2=None, sil=None, cov=None):
        """Update plot displays during decomposition using PyQtGraph"""
        try:
            self.iteration_counter += 1

            if sil is not None and cov is not None:
                self.edit_field.setText(f"Iteration #{self.iteration_counter}: SIL = {sil:.4f}, CoV = {cov:.4f}")
                self.sil_value_label.setText(f"SIL: {sil:.4f}")
                self.cov_value_label.setText(f"CoV: {cov:.4f}")

            # Only update plots every 5 iterations
            if self.iteration_counter % 5 != 0 and self.iteration_counter > 1:
                return

            # Check for valid input data to avoid errors
            if target is None:
                return

            # Ensure arrays are 1D
            if isinstance(target, np.ndarray) and target.ndim > 1:
                target = target.flatten()

            # Check if time array is compatible with target array
            if time is None or (isinstance(time, np.ndarray) and (time.size == 1 or time.shape != target.shape)):
                # Create a synthetic time array that matches target's length
                print(f"Creating synthetic time array to match target shape {target.shape}")
                time = np.arange(len(target))
            elif isinstance(time, np.ndarray) and time.ndim > 1:
                time = time.flatten()

            # Clear previous plots
            self.ui_plot_reference.clear()

            # Plot reference signal with plateau markers
            self.ui_plot_reference.plot(
                time, target, pen=pg.mkPen(color="#000000", width=2, style=Qt.PenStyle.DashLine)
            )

            # Plot plateau markers if available
            if plateau_coords is not None and len(plateau_coords) >= 2:
                try:
                    if len(time) > max(plateau_coords):
                        for coord in plateau_coords[:2]:  # Just plot the first two markers
                            line = pg.InfiniteLine(pos=time[coord], angle=90, pen=pg.mkPen(color="#FF0000", width=2))
                            self.ui_plot_reference.addItem(line)
                except (IndexError, TypeError) as e:
                    print(f"Warning: Error plotting plateau markers: {e}")

            # Plot decomposition results if available
            if icasig is not None:
                try:
                    if isinstance(icasig, np.ndarray) and icasig.ndim > 1:
                        icasig = icasig.flatten()

                    if time2 is None or (
                        isinstance(time2, np.ndarray) and (time2.size == 1 or time2.shape != icasig.shape)
                    ):
                        print(f"Creating synthetic time2 array to match icasig shape {icasig.shape}")
                        time2 = np.arange(len(icasig))
                    elif isinstance(time2, np.ndarray) and time2.ndim > 1:
                        time2 = time2.flatten()

                    self.ui_plot_pulsetrain.clear()
                    self.ui_plot_pulsetrain.plot(time2, icasig, pen=pg.mkPen(color="#000000", width=1))

                    if spikes is not None and len(spikes) > 0:
                        valid_indices = [i for i in spikes if i < len(time2)]
                        if valid_indices:
                            scatter = pg.ScatterPlotItem(
                                x=[time2[i] for i in valid_indices],
                                y=[icasig[i] for i in valid_indices],
                                size=10,
                                pen=pg.mkPen(None),
                                brush=pg.mkBrush("#FF0000"),
                            )
                            self.ui_plot_pulsetrain.addItem(scatter)

                    self.ui_plot_pulsetrain.setYRange(-0.2, 1.5)

                    # Update title with SIL and CoV values if available
                    if sil is not None and cov is not None:
                        title = f"Iteration #{self.iteration_counter}: SIL = {sil:.4f}, CoV = {cov:.4f}"
                        self.ui_plot_pulsetrain.setTitle(title)

                except Exception as e:
                    print(f"Warning: Error plotting decomposition results: {e}")
                    traceback.print_exc()

        except Exception as e:
            print(f"Error in update_plots: {e}")
            traceback.print_exc()
            
    def save_output_to_location(self):
        """Save decomposition results to a user-specified location"""
        if not hasattr(self, 'decomposition_result') or self.decomposition_result is None:
            self.edit_field.setText("No decomposition results available to save")
            return
        
        # Open file dialog to select save location
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Decomposition Results", 
            os.path.join(self.pathname if self.pathname else "", "decomposition_results.mat"),
            "MAT Files (*.mat);;All Files (*.*)"
        )
        
        if not save_path:  # User cancelled
            return
        
        # Ensure the path has a .mat extension
        if not save_path.lower().endswith('.mat'):
            save_path += '.mat'
        
        # Format the result properly (same as in on_decomposition_complete)
        formatted_result = self.decomposition_result
        
        # Get the parameters that were used
        parameters = prepare_parameters(self.ui_params) if hasattr(self, 'ui_params') else {}
        
        # Save in background
        self.save_mat_in_background(save_path, {"signal": formatted_result, "parameters": parameters}, True)
        self.edit_field.setText(f"Saving results to {save_path}")
        
        # Add to recent datasets
        if hasattr(self.recent_datasets_manager, 'add_dataset'):
            # Count total MUs
            total_mus = 0
            if "Pulsetrain" in self.decomposition_result:
                if isinstance(self.decomposition_result["Pulsetrain"], dict):
                    for electrode, pulses in self.decomposition_result["Pulsetrain"].items():
                        if hasattr(pulses, "shape"):
                            total_mus += pulses.shape[0]
                elif isinstance(self.decomposition_result["Pulsetrain"], list):
                    for electrode_pulses in self.decomposition_result["Pulsetrain"]:
                        if hasattr(electrode_pulses, "shape"):
                            total_mus += electrode_pulses.shape[0]
            
            # Add to recent datasets with row count = number of motor units
            self.recent_datasets_manager.add_dataset(
                save_path,
                dataset_type="Saved Decomposition Result",
                row_count=total_mus
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DecompositionApp()
    window.show()
    sys.exit(app.exec_())