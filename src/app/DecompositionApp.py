import sys
import os
import traceback
import numpy as np
import scipy.io as sio
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog

import pyqtgraph as pg

# Add project root to path
from pathlib import Path

from ui.components.SegmentSessionPage import SegmentSessionPage

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import UI setup
from ui.DecompositionAppUI import setup_ui

# Import workers and other required modules
from workers.SaveMatWorker import SaveMatWorker
from workers.DecompositionWorker import DecompositionWorker
from core.scd.main import SCDDecompositionWorker
from core.utils.config.prepare_parameters import prepare_parameters
from core.EmgDecomposition import format_results_2
from MUeditManual import MUeditManual


class DecompositionApp(QMainWindow):
    def __init__(self, emg_obj=None, filename=None, pathname=None, imported_signal=None, config=None, parent=None):
        super().__init__(parent)

        # Initialize variables
        self.filename = filename
        self.pathname = pathname
        self.emg_obj = emg_obj
        self.imported_signal = imported_signal

        self.MUdecomp = {"config": config}
        self.Configuration = None
        self.MUedition = None
        self.Backup = {"lock": 0}
        self.graphstart = None
        self.graphend = None
        self.roi = None
        self.threads = []
        self.iteration_counter = 0
        self.decomposition_result = None  # Store the decomposition result
        self.ui_params = None  # Store UI parameters

        # Set up the UI components by calling the function from DecompositionAppUI.py
        setup_ui(self)

        # Connect signals to slots
        self.connect_signals()

        # Initialize with data if provided
        if self.emg_obj and self.filename:
            self.update_ui_with_loaded_data()

    def connect_signals(self):
        """Connect all UI signals to their handlers."""
        # Center panel connections
        self.start_button.clicked.connect(self.start_button_pushed)

        # Right panel connections
        self.save_output_button.clicked.connect(self.save_output_to_location)
        self.next_button.clicked.connect(self.open_editing_mode)

    def back_to_import(self):
        """Return to the Import window."""
        # This will now be connected externally to show the import view in the dashboard
        pass

    def set_data(self, emg_obj, filename, pathname, imported_signal=None):
        """Set data from ImportDataWindow and update UI."""
        self.emg_obj = emg_obj
        self.filename = filename
        self.pathname = pathname
        self.imported_signal = imported_signal

        self.update_ui_with_loaded_data()

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

            if "ngrid" in signal:
                file_info += f"Grids: {signal['ngrid']}\n"

        self.file_info_display.setText(file_info)

        """ reference dropdown signals update """

        # Update the reference dropdown with available signals
        # self.reference_dropdown.blockSignals(True)
        # self.reference_dropdown.clear()

        signal = self.emg_obj.signal_dict

        # # Update the list of signals for reference
        # if "auxiliaryname" in signal:
        #     self.reference_dropdown.addItem("EMG amplitude")
        #     for name in signal["auxiliaryname"]:
        #         self.reference_dropdown.addItem(name)
        # elif "target" in signal:
        #     path_data = signal["path"]
        #     target_data = signal["target"]

        #     if isinstance(path_data, np.ndarray) and isinstance(target_data, np.ndarray):
        #         path_reshaped = path_data.reshape(1, -1) if path_data.ndim == 1 else path_data
        #         target_reshaped = target_data.reshape(1, -1) if target_data.ndim == 1 else target_data
        #         signal["auxiliary"] = np.vstack((path_reshaped, target_reshaped))
        #     else:
        #         signal["auxiliary"] = np.vstack((np.array([path_data]), np.array([target_data])))

        #     signal["auxiliaryname"] = ["Path", "Target"]
        #     self.reference_dropdown.addItem("EMG amplitude")
        #     for name in signal["auxiliaryname"]:
        #         self.reference_dropdown.addItem(name)
        # else:
        #     self.reference_dropdown.addItem("EMG amplitude")

        # self.reference_dropdown.blockSignals(False)

        """ --- """

        # Enable the start button and configuration
        self.start_button.setEnabled(True)

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

                self.ui_plot_reference.clear()

                # Plot all selected channels for preview
                num_preview_channels = min(signal["data"].shape[0], 3)
                num_actual_channels = 0
                colors = ["b", "g", "r", "c", "m", "y"]

                for i in range(num_preview_channels):
                     if i not in self.emg_obj.rejected_channel_indices:
                        num_actual_channels += 1
                        self.ui_plot_reference.plot(
                            time, signal["data"][i, :], pen=pg.mkPen(color=colors[i % len(colors)], width=1)
                        )

                self.ui_plot_reference.setTitle(f"Signal Preview ({num_actual_channels} channels)")
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

            def openEditor():
                # Create the MUeditManual window
                self.mu_edit_window = MUeditManual(filename=self.filename + "_fixed_for_editing.mat", pathname=self.pathname)

                # Show the window without preloading
                self.mu_edit_window.show()

                # Suggest the file to open
                self.edit_field.setText(f"Editor opened. Please select {fixed_filename}")


            # Use existing save_mat_in_background function to save the fixed data
            self.save_mat_in_background(fixed_filename, fixed_data, True, onFinished=openEditor)

            # Update UI
            self.edit_field.setText(f"Preparing data for editing and opening editor...")

        except Exception as e:
            self.edit_field.setText(f"Error opening editing mode: {str(e)}")
            traceback.print_exc()

    # Event handlers
    def save_mat_in_background(self, filename, data, compression=True, onFinished=None):
        self.edit_field.setText("Saving data in background...")

        # Create and configure the worker thread
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)

        worker.finished.connect(lambda: self.on_save_finished(worker))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))
        if onFinished:
            worker.finished.connect(onFinished)

        worker.start()

    def on_save_finished(self, worker):
        self.edit_field.setText("Data saved successfully")
        self.cleanup_thread(worker)
        self.next_button.setEnabled(True)

    def on_save_error(self, worker, error_msg):
        self.edit_field.setText(f"Error saving data: {error_msg}")
        self.cleanup_thread(worker)

    def cleanup_thread(self, worker):
        if worker in self.threads:
            self.threads.remove(worker)

    def start_button_pushed(self):
        algo_choice = self.algo_combo.currentText()
        print(f"Algorithm chosen: {algo_choice}")
        # Reset iteration counter at the start of a new decomposition
        self.iteration_counter = 0
        ui_params = {}

        if algo_choice == "Fast ICA":
            # Get UI parameters
            ui_params = {
                "check_emg": "Yes",   # self.check_emg_dropdown.currentText(),
                "peeloff": self.peeloff_dropdown.currentText(),
                "cov_filter": "Yes",    # self.cov_filter_dropdown.currentText(),
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
        elif algo_choice == "SCD":
            ui_params = {
                "device": "CPU",  # "self.device_dropdown.currentText()",
                "filt_harms": self.filt_harms_dropdown.currentText(),
                "use_coeff_var_fitness": self.use_coeff_var_fitness_dropdown.currentText(),
                "remove_bad_fr": self.remove_bad_fr_dropdown.currentText(),
                "iterations": self.number_iterations_scd_field.value(),
                "acceptance_silhouette": self.acceptance_silhouette_field.value(),
                "extension_factor": self.extension_factor_field.value(),
                "low_pass_cutoff": self.low_pass_cutoff_field.value(),
                "high_pass_cutoff": self.high_pass_cutoff_field.value(),
                "powerline_frequency": self.powerline_frequency_field.value(),
                "peel_off_window_size": self.peel_off_window_size_field.value(),
                "bandwidth": self.bandwidth_field.value()
            }

        # Store UI params and algorithm choice for later use when saving results
        self.ui_params = ui_params
        self.algo_choice = algo_choice

        # Convert UI parameters to algorithm parameters
        parameters = prepare_parameters(ui_params, algo_choice)
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

        decomp_obj = None
        match algo_choice:
            case "Fast ICA":
                decomp_obj = DecompositionWorker
            case "SCD":
                decomp_obj = SCDDecompositionWorker

        # Pass the EMG object to the DecompositionWorker
        self.decomp_worker = decomp_obj(self.emg_obj, parameters)
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
        if self.pathname and self.filename:
            savename = os.path.join(self.pathname, self.filename + "_output_decomp.mat")

            formatted_result = format_results_2(result)

            # Save with parameters
            parameters = prepare_parameters(self.ui_params, self.algo_choice) if hasattr(self, 'ui_params') else {}
            self.save_mat_in_background(savename, {"signal": formatted_result, "parameters": parameters}, True)

            # Store the decomposition result
            self.decomposition_result = formatted_result

        self.edit_field.setText("Decomposition complete")
        self.status_text.setText("Complete")
        self.status_progress.setValue(100)
        self.start_button.setEnabled(True)
        self.save_output_button.setEnabled(True)

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

        # Plot the reference signal
        try:
            if "auxiliary" in self.decomposition_result and "fsamp" in self.decomposition_result:
                index = 0
                # Plot selected auxiliary signal
                for i, aux_name in enumerate(self.decomposition_result["auxiliaryname"][0]):
                    # if aux_name == self.reference_dropdown.currentText():
                    if aux_name == "EMG amplitude":
                        index = i
                        break

                # First auxiliary signal
                reference_signal = self.decomposition_result["auxiliary"][index, :]
                fsamp = self.decomposition_result["fsamp"]
                time_vector = np.arange(reference_signal.shape[0]) / fsamp

                # Clear signal preview plot
                self.ui_plot_reference.clear()
                # Plot new reference signal
                self.ui_plot_reference.plot(time_vector, reference_signal, pen=pg.mkPen(color="#E40000", width=2))

                # Adjust the plot title
                if "auxiliaryname" in self.decomposition_result:
                    name_array = self.decomposition_result["auxiliaryname"]
                    name = name_array[0, 0] if isinstance(name_array[0, 0], str) else str(name_array[0, 0][0])
                    self.ui_plot_reference.setTitle(f"Reference Signal: {name}")
                else:
                    self.ui_plot_reference.setTitle("Reference Signal")
            else:
                print("No reference signal found to plot.")
        except Exception as e:
            print(f"Error plotting reference signal after decomposition: {e}")

        # Save the decomposition state
        try:
            # Import the DecompositionState class
            from core.utils.decomposition_state import DecompositionState

            # Save the state and get metadata
            state_meta = DecompositionState.save_state(self)

            # Add to dashboard's recent visualizations if parent exists
            if hasattr(self, 'parent') and callable(self.parent):
                parent = self.parent()
                if parent is not None and hasattr(parent, 'add_recent_visualization'):
                    parent.add_recent_visualization(state_meta)
                    print(f"Successfully added visualization to dashboard: {state_meta['title']}")
                else:
                    print("Parent exists but does not have add_recent_visualization method")
            else:
                print("No parent available to add visualization to dashboard")
        except Exception as e:
            print(f"Error saving decomposition state: {e}")
            import traceback
            traceback.print_exc()

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

    def update_plots(self, icasig=None, spikes=None, time2=None, sil=None, cov=None):
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

                    self.ui_plot_pulsetrain.setYRange(min(-0.2, min(icasig) * 1.05), max(1.5, max(icasig) * 1.05))

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
        parameters = prepare_parameters(self.ui_params, self.algo_choice) if hasattr(self, "ui_params") else {}

        # Save in background
        self.save_mat_in_background(save_path, {"signal": formatted_result, "parameters": parameters}, True)
        self.edit_field.setText(f"Saving results to {save_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DecompositionApp()
    window.show()
    sys.exit(app.exec_())
