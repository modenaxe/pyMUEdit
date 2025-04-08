import os
import sys
import traceback
import numpy as np
import scipy.io as sio
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
)

# Import UI module
from gui.MUeditUI import setup_ui

from utils.config_and_input.openOTBplus import openOTBplus
from utils.config_and_input.segmentsession import SegmentSession
from SaveMatWorker import SaveMatWorker
from DecompositionWorker import DecompositionWorker
from HDEMGdecomposition import prepare_parameters


class MUedit(QMainWindow):
    def __init__(self):
        super().__init__()

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

        # Initialize UI using the imported setup function
        setup_ui(self)

    # Event handlers
    def tabs_value_changed(self, value):
        if value == "DECOMPOSITION":
            self.panel.setVisible(True)
            self.panel_4.setVisible(False)
            self.panel_3.setVisible(False)
            self.panel_2.setVisible(True)
        else:
            self.panel.setVisible(False)
            self.panel_4.setVisible(True)
            self.panel_3.setVisible(True)
            self.panel_2.setVisible(False)

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

    def select_file_button_pushed(self):
        file, path = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
        if not file:
            return

        self.filename = os.path.basename(file)
        self.pathname = os.path.dirname(file) + "/"
        self.edit_field_saving_3.setText(self.filename)

        self.select_file_button.setStyleSheet(
            "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.set_configuration_button.setStyleSheet(
            "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.segment_session_button.setStyleSheet(
            "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.start_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;"
        )
        QApplication.processEvents()

        # Load files
        ext = os.path.splitext(self.filename)[1]
        if ext == ".otb+":  # OT Biolab+
            self.MUdecomp["config"], signal, savename = openOTBplus(self.pathname, self.filename, 1)
            if self.MUdecomp["config"]:
                self.MUdecomp["config"].hide()
                self.set_configuration_button.setEnabled(True)

            if savename:
                self.save_mat_in_background(savename, {"signal": signal}, True)

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

        savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
        self.save_mat_in_background(savename, {"signal": signal}, True)
        self.select_file_button.setStyleSheet(
            "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
        )

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

        parameters = prepare_parameters(ui_params)

        # Load signal data
        if self.pathname and self.filename:
            savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
        file = sio.loadmat(savename)
        signal = file["signal"]

        # Disable the start button during processing
        self.start_button.setEnabled(False)
        self.edit_field.setText("Starting decomposition...")
        self.decomp_worker = DecompositionWorker(signal, parameters)
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

            if "gridname" in formatted_result:
                gridname = formatted_result["gridname"]
                gridname_obj = np.empty((1, len(gridname)), dtype=object)

                # Fill the array with grid names
                for i, name in enumerate(gridname):
                    gridname_obj[0, i] = str(name)

                formatted_result["gridname"] = gridname_obj

            if "muscle" in formatted_result:
                muscle = formatted_result["muscle"]
                muscle_obj = np.empty((1, len(muscle)), dtype=object)

                # Fill the array with grid names
                for i, name in enumerate(muscle):
                    muscle_obj[0, i] = str(name)

                formatted_result["muscle"] = muscle_obj

            if "auxiliaryname" in formatted_result:
                auxname = formatted_result["auxiliaryname"]
                auxname_obj = np.empty((1, len(auxname)), dtype=object)

                # Fill the array with grid names
                for i, name in enumerate(auxname):
                    auxname_obj[0, i] = str(name)

                formatted_result["auxiliaryname"] = auxname_obj

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

            parameters = prepare_parameters(self.ui_params) if hasattr(self, "ui_params") else {}
            self.save_mat_in_background(savename, {"signal": formatted_result, "parameters": parameters}, True)

        self.edit_field.setText("Decomposition complete")
        self.start_button.setEnabled(True)

        if hasattr(self, "decomp_worker") and self.decomp_worker in self.threads:
            self.threads.remove(self.decomp_worker)

    def on_decomposition_error(self, error_msg):
        """Handle errors during decomposition"""
        self.edit_field.setText(f"Error in decomposition: {error_msg}")
        self.start_button.setEnabled(True)

        if hasattr(self, "decomp_worker") and self.decomp_worker in self.threads:
            self.threads.remove(self.decomp_worker)

    def update_progress(self, message, progress=None):
        self.edit_field.setText(message)
        # Update any progress bars if needed

    def update_plots(self, time, target, plateau_coords, icasig=None, spikes=None, time2=None, sil=None, cov=None):
        """Update plot displays during decomposition using PyQtGraph"""
        try:
            self.iteration_counter += 1

            if sil is not None and cov is not None:
                self.edit_field.setText(f"Iteration #{self.iteration_counter}: SIL = {sil:.4f}, CoV = {cov:.4f}")

            # Only update plots every 5 iterations
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
                time, target, pen=pg.mkPen(color="#f0f0f0", width=2, style=Qt.PenStyle.DashLine)
            )

            # Plot plateau markers if available
            if plateau_coords is not None and len(plateau_coords) >= 2:
                try:
                    if len(time) > max(plateau_coords):
                        for coord in plateau_coords[:2]:  # Just plot the first two markers
                            line = pg.InfiniteLine(pos=time[coord], angle=90, pen=pg.mkPen(color="#d95535", width=2))
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
                    self.ui_plot_pulsetrain.plot(time2, icasig, pen=pg.mkPen(color="#f0f0f0", width=1))

                    if spikes is not None and len(spikes) > 0:
                        valid_indices = [i for i in spikes if i < len(time2)]
                        if valid_indices:
                            scatter = pg.ScatterPlotItem(
                                x=[time2[i] for i in valid_indices],
                                y=[icasig[i] for i in valid_indices],
                                size=10,
                                pen=pg.mkPen(None),
                                brush=pg.mkBrush("#d95535"),
                            )
                            self.ui_plot_pulsetrain.addItem(scatter)

                    self.ui_plot_pulsetrain.setYRange(-0.2, 1.5)

                    # Update title with SIL and CoV values if available
                    if sil is not None and cov is not None:
                        title = f"Iteration #{self.iteration_counter}: SIL = {sil:.4f}, CoV = {cov:.4f}"
                        self.ui_plot_pulsetrain.setTitle(title, color="#f0f0f0")

                except Exception as e:
                    print(f"Warning: Error plotting decomposition results: {e}")
                    traceback.print_exc()

        except Exception as e:
            print(f"Error in update_plots: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MUedit()
    window.show()
    sys.exit(app.exec_())
