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
        self.should_stop = False
    
    def stop(self):
        """Stop the decomposition worker"""
        logger.info("DecompositionWorker.stop() called")
        self.should_stop = True
        
        # set stop flag on the EMG object so FastICA can see it
        if hasattr(self, 'emg_obj'):
            setattr(self.emg_obj, 'should_stop', True)
            logger.debug("Stop flag set on EMG object for FastICA")
        
        logger.debug("Stop flag set for decomposition worker")

    def cleanup_incomplete_decomposition(self):
        """Clean up incomplete decomposition data to prevent errors"""
        try:
            logger.info("cleaning up incoplete decomposition data")

            # reset mu directories to prevent index error
            if hasattr(self.emg_obj, 'mu_dict'):
                self.emg_obj.mu_dict["pulse_trains"] = []
            
                if hasattr(self.emg_obj, 'signal_dict'):
                    num_electrodes = getattr(self.emg_obj.signal_dict, 'ngrid', 1)
                else:
                    num_electrodes = 1

                # initialise the discharge_times list for each electrode
                self.emg_obj.mu_dict["discharge_times"] = [[] for _ in range(num_electrodes)]

                logger.info(f"reset mu dictionaries for {num_electrodes} electrodes")

            # reset decomposition dictioniaries
            if hasattr(self.emg_obj, 'decomp_dict'):
                self.emg_obj.decomp_dict["masked_mu_filters"] = []

            logger.debug("clean up completed successfully")
        
        except Exception as cleanup_error:
            logger.exception(f"error during clean up: {cleanup_error}")

    def run(self):
        """Run the decomposition process in a separate thread."""
        try:
            # Set optimal thread count for matrix operations
            os.environ["OMP_NUM_THREADS"] = "4"
            os.environ["MKL_NUM_THREADS"] = "4"
            os.environ["NUMEXPR_NUM_THREADS"] = "4"
            os.environ["OPENBLAS_NUM_THREADS"] = "4"

            if self.should_stop:
                logger.info("Decomposition stoppped before starting")
                self.cleanup_incomplete_decomposition()
                return

            # Map parameters from MUedit to the emg_obj
            self.map_parameters_to_emg_obj()

            if self.should_stop:
                logger.info("Decomposition stoppped after parameter mapping")
                self.cleanup_incomplete_decomposition()
                return

            # Send initial progress
            self.progress.emit("Formatting electrode configuration...", 0.1)

            # =================== ELECTRODE FORMATTING ===================
            self.emg_obj.electrode_formatter()  # adds spatial context, and additional filtering

            if self.should_stop:
                logger.info("Decomposition stoppped after electrode formatting")
                self.cleanup_incomplete_decomposition()
                return

            # Manual rejection (only if enabled)
            if self.emg_obj.check_emg:
                self.progress.emit("Checking EMG quality...", 0.15)
                self.emg_obj.manual_rejection()

            if self.should_stop:
                logger.info("Decomposition stoppped after manual rejection")
                self.cleanup_incomplete_decomposition()
                return

            # =================== BATCHING SIGNAL =======================
            self.progress.emit("Batching signal...", 0.2)

            if "target" in self.emg_obj.signal_dict and self.emg_obj.signal_dict["target"] is not None:
                self.progress.emit("Target used for batching", 0.2)
                logger.info("Target detected — using target-based batching")
                logger.debug(f"Target shape: {self.emg_obj.signal_dict['target'].shape}")
                logger.debug(f"Target max value: {np.max(self.emg_obj.signal_dict['target'])}")
                self.emg_obj.batch_w_target()
            else:
                logger.info("No target present — using batching without target")
                logger.debug("Signal keys present: %s", list(self.emg_obj.signal_dict.keys()))
                self.emg_obj.batch_wo_target()

            if self.should_stop:
                logger.info("Decomposition stoppped after batching")
                self.cleanup_incomplete_decomposition()
                return

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

                    if self.should_stop:
                        logger.info(f"Decomposition stoppped before convolutive sphering at electrode {g+1}, interval {interval+1}")
                        self.cleanup_incomplete_decomposition()
                        return

                    # Run convolutive sphering
                    self.emg_obj.convul_sphering(g, interval, tracker)

                    if self.should_stop:
                        logger.info(f"Decomposition stoppped before FastICA at electrode {g+1}, interval {interval+1}")
                        self.cleanup_incomplete_decomposition()
                        return

                    # Run FastICA with plot callback
                    self.emg_obj.fast_ICA_and_CKC(
                        g,
                        interval,
                        tracker,
                        cf_type=self.parameters.get("contrastfunc", "skew"),
                        plot_callback=self.send_plot_update,
                    )

                    if self.should_stop:
                        logger.info(f"Decomposition stoppped after FastICA at electrode {g+1}, interval {interval+1}")
                        self.cleanup_incomplete_decomposition()
                        return

                    # Send current progress with SIL/CoV information
                    if "SILs" in self.emg_obj.decomp_dict and "CoVs" in self.emg_obj.decomp_dict:
                        sil = np.max(self.emg_obj.decomp_dict["SILs"][interval, :])
                        cov = np.min(self.emg_obj.decomp_dict["CoVs"][interval, :])
                        self.progress.emit(
                            f"Electrode {g+1}, interval {interval+1}: SIL={sil:.4f}, CoV={cov:.4f}", None
                        )

                    tracker += 1

                if self.should_stop:
                    logger.info(f"Decomposition stoppped before post-processing electrode {g+1}")
                    self.cleanup_incomplete_decomposition()
                    return

                # Post-process this electrode
                self.progress.emit(f"Post-processing electrode {g+1}...", electrode_progress + 0.1)
                self.emg_obj.post_process_EMG(g)
            
            if self.should_stop:
                logger.info(f"Decomposition stoppped before processing across arrays")
                self.cleanup_incomplete_decomposition()
                return

            # Process across arrays if enabled
            if self.emg_obj.dup_bgrids and sum(self.emg_obj.mus_in_array) > 0:
                self.progress.emit("Processing across arrays...", 0.85)
                self.emg_obj.post_process_across_arrays()

            if self.should_stop:
                logger.info(f"Decomposition stoppped before formatting results")
                self.cleanup_incomplete_decomposition()
                return

            # Format results for return
            self.progress.emit("Formatting results...", 0.9)
            result = self.format_results()

            # Signal completion
            if not self.should_stop:
                self.progress.emit("Decomposition complete", 1.0)
                self.finished.emit(result)
            else:
                logger.info("Decomposition was stopped by user")

        except Exception as e:
            if not self.should_stop:
                logger.exception(f"Exception in DecompositionWorker: {str(e)}")
                self.error.emit(str(e))
            else:
                logger.debug("Decomposition stopped by user during processing")

    def send_plot_update(self, fICA_source, spikes, time2, sil, cov):
        """Send plot update signals to the main UI thread"""
        
        # CHECK FOR STOP FLAG IN PLOT CALLBACK (called during each FastICA iteration)
        if getattr(self, 'should_stop', False):
            logger.info("Plot update detected stop flag - stopping FastICA")
            # Set stop flag on EMG object so FastICA iterations will stop
            if hasattr(self, 'emg_obj'):
                setattr(self.emg_obj, 'should_stop', True)
                logger.debug("Stop flag propagated to EMG object")
            return  # Don't send plot update, just return to stop the iteration
        
        # Send the plot update if not stopping
        self.plot_update.emit(fICA_source, spikes, time2, sil, cov)

    def map_parameters_to_emg_obj(self):
        """Map parameters from MUedit UI to offline_EMG parameters."""
        self.emg_obj.apply_muedit_params(self.parameters)
        self.ref_exist = 1  # We'll check for target in the signal
        self.emg_obj.drawing_mode = 1  # Enable drawing for PyQtGraph updates

    def format_results(self):
        """Format results from offline_EMG to match MUedit's expected format."""
        return self.emg_obj.format_results_1()
