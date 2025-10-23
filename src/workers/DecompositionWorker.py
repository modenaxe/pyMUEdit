from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import traceback
import os
import time
from core.logger import logger

class DecompositionWorker(QThread):
    """
    Worker thread to run EMG decomposition in the background.
    Directly implements the processing flow from emg_main_offline.py.
    """

    progress = pyqtSignal(str, object)
    plot_update = pyqtSignal(object, object, object, object, object)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, emg_obj, parameters):
        """
        Initialize the worker with an emg_obj instance and parameters.

        Args:
            emg_obj: An instance of offline_EMG that has already loaded a file
            parameters: Dictionary of algorithm parameters
        """
        super().__init__()
        self.emg_obj = emg_obj
        self.parameters = parameters

    def run(self):
        """Run the decomposition process in a separate thread."""
        try:
            # Set optimal thread count for matrix operations
            os.environ["OMP_NUM_THREADS"] = "4"
            os.environ["MKL_NUM_THREADS"] = "4"
            os.environ["NUMEXPR_NUM_THREADS"] = "4"
            os.environ["OPENBLAS_NUM_THREADS"] = "4"

            # Map parameters from MUedit to the emg_obj
            self.map_parameters_to_emg_obj()

            # Send initial progress
            self.progress.emit("Formatting electrode configuration...", 0.1)

            # =================== ELECTRODE FORMATTING ===================
            self.emg_obj.electrode_formatter()  # adds spatial context, and additional filtering

            # Manual rejection (only if enabled)
            if self.emg_obj.check_emg:
                self.progress.emit("Checking EMG quality...", 0.15)
                self.emg_obj.manual_rejection()

            # =================== BATCHING SIGNAL =======================
            self.progress.emit("Batching signal...", 0.2)

            if "target" in self.emg_obj.signal_dict and self.emg_obj.signal_dict["target"] is not None:
                self.progress.emit("Target used for batching", 0.2)
                self.emg_obj.batch_w_target()
            else:
                self.emg_obj.batch_wo_target()

            # =================== CONVOLUTIVE SPHERING ==================
            self.progress.emit("Beginning decomposition...", 0.25)

            # ===== DIRECTLY FOLLOWING THE STRUCTURE IN emg_main_offline.py =====
            self.emg_obj.signal_dict["diff_data"] = []
            tracker = 0
            nwins = int(len(self.emg_obj.plateau_coords) / 2)

            # For each electrode
            for g in range(int(self.emg_obj.signal_dict["ngrid"])):
                electrode_progress = 0.25 + (0.6 * g / self.emg_obj.signal_dict["ngrid"])
                self.progress.emit(
                    f"Processing electrode {g+1}/{self.emg_obj.signal_dict['ngrid']}", electrode_progress
                )

                # Calculate extension factor
                extension_factor = int(
                    np.round(self.emg_obj.ext_factor / np.shape(self.emg_obj.signal_dict["batched_data"][tracker])[0])
                )

                # Initialize arrays for extended EMG data PRIOR to removal of edges
                self.emg_obj.signal_dict["extend_obvs_old"] = np.zeros(
                    [
                        nwins,
                        np.shape(self.emg_obj.signal_dict["batched_data"][tracker])[0] * (extension_factor),
                        np.shape(self.emg_obj.signal_dict["batched_data"][tracker])[1]
                        + extension_factor
                        - 1
                        - self.emg_obj.differential_mode,
                    ]
                )
                self.emg_obj.decomp_dict["whitened_obvs_old"] = self.emg_obj.signal_dict["extend_obvs_old"].copy()

                # Initialize arrays for square and inverse of extended EMG data
                self.emg_obj.signal_dict["sq_extend_obvs"] = np.zeros(
                    [
                        nwins,
                        np.shape(self.emg_obj.signal_dict["batched_data"][tracker])[0] * (extension_factor),
                        np.shape(self.emg_obj.signal_dict["batched_data"][tracker])[0] * (extension_factor),
                    ]
                )
                self.emg_obj.signal_dict["inv_extend_obvs"] = self.emg_obj.signal_dict["sq_extend_obvs"].copy()

                # Dewhitening and whitening matrices
                self.emg_obj.decomp_dict["dewhiten_mat"] = self.emg_obj.signal_dict["sq_extend_obvs"].copy()
                self.emg_obj.decomp_dict["whiten_mat"] = self.emg_obj.signal_dict["sq_extend_obvs"].copy()

                # Extended EMG data AFTER removal of edges
                self.emg_obj.signal_dict["extend_obvs"] = self.emg_obj.signal_dict["extend_obvs_old"][
                    :,
                    :,
                    int(np.round(self.emg_obj.signal_dict["fsamp"] * self.emg_obj.edges2remove) - 1) : -int(
                        np.round(self.emg_obj.signal_dict["fsamp"] * self.emg_obj.edges2remove)
                    ),
                ].copy()
                self.emg_obj.decomp_dict["whitened_obvs"] = self.emg_obj.signal_dict["extend_obvs"].copy()

                # For each window interval
                for interval in range(nwins):
                    interval_progress = electrode_progress + (0.6 / self.emg_obj.signal_dict["ngrid"]) * (
                        interval / nwins
                    )
                    self.progress.emit(f"Electrode {g+1}, interval {interval+1}/{nwins}", interval_progress)

                    # Initialize separation matrices and vectors
                    self.emg_obj.decomp_dict["B_sep_mat"] = np.zeros(
                        [np.shape(self.emg_obj.decomp_dict["whitened_obvs"][interval])[0], self.emg_obj.its]
                    )
                    self.emg_obj.decomp_dict["w_sep_vect"] = np.zeros(
                        [np.shape(self.emg_obj.decomp_dict["whitened_obvs"][interval])[0], 1]
                    )
                    self.emg_obj.decomp_dict["MU_filters"] = np.zeros(
                        [nwins, np.shape(self.emg_obj.decomp_dict["whitened_obvs"][interval])[0], self.emg_obj.its]
                    )
                    self.emg_obj.decomp_dict["SILs"] = np.zeros([nwins, self.emg_obj.its])
                    self.emg_obj.decomp_dict["CoVs"] = np.zeros([nwins, self.emg_obj.its])
                    self.emg_obj.decomp_dict["tracker"] = np.zeros([1, self.emg_obj.its])
                    self.emg_obj.decomp_dict["masked_mu_filters"] = []  # Initialize empty list

                    # Run convolutive sphering
                    self.emg_obj.convul_sphering(g, interval, tracker)

                    # Run FastICA with plot callback
                    self.emg_obj.fast_ICA_and_CKC(
                        g,
                        interval,
                        tracker,
                        cf_type=self.parameters.get("contrastfunc", "skew"),
                        plot_callback=self.send_plot_update,
                    )

                    # Send current progress with SIL/CoV information
                    if "SILs" in self.emg_obj.decomp_dict and "CoVs" in self.emg_obj.decomp_dict:
                        sil = np.max(self.emg_obj.decomp_dict["SILs"][interval, :])
                        cov = np.min(self.emg_obj.decomp_dict["CoVs"][interval, :])
                        self.progress.emit(
                            f"Electrode {g+1}, interval {interval+1}: SIL={sil:.4f}, CoV={cov:.4f}", None
                        )

                    tracker += 1

                # Post-process this electrode
                self.progress.emit(f"Post-processing electrode {g+1}...", electrode_progress + 0.1)
                self.emg_obj.post_process_EMG(g)

            # Process across arrays if enabled
            if self.emg_obj.dup_bgrids and sum(self.emg_obj.mus_in_array) > 0:
                self.progress.emit("Processing across arrays...", 0.85)
                self.emg_obj.post_process_across_arrays()

            # Format results for return
            self.progress.emit("Formatting results...", 0.9)
            result = self.format_results()

            # Signal completion
            self.progress.emit("Decomposition complete", 1.0)
            self.finished.emit(result)

        except Exception as e:
            print(f"Exception in DecompositionWorker: {str(e)}")
            traceback.print_exc()
            self.error.emit(str(e))

    def send_plot_update(self, fICA_source, spikes, time2, sil, cov):
        """Send plot update signals to the main UI thread"""
        # Throttle updates to avoid overwhelming the UI
        self.plot_update.emit(fICA_source, spikes, time2, sil, cov)
        # Process events to keep the UI responsive during long computations
        time.sleep(0.01)  # Small delay to prevent UI freezing

    def map_parameters_to_emg_obj(self):
        """Map parameters from MUedit UI to offline_EMG parameters."""
        self.emg_obj.apply_muedit_params(self.parameters)
        self.ref_exist = 1  # We'll check for target in the signal
        self.emg_obj.drawing_mode = 1  # Enable drawing for PyQtGraph updates

    def format_results(self):
        """Format results from offline_EMG to match MUedit's expected format."""
        return self.emg_obj.format_results_1()
