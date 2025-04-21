import sys
import os
import traceback
import numpy as np
import scipy.io as sio
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
from datetime import datetime

# Add project root to path
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import UI setup
from ui.DecompositionAppUI import setup_ui

# Import workers and other required modules
from SaveMatWorker import SaveMatWorker
from DecompositionWorker import DecompositionWorker
from utils.config_and_input.prepare_parameters import prepare_parameters
from utils.config_and_input.segmentsession import SegmentSession
from MUeditManual import MUeditManual


class DecompositionApp(QMainWindow):
    # Signal to notify the dashboard when a visualization is completed
    visualization_completed = pyqtSignal(object, str, str, str, dict)
    
    def __init__(self, emg_obj=None, filename=None, pathname=None, imported_signal=None, parameters=None, result_file=None):
        super().__init__()

        # Initialize variables
        self.filename = filename
        self.pathname = pathname
        self.emg_obj = emg_obj
        self.imported_signal = imported_signal
        self.result_file = result_file
        self.parent_dashboard = None

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
        self.ui_params = parameters or None  # Store UI parameters

        # Set up the UI components by calling the function from DecompositionAppUI.py
        setup_ui(self)

        # Connect signals to slots
        self.connect_signals()

        # Initialize with data if provided
        if self.emg_obj and self.filename:
            self.update_ui_with_loaded_data()
            
        # If a result file was provided, load it
        if self.result_file and os.path.exists(self.result_file):
            self.load_result_file(self.result_file)

    def connect_signals(self):
        """Connect all UI signals to their handlers."""
        # Left panel connections
        self.set_configuration_button.clicked.connect(self.set_configuration_button_pushed)
        self.segment_session_button.clicked.connect(self.segment_session_button_pushed)

        # Center panel connections
        self.start_button.clicked.connect(self.start_button_pushed)

        # Right panel connections
        self.save_output_button.clicked.connect(self.save_output_to_location)
        self.edit_mode_btn.clicked.connect(self.open_editing_mode)
        self.back_to_import_btn.clicked.connect(self.back_to_import)

    def back_to_import(self):
        """Return to the Import window or dashboard."""
        self.close()
        
        # Notify parent dashboard if available
        if self.parent_dashboard:
            self.parent_dashboard.on_decomp_app_closed()

    def set_data(self, emg_obj, filename, pathname, imported_signal=None):
        """Set data from ImportDataWindow and update UI."""
        self.emg_obj = emg_obj
        self.filename = filename
        self.pathname = pathname
        self.imported_signal = imported_signal

        self.update_ui_with_loaded_data()
        
    def set_parent_dashboard(self, dashboard):
        """Set the parent dashboard for communication."""
        self.parent_dashboard = dashboard
        
    def load_result_file(self, result_file):
        """Load a saved result file."""
        try:
            if not os.path.exists(result_file):
                QMessageBox.warning(self, "File Not Found", f"Could not find result file: {result_file}")
                return False
                
            # Load the .mat file
            data = sio.loadmat(result_file)
            
            # Check if it has the expected structure
            if "signal" not in data:
                QMessageBox.warning(self, "Invalid File", "The result file does not contain valid decomposition data.")
                return False
                
            # Extract parameters if available
            if "parameters" in data:
                self.ui_params = {}
                params = data["parameters"]
                
                # Convert MATLAB parameters to Python dictionary
                for param in params.dtype.names:
                    self.ui_params[param] = params[param][0, 0]
                    
                # Update UI controls with the parameters
                self.update_ui_controls_from_parameters()
                
            # Extract and set the result data
            self.decomposition_result = data["signal"]
            
            # If available, update EMP amplitude/signal preview plot
            if hasattr(self.decomposition_result, "data") and hasattr(self.decomposition_result, "fsamp"):
                self.update_signal_preview()
                
            # Update motor unit count
            self.update_motor_unit_count()
            
            # Enable editing mode
            self.edit_mode_btn.setEnabled(True)
            self.save_output_button.setEnabled(True)
            
            self.status_text.setText("Loaded decomposition result file")
            self.edit_field.setText(f"Loaded {os.path.basename(result_file)}")
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load result file: {str(e)}")
            traceback.print_exc()
            return False
    
    def update_ui_controls_from_parameters(self):
        """Update UI controls based on loaded parameters."""
        if not self.ui_params:
            return
            
        # Map parameters to UI controls
        try:
            # Number iterations
            if "NITER" in self.ui_params:
                self.number_iterations_field.setValue(self.ui_params["NITER"])
                
            # Windows
            if "nwindows" in self.ui_params:
                self.number_windows_field.setValue(self.ui_params["nwindows"])
                
            # Check EMG
            if "checkEMG" in self.ui_params:
                self.check_emg_dropdown.setCurrentIndex(1 if self.ui_params["checkEMG"] == 0 else 0)
                
            # Peel off
            if "peeloff" in self.ui_params:
                self.peeloff_dropdown.setCurrentIndex(1 if self.ui_params["peeloff"] == 0 else 0)
                
            # CoV filter
            if "covfilter" in self.ui_params:
                self.cov_filter_dropdown.setCurrentIndex(1 if self.ui_params["covfilter"] == 0 else 0)
                
            # Initialization
            if "initialization" in self.ui_params:
                self.initialisation_dropdown.setCurrentIndex(self.ui_params["initialization"])
                
            # Refine MUs
            if "refineMU" in self.ui_params:
                self.refine_mus_dropdown.setCurrentIndex(1 if self.ui_params["refineMU"] == 0 else 0)
                
            # Contrast function
            if "contrastfunc" in self.ui_params:
                contrast_mapping = {"square": 0, "skew": 1, "logcosh": 2}
                if self.ui_params["contrastfunc"] in contrast_mapping:
                    self.contrast_function_dropdown.setCurrentIndex(contrast_mapping[self.ui_params["contrastfunc"]])
                    
            # Thresholds
            if "thresholdtarget" in self.ui_params:
                self.threshold_target_field.setValue(self.ui_params["thresholdtarget"])
                
            if "duplicatesthresh" in self.ui_params:
                self.duplicate_threshold_field.setValue(self.ui_params["duplicatesthresh"])
                
            if "silthr" in self.ui_params:
                self.sil_threshold_field.setValue(self.ui_params["silthr"])
                
            if "covthr" in self.ui_params:
                self.cov_threshold_field.setValue(self.ui_params["covthr"])
                
            if "nbextchan" in self.ui_params:
                self.nb_extended_channels_field.setValue(self.ui_params["nbextchan"])
                
        except Exception as e:
            print(f"Error updating UI controls from parameters: {e}")
            traceback.print_exc()

    def update_signal_preview(self):
        """Update the signal preview plot with loaded data."""
        try:
            if hasattr(self.decomposition_result, "data") and hasattr(self.decomposition_result, "fsamp"):
                # Create a time vector
                data = self.decomposition_result["data"]
                fsamp = self.decomposition_result["fsamp"]
                nsamples = data.shape[1]
                time = np.arange(nsamples) / fsamp

                # Clear existing plot
                self.ui_plot_reference.clear()

                # Plot first few channels
                num_preview_channels = min(3, data.shape[0])
                colors = ["b", "g", "r", "c", "m", "y"]

                for i in range(num_preview_channels):
                    self.ui_plot_reference.plot(
                        time, data[i, :], pen=pg.mkPen(color=colors[i % len(colors)], width=1)
                    )

                self.ui_plot_reference.setTitle(f"Signal Preview ({num_preview_channels} channels)")
        except Exception as e:
            print(f"Error updating signal preview: {e}")
            traceback.print_exc()

    def update_motor_unit_count(self):
        """Update the motor unit count display."""
        try:
            total_mus = 0
            
            if hasattr(self.decomposition_result, "Pulsetrain"):
                pulsetrain = self.decomposition_result["Pulsetrain"]
                
                if isinstance(pulsetrain, np.ndarray) and pulsetrain.ndim > 1:
                    # Iterate through the cell array
                    for i in range(pulsetrain.shape[1]):
                        if i < pulsetrain.shape[1] and pulsetrain[0, i] is not None:
                            if hasattr(pulsetrain[0, i], "shape"):
                                total_mus += pulsetrain[0, i].shape[0]
            
            self.motor_units_label.setText(f"Motor Units: {total_mus}")
            
        except Exception as e:
            print(f"Error updating motor unit count: {e}")
            traceback.print_exc()

    def update_ui_with_loaded_data(self):
        """Update UI elements with the loaded data information."""
        if not self.emg_obj or not self.filename:
            return

        # Update file info display
        file_info = f"File: {self.filename}\n"

        if hasattr(self.emg_obj, "signal_dict"):
            signal = self.emg_obj.signal_dict

            if "data" in signal:
                nchannels, nsamples = signal["data"].shape
                file_info += f"Channels: {nchannels}\n"
                file_info += f"Samples: {nsamples}\n"

            if "fsamp" in signal:
                file_info += f"Sample rate: {signal['fsamp']} Hz\n"

            if "nelectrodes" in signal:
                file_info += f"Electrodes: {signal['nelectrodes']}\n"

        self.file_info_display.setText(file_info)

        # Update the reference dropdown with available signals
        self.reference_dropdown.blockSignals(True)
        self.reference_dropdown.clear()

        signal = self.emg_obj.signal_dict

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

        # Enable the start button and configuration
        self.start_button.setEnabled(True)
        self.set_configuration_button.setEnabled(True)

        # Update status text
        self.edit_field.setText(f"Loaded {self.filename}")
        self.status_text.setText("Ready to start decomposition")

        # Create a preview plot if possible
        if "data" in signal and "fsamp" in signal:
            try:
                # Create a time vector
                fsamp = signal["fsamp"]
                nsamples = signal["data"].shape[1]
                time = np.arange(nsamples) / fsamp

                # Plot first channel as preview
                self.ui_plot_reference.clear()

                # Plot the first few channels for preview
                num_preview_channels = min(3, signal["data"].shape[0])
                colors = ["b", "g", "r", "c", "m", "y"]

                for i in range(num_preview_channels):
                    self.ui_plot_reference.plot(
                        time, signal["data"][i, :], pen=pg.mkPen(color=colors[i % len(colors)], width=1)
                    )

                self.ui_plot_reference.setTitle(f"Signal Preview ({num_preview_channels} channels)")
            except Exception as e:
                print(f"Error creating preview plot: {e}")

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
                "time": np.linspace(
                    0, signal[0, 0]["data"].shape[1] / signal[0, 0]["fsamp"][0, 0], signal[0, 0]["data"].shape[1]
                ),
                "Pulsetrain": [],
                "Dischargetimes": {},
                "silval": {},
                "silvalcon": {},
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
                "edition": edition_data,  # Properly formatted edition data
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

        except Exception as e:
            self.edit_field.setText(f"Error opening editing mode: {str(e)}")
            traceback.print_exc()

    # Event handlers
    def save_mat_in_background(self, filename, data, compression=True):
        self.edit_field.setText("Saving data in background...")

        # Create and configure the worker thread
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)

        worker.finished.connect(lambda: self.on_save_finished(worker))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))

        worker.start()

    def on_save_finished(self, worker):
        self.edit_field.setText("Data saved successfully")
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
                self.set_configuration_button.setStyleSheet(
                    "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
                )
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
        self.segment_session_button.setStyleSheet(
            "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
        )

    def start_button_pushed(self):
        # Reset iteration counter at the start of a new decomposition
        self.iteration_counter = 0

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

        # Convert UI parameters to algorithm parameters
        parameters = prepare_parameters(ui_params)

        print(parameters)

        # Check if we have a file and EMG object
        if not self.emg_obj or not self.pathname or not self.filename:
            self.edit_field.setText("Please select and load a file first")
            return

        # Disable the start button during processing
        self.start_button.setEnabled(False)
        self.edit_field.setText("Starting decomposition...")
        self.status_text.setText("Processing...")
        self.status_progress.setValue(10)

        # Pass the EMG object to the DecompositionWorker
        self.decomp_worker = DecompositionWorker(self.emg_obj, parameters)
        self.threads.append(self.decomp_worker)  # Keep a reference to prevent garbage collection

        # Connect signals
        self.decomp_worker.progress.connect(self.update_progress)
        self.decomp_worker.plot_update.connect(self.update_plots)
        self.decomp_worker.finished.connect(self.on_decomposition_complete)
        self.decomp_worker.error.connect(self.on_decomposition_error)

        # Start the worker thread
        self.decomp_worker.start()

    def on_decomposition_complete(self, result):
        """Handle successful completion of decomposition"""
        result_file = None
        
        if self.pathname and self.filename:
            savename = os.path.join(self.pathname, self.filename + "_output_decomp.mat")
            result_file = savename

            formatted_result = result.copy() if isinstance(result, dict) else result

            # Format Pulsetrain as a MATLAB-compatible cell array
            if "Pulsetrain" in formatted_result:
                max_electrode = max(formatted_result["Pulsetrain"].keys()) if formatted_result["Pulsetrain"] else 0

                pulsetrain_obj = np.empty((1, max_electrode + 1), dtype=object)

                # Fill the array with pulse trains
                for i in range(max_electrode + 1):
                    if i in formatted_result["Pulsetrain"]:
                        pulsetrain_obj[0, i] = formatted_result["Pulsetrain"][i]
                    else:
                        signal_width = formatted_result["data"].shape[1] if "data" in formatted_result else 0
                        pulsetrain_obj[0, i] = np.zeros((0, signal_width))

                # Replace dictionary with object array
                formatted_result["Pulsetrain"] = pulsetrain_obj

            # Format Dischargetimes as a MATLAB-compatible cell array
            if "Dischargetimes" in formatted_result:
                max_electrode = 0
                max_mu = 0

                for key in formatted_result["Dischargetimes"].keys():
                    if isinstance(key, tuple) and len(key) == 2:
                        electrode, mu = key
                        max_electrode = max(max_electrode, electrode)
                        max_mu = max(max_mu, mu)

                dischargetimes_obj = np.empty((max_electrode + 1, max_mu + 1), dtype=object)

                # Initialize all cells with empty arrays
                for i in range(max_electrode + 1):
                    for j in range(max_mu + 1):
                        dischargetimes_obj[i, j] = np.array([], dtype=int)

                # Fill with actual discharge times
                for key, value in formatted_result["Dischargetimes"].items():
                    if isinstance(key, tuple) and len(key) == 2:
                        electrode, mu = key
                        dischargetimes_obj[electrode, mu] = value

                formatted_result["Dischargetimes"] = dischargetimes_obj

            # Format other arrays properly for MATLAB compatibility
            for field_name in ["gridname", "muscle", "auxiliaryname"]:
                if field_name in formatted_result:
                    field_data = formatted_result[field_name]
                    field_obj = np.empty((1, len(field_data)), dtype=object)

                    # Fill the array with the field data
                    for i, item in enumerate(field_data):
                        field_obj[0, i] = str(item)

                    formatted_result[field_name] = field_obj

            # Format coordinates and EMG mask
            if "coordinates" in formatted_result:
                coordinates = formatted_result["coordinates"]
                ngrid = formatted_result.get("ngrid", 1)

                coord_obj = np.empty((1, ngrid), dtype=object)

                # Process list of coordinates arrays
                for i, coord in enumerate(coordinates):
                    if i < ngrid:
                        if isinstance(coord, np.ndarray):
                            if coord.ndim == 2 and coord.shape[1] == 2:
                                coord_obj[0, i] = coord
                            else:
                                coord_obj[0, i] = np.reshape(coord, (-1, 2))
                        else:
                            coord_obj[0, i] = np.array(coord).reshape(-1, 2)

                # Fill any empty cells with default
                for i in range(ngrid):
                    if coord_obj[0, i] is None:
                        coord_obj[0, i] = np.zeros((0, 2))

                formatted_result["coordinates"] = coord_obj

            if "EMGmask" in formatted_result:
                emgmask = formatted_result["EMGmask"]
                ngrid = formatted_result.get("ngrid", 1)

                mask_obj = np.empty((1, ngrid), dtype=object)

                # Process list of mask arrays
                for i, mask in enumerate(emgmask):
                    if i < ngrid:
                        if isinstance(mask, np.ndarray):
                            if mask.ndim == 1:
                                mask_obj[0, i] = mask.reshape(-1, 1)
                            elif mask.ndim == 2 and mask.shape[1] == 1:
                                mask_obj[0, i] = mask
                            else:
                                mask_obj[0, i] = mask.flatten().reshape(-1, 1)
                        else:
                            mask_obj[0, i] = np.array(mask).flatten().reshape(-1, 1)

                # Fill any empty cells with default (empty) mask arrays
                for i in range(ngrid):
                    if mask_obj[0, i] is None:
                        if "coordinates" in formatted_result and formatted_result["coordinates"][0, i] is not None:
                            coord_len = formatted_result["coordinates"][0, i].shape[0]
                            mask_obj[0, i] = np.zeros((coord_len, 1), dtype=int)
                        else:
                            mask_obj[0, i] = np.zeros((0, 1), dtype=int)

                formatted_result["EMGmask"] = mask_obj

            # Save with parameters
            parameters = prepare_parameters(self.ui_params) if hasattr(self, "ui_params") else {}
            self.save_mat_in_background(savename, {"signal": formatted_result, "parameters": parameters}, True)

            # Store the decomposition result
            self.decomposition_result = formatted_result

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

        # Emit signal to notify dashboard of completed visualization
        if hasattr(self, "parent_dashboard") and self.parent_dashboard and hasattr(self, "visualization_completed"):
            # Include EMG object, filename, path, result file path, and parameters
            self.visualization_completed.emit(
                self.emg_obj,
                self.filename,
                self.pathname,
                result_file,
                self.ui_params
            )
            # Call parent dashboard's method directly
            if hasattr(self.parent_dashboard, "on_decomposition_complete"):
                self.parent_dashboard.on_decomposition_complete(
                    self.emg_obj,
                    self.filename,
                    self.pathname,
                    result_file,
                    self.ui_params
                )

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
            self.status_progress.setValue(int(progress * 100))

    def update_plots(self, time, target, plateau_coords, icasig=None, spikes=None, time2=None, sil=None, cov=None):
        """Update plot displays during decomposition using PyQtGraph"""
        try:
            self.iteration_counter += 1

            if sil is not None and cov is not None:
                self.edit_field.setText(f"Iteration #{self.iteration_counter}: SIL = {sil:.4f}, CoV = {cov:.4f}")
                self.sil_value_label.setText(f"SIL: {sil:.4f}")
                self.cov_value_label.setText(f"CoV: {cov:.4f}")

            # Only update plots every 5 iterations to reduce UI overhead
            if self.iteration_counter % 5 != 0 and self.iteration_counter > 1:
                return

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
        if not hasattr(self, "decomposition_result") or self.decomposition_result is None:
            self.edit_field.setText("No decomposition results available to save")
            return

        # Open file dialog to select save location
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Decomposition Results",
            os.path.join(self.pathname if self.pathname else "", "decomposition_results.mat"),
            "MAT Files (*.mat);;All Files (*.*)",
        )

        if not save_path:  # User cancelled
            return

        # Ensure the path has a .mat extension
        if not save_path.lower().endswith(".mat"):
            save_path += ".mat"

        # Format the result properly (same as in on_decomposition_complete)
        formatted_result = self.decomposition_result

        # Get the parameters that were used
        parameters = prepare_parameters(self.ui_params) if hasattr(self, "ui_params") else {}

        # Save in background
        self.save_mat_in_background(save_path, {"signal": formatted_result, "parameters": parameters}, True)
        self.edit_field.setText(f"Saving results to {save_path}")
        
        # If connected to dashboard, notify of new result saved
        if hasattr(self, "parent_dashboard") and self.parent_dashboard and hasattr(self.parent_dashboard, "on_decomposition_complete"):
            self.parent_dashboard.on_decomposition_complete(
                self.emg_obj,
                self.filename,
                self.pathname,
                save_path,
                self.ui_params
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DecompositionApp()
    window.show()
    sys.exit(app.exec_())
