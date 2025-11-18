import scipy
import numpy as np
import os
import scipy.io as sio
from typing import TYPE_CHECKING, Dict, List, Tuple, Any, Optional, Union

from core.utils.io.open_mat import open_mat
from core.logger import logger

from .utils.io.open_otb_plus import open_otb_plus
from .utils.data_processing.electrode_formatter import electrode_formatter
from .utils.preprocessing.notch_filter import notch_filter
from .utils.preprocessing.bandpass_filter import bandpass_filter
from .utils.preprocessing.extend_emg import extend_emg
from .utils.preprocessing.whiten_emg import whiten_emg
from .utils.decomposition.get_spikes import get_spikes
from .utils.decomposition.min_cov_isi import min_cov_isi
from .utils.postprocessing.get_silhouette import get_silhouette
from .utils.decomposition.peel_off import peel_off
from .utils.decomposition.batch_process_filters import batch_process_filters
from .utils.postprocessing.remove_duplicates import remove_duplicates
from .utils.postprocessing.remove_duplicates_between_arrays import remove_duplicates_between_arrays
from .utils.postprocessing.remove_outliers import remove_outliers
from .utils.decomposition.refine_mus import refine_mus
from .utils.decomposition.get_pulse_trains import get_pulse_trains
from .utils.decomposition.get_mu_filters import get_mu_filters
from .utils.decomposition.get_online_parameters import get_online_parameters
from .utils.decomposition.fixed_point_alg import fixed_point_alg
from .utils.decomposition.mathematical_functions import (
    square,
    skew,
    exp,
    logcosh,
    dot_square,
    dot_skew,
    dot_exp,
    dot_logcosh,
)
from core.logger import logger

if TYPE_CHECKING:
    from app.ImportDataWindow import ImportDataWindow

np.random.seed(1337)  # Fixes random generation to get same results each time the script is run


class EMG:
    def __init__(self):
        logger.debug("Initializing EMG base class")
        self.its = 20  # number of iterations of the fixed point algorithm
        self.ref_exist = 1  # if ref_signal exist ref_exist = 1; if not ref_exist = 0 and manual selection of windows
        self.windows = 1  # number of segmented windows over each contraction
        self.check_emg = 1  # 0 = Automatic selection of EMG channels (remove 5% of channels) ; 1 = Visual checking
        self.drawing_mode = 0  # 0 = Output in the command window ; 1 = Output in a figure
        self.differential_mode = 0  # filter out the smallest MU, can improve decomposition at the highest intensities
        self.peel_off = 0  # update the residual EMG by removing the motor units with the highest SIL value
        self.sil_thr = 0.9  # Threshold for SIL values when discarding MUs after two fastICA phases
        self.silthrpeeloff = 0.9  # Threshold for MU removed from the signal (if the sparse deflation is on)
        self.ext_factor = 1000  # extension of observations for numerical stability
        self.edges2remove = 0.2  # Extent of signal clipping after whitening
        self.target_thres = 0.8  # Threshold for segmenting and batching the EMG signals based on a target force profile
        self.initialisation = 0  # initialisation based on the a maximum value in the EMG signal or random
        self.cov_thr = 0.5  # Threshold for CoV values when discarding MUs after two fastICA phases
        self.cov_filter = 1
        self.dup_thr = 0.3  # Correlation threshold for defining a pair of spike trains as derived from the same MU
        self.cov_disch_rate_thr = 0.3
        self.refine_mu = 1
        self.dup_bgrids = 0
        logger.info(f"EMG initialization parameters: its={self.its}, sil_thr={self.sil_thr}, cov_thr={self.cov_thr}")

    def apply_muedit_params(self, parameters):
        """Apply parameters in the format MUedit expects to this object."""
        # Map iteration parameters
        self.its = parameters.get("NITER", 75)
        self.windows = parameters.get("nwindows", 1)

        # Map mode flags
        self.ref_exist = parameters.get("ref_exist", 1)
        self.check_emg = parameters.get("checkEMG", 0)
        self.drawing_mode = parameters.get("drawingmode", 1)
        self.differential_mode = parameters.get("differentialmode", 0)
        self.peel_off = parameters.get("peeloff", 0)
        self.initialisation = parameters.get("initialization", 0)
        self.cov_filter = parameters.get("covfilter", 1)
        self.refine_mu = parameters.get("refineMU", 1)
        self.dup_bgrids = parameters.get("duplicatesbgrids", 0)

        # Map thresholds
        self.sil_thr = parameters.get("silthr", 0.9)
        self.cov_thr = parameters.get("covthr", 0.5)
        self.dup_thr = parameters.get("duplicatesthresh", 0.3)
        self.target_thres = parameters.get("thresholdtarget", 0.8)
        self.ext_factor = parameters.get("nbextchan", 1000)
        self.edges2remove = parameters.get("edges", 0.5)
        self.cov_disch_rate_thr = parameters.get("CoVDR", 0.3)

        # TODO: apply rest of params:
        # - contrastfunc, currently passed as arg
        # - peeloffwin, currently hardcoded in peel_off.py


#######################################################################################################
########################################## OFFLINE EMG ################################################
#######################################################################################################


class offline_EMG(EMG):
    def __init__(self, save_dir: str, to_filter: bool):
        logger.debug(f"Initializing offline_EMG with save_dir={save_dir}, to_filter={to_filter}")
        super().__init__()
        self.save_dir = save_dir  # directory at which final discharges will be saved
        self.to_filter = to_filter  # whether or not you notch and butter filter the
        self.debug_dir = os.path.join(save_dir, "debug_outputs")  # directory for intermediate outputs
        self.save_intermediate = False  # flag to enable/disable saving intermediate outputs

        # Create debug directory if it doesn't exist
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)

        # Initialize attributes that will be set later
        self.signal_dict: Dict[str, Any] = {}
        self.decomp_dict: Dict[str, Any] = {}
        self.mu_dict: Dict[str, Any] = {}
        self.rejected_channel_indices = []
        self.rejected_channels: List[np.ndarray] = []
        self.coordinates: List[np.ndarray] = []
        self.chans_per_electrode: List[int] = []
        self.c_maps: List[int] = []
        self.r_maps: List[int] = []
        self.ied: List[int] = []
        self.emgopt: List[str] = []
        self.ext_number: int = 0
        self.plateau_coords: Union[List[int], np.ndarray] = []
        self.mus_in_array: np.ndarray = np.array([])

        # For plot data communication
        self.current_plot_data = {
            "g": 0,  # Current electrode
            "interval": 0,  # Current interval
            "iteration": 0,  # Current iteration
            "time_axis": None,  # Time axis for plotting
            "fICA_source": None,  # Source signal
            "spikes": None,  # Spike indices
            "sil": 0,  # Silhouette value
            "cov": 0,  # Coefficient of variation
        }

    def save_intermediate_output(self, data: Dict[str, Any], step_name: str, electrode: int = None, interval: int = None, iteration: int = None, sub_iteration: int = None):
        """
        Save intermediate outputs to .mat files for debugging and comparison with MATLAB.

        Args:
            data: Dictionary containing the data to save
            step_name: Name of the processing step
            electrode: Electrode index (optional)
            interval: Interval index (optional)
            iteration: Iteration index (optional)
            sub_iteration: Sub-iteration index (optional)
        """
        if not self.save_intermediate:
            return

        # Create filename with step name and indices
        filename_parts = [step_name]
        if electrode is not None:
            filename_parts.append(f"electrode_{electrode}")
        if interval is not None:
            filename_parts.append(f"interval_{interval}")
        if iteration is not None:
            filename_parts.append(f"iteration_{iteration}")
        if sub_iteration is not None:
            filename_parts.append(f"sub_iteration_{sub_iteration}")

        filename = "_".join(filename_parts) + ".mat"
        filepath = os.path.join(self.debug_dir, filename)

        # Save data to .mat file
        try:
            sio.savemat(filepath, data, do_compression=True)
            logger.debug(f"Saved intermediate output to {filepath}")
        except Exception as e:
            logger.exception(f"Error saving intermediate output to {filepath}: {str(e)}")

        return filepath

    def open_otb_plus(self, inputfile: str, import_window: "ImportDataWindow | None" = None) -> None:
        """
        Opens OTB file and extracts data.
        This is now a wrapper around the standalone open_otb_plus function.
        """
        logger.debug(f"Opening OTB file: {inputfile}")

        self.signal_dict = open_otb_plus(inputfile, import_window)
        self.decomp_dict = {}  # initialising this dictionary here for later use

        # initialising a dictionary that is an empty nested list
        self.mu_dict = dict(pulse_trains=[], discharge_times=[[] for item in range(1)])

        # Save initial signal data for debugging
        if self.save_intermediate:
            self.save_intermediate_output(
                {"signal_dict": self.signal_dict},
                "open_otb"
            )

    def open_mat(self, inputfile: str) -> None:
        """
        Opens MAT file and extracts data.
        """
        logger.debug(f"Opening MAT file: {inputfile}")

        self.signal_dict = open_mat(inputfile)
        self.decomp_dict = {}  # initialising this dictionary here for later use

        # initialising a dictionary that is an empty nested list
        self.mu_dict = dict(pulse_trains=[], discharge_times=[[] for item in range(1)])

    def electrode_formatter(self) -> None:
        """
        Match up the signals with the electrode shape and numbering.
        This is now a wrapper around the standalone electrode_formatter function.
        """
        logger.debug("Starting electrode formatting")
        result = electrode_formatter(self)

        # Save electrode formatting data for debugging
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "coordinates": self.coordinates,
                    "chans_per_electrode": self.chans_per_electrode,
                    "c_maps": self.c_maps,
                    "r_maps": self.r_maps,
                    "ied": self.ied,
                    "emgopt": self.emgopt
                },
                "electrode_formatter"
            )

        return result

    def manual_rejection(self):
        """Manual rejection for channels with noise/artificats (as configured in the Channel Viewer)"""
        logger.debug("Starting channel rejection")
        prev_chans_per_electrode = 0
        total_chans_rejected = 0
        for i in range(self.signal_dict["ngrid"]):
            num_channels = self.chans_per_electrode[i]
            # Initialise the boolean array for each electrode (if it doesn't exist)
            if len(self.rejected_channels) <= i:
                self.rejected_channels.append(np.zeros([num_channels]))

            for j in range(num_channels):
                # If the channel index is rejected, boolean array should be 1 for the
                # corresponding channel
                if j + prev_chans_per_electrode in self.rejected_channel_indices:
                    self.rejected_channels[i][j] = 1
                    total_chans_rejected += 1
                else:
                    self.rejected_channels[i][j] = 0

            prev_chans_per_electrode += num_channels

        logger.debug(f"Channel rejection completed - {total_chans_rejected} channels rejected")

        # Save rejected channels data for debugging
        if self.save_intermediate:
            self.save_intermediate_output(
                {"rejected_channels": self.rejected_channels},
                "manual_rejection"
            )

    def batch_w_target(self):
        logger.debug("Starting signal batching with target")

        plateau = np.where(self.signal_dict["target"] >= max(self.signal_dict["target"]) * self.target_thres)[0]
        logger.info(f"Plateau range: {plateau[0]} to {plateau[-1]}, length: {len(plateau)}")

        discontinuity = np.where(np.diff(plateau) > 1)[0]

        if self.windows > 1 and not discontinuity.size:
            logger.info(f"Multiple windows ({self.windows}) with continuous plateau")
            plat_len = plateau[-1] - plateau[0]
            wind_len = np.floor(plat_len / self.windows)
            batch = np.zeros(self.windows * 2)

            for i in range(self.windows):
                batch[i * 2] = plateau[0] + i * wind_len + 1
                batch[(i + 1) * 2 - 1] = plateau[0] + (i + 1) * wind_len

            self.plateau_coords = batch

        elif self.windows >= 1 and discontinuity.any():
            logger.info(f"Multiple windows with discontinuous plateau")
            prebatch = np.zeros([len(discontinuity) + 1, 2])

            prebatch[0, :] = [plateau[0], plateau[discontinuity[0]]]
            n = len(discontinuity)
            for i, d in enumerate(discontinuity):
                if i < n - 1:
                    prebatch[i + 1, :] = [plateau[d + 1], plateau[discontinuity[i + 1]]]
                else:
                    prebatch[i + 1, :] = [plateau[d + 1], plateau[-1]]

            plat_len = prebatch[:, -1] - prebatch[:, 0]
            wind_len = np.floor(plat_len / self.windows)
            batch = np.zeros([len(discontinuity) + 1, self.windows * 2])

            for i in range(self.windows):
                batch[:, i * 2] = prebatch[:, 0] + i * wind_len + 1
                batch[:, (i + 1) * 2 - 1] = prebatch[:, 0] + (i + 1) * wind_len

            batch = np.sort(batch.reshape([1, np.shape(batch)[0] * np.shape(batch)[1]]))
            self.plateau_coords = batch

        else:
            # the last option is having only one window and no discontinuity in the plateau; Here you leave as is
            logger.info(f"Single window with continuous plateau")
            batch = [plateau[0], plateau[-1]]
            self.plateau_coords = batch

        # with the markers for windows and plateau discontinuities, batch the emg data ready for decomposition
        tracker = 0
        n_intervals = int(len(self.plateau_coords) / 2)
        logger.info(f"Number of intervals: {n_intervals}")
        batched_data = [None] * (self.signal_dict["ngrid"] * n_intervals)

        for i in range(int(self.signal_dict["ngrid"])):
            logger.debug(f"Batching grid {i+1}/{self.signal_dict['ngrid']}")
            electrode = i + 1
            for interval in range(n_intervals):
                start_idx = int(self.plateau_coords[interval * 2])
                end_idx = int(self.plateau_coords[(interval + 1) * 2 - 1]) + 1

                data_slice = self.signal_dict["data"][
                    self.chans_per_electrode[i] * (electrode - 1) : electrode * self.chans_per_electrode[i],
                    start_idx:end_idx,
                ]

                rejected_channels_slice = np.ravel(self.rejected_channels[i]) == 1
                # Remove rejected channels
                batched_data[tracker] = np.delete(data_slice, rejected_channels_slice, 0)
                tracker += 1

        self.signal_dict["batched_data"] = batched_data
        logger.debug(f"Created {len(batched_data)} batched data segments")

        # Save batch processing with target data for debugging
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "plateau_coords": self.plateau_coords,
                    "batched_data_shape": [bd.shape if bd is not None else None for bd in batched_data],
                    "n_intervals": n_intervals
                },
                "batch_w_target"
            )

    def batch_wo_target(self):
        logger.debug("Starting signal batching without target")
        logger.warning("Warning: Manual window selection not implemented in non-interactive mode")

        # Create default window using the entire signal
        start_idx = 0
        end_idx = self.signal_dict["data"].shape[1] - 1

        self.plateau_coords = np.array([start_idx, end_idx])

        # Process similarly to the batched version
        tracker = 0
        n_intervals = int(len(self.plateau_coords) / 2)
        batched_data = [None] * (self.signal_dict["ngrid"] * n_intervals)

        for i in range(int(self.signal_dict["ngrid"])):
            logger.debug(f"Batching grid {i+1}/{self.signal_dict['ngrid']}")
            electrode = i + 1
            for interval in range(n_intervals):
                start_idx = int(self.plateau_coords[interval * 2])
                end_idx = int(self.plateau_coords[(interval + 1) * 2 - 1]) + 1

                data_slice = self.signal_dict["data"][
                    self.chans_per_electrode[i] * (electrode - 1) : electrode * self.chans_per_electrode[i],
                    start_idx:end_idx,
                ]

                rejected_channels_slice = self.rejected_channels[i] == 1
                batched_data[tracker] = np.delete(data_slice, rejected_channels_slice, 0)
                tracker += 1

        self.signal_dict["batched_data"] = batched_data
        logger.debug(f"Created {len(batched_data)} batched data segments")

        # Save batch processing without target data for debugging
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "plateau_coords": self.plateau_coords,
                    "batched_data_shape": [bd.shape if bd is not None else None for bd in batched_data],
                    "n_intervals": n_intervals
                },
                "batch_wo_target"
            )

    ################################ CONVOLUTIVE SPHERING ########################################
    def convul_sphering(self, g, interval, tracker):
        logger.debug(f"Starting convolutive sphering for electrode {g+1}, interval {interval+1}")

        """
        1) Filter the batched EMG data
        2) Extend to improve speed of convergence/reduce numerical instability
        3) Remove any DC component
        4) Whiten
        """

        # Save raw data before processing
        if self.save_intermediate:
            self.save_intermediate_output(
                {"raw_data": self.signal_dict["batched_data"][tracker].copy()},
                "convul_sphering", g, interval, 0
            )

        if self.to_filter:
            # Apply notch and bandpass filters
            self.signal_dict["batched_data"][tracker] = notch_filter(
                self.signal_dict["batched_data"][tracker], self.signal_dict["fsamp"]
            )

            # Save notch filtered data
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"notch_filtered_data": self.signal_dict["batched_data"][tracker].copy()},
                    "convul_sphering", g, interval, 1
                )

            self.signal_dict["batched_data"][tracker] = bandpass_filter(
                self.signal_dict["batched_data"][tracker], self.signal_dict["fsamp"], emg_type=self.emgopt[g]
            )

            # Save bandpass filtered data
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"bandpass_filtered_data": self.signal_dict["batched_data"][tracker].copy()},
                    "convul_sphering", g, interval, 2
                )

        # differentiation - typical EMG generation model treats low amplitude spikes/MUs as noise
        if self.differential_mode:  # just a basic 1st order differential (bipolar processing)
            self.signal_dict["batched_data"][tracker] = np.diff(self.signal_dict["batched_data"][tracker], n=1, axis=-1)

            # Save differentiated data
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"differentiated_data": self.signal_dict["batched_data"][tracker].copy()},
                    "convul_sphering", g, interval, 3
                )

        # signal extension - increasing the number of channels to 1000
        # Holobar 2007 -  Multichannel Blind Source Separation using Convolutive Kernel Compensation
        extension_factor = int(np.round(self.ext_factor / len(self.signal_dict["batched_data"][tracker])))
        self.ext_number = extension_factor

        # Extend EMG observations
        self.signal_dict["extend_obvs_old"][interval] = extend_emg(
            self.signal_dict["extend_obvs_old"][interval], self.signal_dict["batched_data"][tracker], extension_factor
        )

        # Save extended data
        if self.save_intermediate:
            self.save_intermediate_output(
                {"extended_data": self.signal_dict["extend_obvs_old"][interval].copy()},
                "convul_sphering", g, interval, 4
            )

        # Compute signal covariance matrix
        self.signal_dict["sq_extend_obvs"][interval] = (
            self.signal_dict["extend_obvs_old"][interval] @ self.signal_dict["extend_obvs_old"][interval].T
        ) / np.shape(self.signal_dict["extend_obvs_old"][interval])[1]

        # Save covariance matrix
        if self.save_intermediate:
            self.save_intermediate_output(
                {"covariance_matrix": self.signal_dict["sq_extend_obvs"][interval].copy()},
                "convul_sphering", g, interval, 5
            )

        # Compute pseudoinverse
        self.signal_dict["inv_extend_obvs"][interval] = np.linalg.pinv(self.signal_dict["sq_extend_obvs"][interval])

        # Save pseudoinverse
        if self.save_intermediate:
            self.save_intermediate_output(
                {"pseudoinverse": self.signal_dict["inv_extend_obvs"][interval].copy()},
                "convul_sphering", g, interval, 6
            )

        # de-mean the extended emg observation matrix
        self.signal_dict["extend_obvs_old"][interval] = scipy.signal.detrend(
            self.signal_dict["extend_obvs_old"][interval], axis=-1, type="constant", bp=0
        )

        # Save detrended data
        if self.save_intermediate:
            self.save_intermediate_output(
                {"detrended_data": self.signal_dict["extend_obvs_old"][interval].copy()},
                "convul_sphering", g, interval, 7
            )

        # whiten the signal
        (
            self.decomp_dict["whitened_obvs_old"][interval],
            self.decomp_dict["whiten_mat"][interval],
            self.decomp_dict["dewhiten_mat"][interval],
        ) = whiten_emg(self.signal_dict["extend_obvs_old"][interval])

        # Save whitened data and matrices
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "whitened_data": self.decomp_dict["whitened_obvs_old"][interval].copy(),
                    "whiten_matrix": self.decomp_dict["whiten_mat"][interval].copy(),
                    "dewhiten_matrix": self.decomp_dict["dewhiten_mat"][interval].copy()
                },
                "convul_sphering", g, interval, 8
            )

        # remove the edges
        edge_samples = int(np.round(self.signal_dict["fsamp"] * self.edges2remove))

        self.signal_dict["extend_obvs"][interval] = self.signal_dict["extend_obvs_old"][interval][
            :,
            edge_samples - 1 : -edge_samples,
        ]

        self.decomp_dict["whitened_obvs"][interval] = self.decomp_dict["whitened_obvs_old"][interval][
            :,
            edge_samples - 1 : -edge_samples,
        ]

        # Save edge-trimmed data
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "trimmed_extended_data": self.signal_dict["extend_obvs"][interval].copy(),
                    "trimmed_whitened_data": self.decomp_dict["whitened_obvs"][interval].copy(),
                    "edge_samples": edge_samples
                },
                "convul_sphering", g, interval, 9
            )

        # Update plateau coordinates for first electrode only
        if g == 0:
            old_start = self.plateau_coords[interval * 2]
            old_end = self.plateau_coords[(interval + 1) * 2 - 1]

            self.plateau_coords[interval * 2] = old_start + edge_samples - 1
            self.plateau_coords[(interval + 1) * 2 - 1] = old_end - edge_samples

            # Save updated plateau coordinates
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"updated_plateau_coords": self.plateau_coords.copy()},
                    "convul_sphering", g, interval, 10
                )

        logger.debug(f"Completed convolutive sphering for electrode {g+1}, interval {interval+1}")

    ######################### FAST ICA AND CONVOLUTIVE KERNEL COMPENSATION  ############################################

    def fast_ICA_and_CKC(self, g, interval, tracker, cf_type="skew", plot_callback=None):
        logger.debug(f"Starting FastICA for electrode {g+1}, interval {interval+1}, contrast={cf_type}, iterations={self.its}")

        init_its = np.zeros([self.its], dtype=int)  # tracker of initialisaitons of separation vectors across iterations
        fpa_its = 500  # maximum number of iterations for the fixed point algorithm

        Z = np.array(self.decomp_dict["whitened_obvs"][interval]).copy()
        time_axis = np.linspace(0, np.shape(Z)[1], np.shape(Z)[1]) / self.signal_dict["fsamp"]

        # Save initial data for debugging
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "Z_initial": Z.copy(),
                    "time_axis": time_axis,
                    "init_its": init_its.copy(),
                    "fpa_its": fpa_its
                },
                "fast_ICA_and_CKC", g, interval, 0
            )

        # Save contrast function choice
        if self.save_intermediate:
            self.save_intermediate_output(
                {"contrast_function": cf_type},
                "fast_ICA_and_CKC", g, interval, 1
            )

        for i in range(self.its):

            # stop flag check
            if hasattr(self, 'should_stop') and self.should_stop:
                logger.info(f"FastICA stopped at iteration {i+1}/{self.its} due to stop flag")
                logger.info(f"Decomposition stoppped before FastICA at electrode {g+1}, interval {interval+1}")
                return

            #################### FIXED POINT ALGORITHM #################################
            if self.initialisation:
                # generate a random vector
                random_init = np.random.randn(
                    self.decomp_dict["whitened_obvs"][interval].shape[0],
                    self.decomp_dict["whitened_obvs"][interval].shape[0],
                )
                self.decomp_dict["w_sep_vect"] = random_init[:, 0]

                # Save random initialization
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"random_init": random_init.copy(), "w_sep_vect_initial": self.decomp_dict["w_sep_vect"].copy()},
                        "fast_ICA_and_CKC", g, interval, i+2, 0
                    )
            else:
                if i == 0:
                    # identify the time instant at which the maximum of the squared summation of all whitened extended observation vectors
                    sort_sq_sum_Z = np.argsort(np.square(np.sum(Z, axis=0)))

                    # Save sorted squared sum
                    if self.save_intermediate:
                        self.save_intermediate_output(
                            {"sort_sq_sum_Z": sort_sq_sum_Z.copy()},
                            "fast_ICA_and_CKC", g, interval, i+2, 1
                        )

                init_its[i] = sort_sq_sum_Z[-(i + 1)]
                self.decomp_dict["w_sep_vect"] = Z[:, int(init_its[i])].copy()

                # Save initialization from data
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"init_its_i": init_its[i], "w_sep_vect_initial": self.decomp_dict["w_sep_vect"].copy()},
                        "fast_ICA_and_CKC", g, interval, i+2, 2
                    )

            # orthogonalise and normalize separation vector
            self.decomp_dict["w_sep_vect"] -= np.dot(
                self.decomp_dict["B_sep_mat"] @ self.decomp_dict["B_sep_mat"].T, self.decomp_dict["w_sep_vect"]
            )
            self.decomp_dict["w_sep_vect"] /= np.linalg.norm(self.decomp_dict["w_sep_vect"])

            # Save orthogonalized and normalized vector
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"w_sep_vect_orthonormalized": self.decomp_dict["w_sep_vect"].copy()},
                    "fast_ICA_and_CKC", g, interval, i+2, 3
                )

            # use the fixed point algorithm to identify consecutive separation vectors
            self.decomp_dict["w_sep_vect"] = fixed_point_alg(
                self.decomp_dict["w_sep_vect"], self.decomp_dict["B_sep_mat"], Z, cf_type, fpa_its
            )

            # Save fixed point algorithm result
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"w_sep_vect_after_fpa": self.decomp_dict["w_sep_vect"].copy()},
                    "fast_ICA_and_CKC", g, interval, i+2, 4
                )

            # get the first iteration of spikes using k means ++
            fICA_source, spikes = get_spikes(self.decomp_dict["w_sep_vect"], Z, self.signal_dict["fsamp"])

            # Save spikes detection results
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"fICA_source": fICA_source.copy(), "spikes": spikes.copy() if len(spikes) > 0 else np.array([])},
                    "fast_ICA_and_CKC", g, interval, i+2, 5
                )

            ################# MINIMISATION OF COV OF DISCHARGES ############################
            if len(spikes) > 10:
                # determine the interspike interval
                ISI = np.diff(spikes / self.signal_dict["fsamp"])
                # determine the coefficient of variation
                CoV = np.std(ISI) / np.mean(ISI)

                # Save ISI and CoV
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"ISI": ISI.copy(), "CoV_initial": CoV},
                        "fast_ICA_and_CKC", g, interval, i+2, 6
                    )

                # update the sepearation vector by summing all the spikes
                w_n_p1 = np.sum(Z[:, spikes], axis=1)

                # Save updated separation vector
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"w_n_p1": w_n_p1.copy()},
                        "fast_ICA_and_CKC", g, interval, i+2, 7
                    )

                # minimisation of covariance of interspike intervals
                self.decomp_dict["MU_filters"][interval][:, i], spikes, self.decomp_dict["CoVs"][interval, i] = (
                    min_cov_isi(w_n_p1, Z, self.signal_dict["fsamp"], CoV, spikes)
                )

                # Save min_cov_isi results
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {
                            "MU_filters_i": self.decomp_dict["MU_filters"][interval][:, i].copy(),
                            "spikes_after_min_cov_isi": spikes.copy(),
                            "CoV_after_min_cov_isi": self.decomp_dict["CoVs"][interval, i]
                        },
                        "fast_ICA_and_CKC", g, interval, i+2, 8
                    )

                self.decomp_dict["B_sep_mat"][:, i] = self.decomp_dict["w_sep_vect"].real

                # Save updated B_sep_mat
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"B_sep_mat_i": self.decomp_dict["B_sep_mat"][:, i].copy()},
                        "fast_ICA_and_CKC", g, interval, i+2, 9
                    )

                # calculate SIL
                fICA_source, spikes, self.decomp_dict["SILs"][interval, i] = get_silhouette(
                    self.decomp_dict["MU_filters"][interval][:, i], Z, self.signal_dict["fsamp"]
                )

                # Save silhouette results
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {
                            "fICA_source_after_silhouette": fICA_source.copy(),
                            "spikes_after_silhouette": spikes.copy(),
                            "SIL_value": self.decomp_dict["SILs"][interval, i]
                        },
                        "fast_ICA_and_CKC", g, interval, i+2, 10
                    )

                # peel off
                if self.peel_off == 1 and self.decomp_dict["SILs"][interval, i] > self.sil_thr:
                    Z_before_peel = Z.copy() if self.save_intermediate else None
                    Z = peel_off(Z, spikes, self.signal_dict["fsamp"])

                    # Save peel off results
                    # very slow
                    # if self.save_intermediate:
                    #     self.save_intermediate_output(
                    #         {"Z_before_peel": Z_before_peel, "Z_after_peel": Z.copy()},
                    #         "fast_ICA_and_CKC", g, interval, i+2, 11
                    #     )

                logger.debug(
                    f"Iteration {i+1}/{self.its} - SIL: {self.decomp_dict['SILs'][interval, i]:.4f}, "
                    f"CoV: {self.decomp_dict['CoVs'][interval, i]:.4f}, Spikes: {len(spikes)}"
                )

                # Store data for plotting
                self.current_plot_data = {
                    "g": g,
                    "interval": interval,
                    "iteration": i,
                    "time_axis": time_axis,
                    "fICA_source": fICA_source,
                    "spikes": spikes,
                    "sil": self.decomp_dict["SILs"][interval, i],
                    "cov": self.decomp_dict["CoVs"][interval, i],
                }

                # Save current plot data
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"current_plot_data": self.current_plot_data.copy()},
                        "fast_ICA_and_CKC", g, interval, i+2, 12
                    )

                # Call the plot callback if provided
                if plot_callback is not None and self.drawing_mode:
                    plot_callback(
                        fICA_source,
                        spikes,
                        time_axis,
                        self.decomp_dict["SILs"][interval, i],
                        self.decomp_dict["CoVs"][interval, i],
                    )

                # stop check
                if hasattr(self, 'should_stop') and self.should_stop:
                    logger.info(f"FastICA stopped during iteration {i+1}/{self.its} after plot callback")
                    logger.info(f"Decomposition stoppped before FastICA at electrode {g+1}, interval {interval+1}")
                    return

            else:
                logger.info(f"Electrode #{g+1} - Iteration #{i+1} - less than 10 spikes")
                # without enough spikes, we skip minimising the covariation of discharges
                self.decomp_dict["B_sep_mat"][:, i] = self.decomp_dict["w_sep_vect"].real

                # Save B_sep_mat for case with few spikes
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"B_sep_mat_i_few_spikes": self.decomp_dict["B_sep_mat"][:, i].copy()},
                        "fast_ICA_and_CKC", g, interval, i+2, 13
                    )

        ####################################### MU FILTER THRESHOLDING ###############################################

        # Apply thresholds
        logger.debug("\nApplying thresholds to MU filters...")
        SIL_condition = self.decomp_dict["SILs"][interval, :] >= self.sil_thr
        final_condition = SIL_condition.copy()

        # Save SIL condition
        if self.save_intermediate:
            self.save_intermediate_output(
                {"SIL_condition": SIL_condition.copy(), "sil_thr": self.sil_thr},
                "fast_ICA_and_CKC", g, interval, self.its+2, 0
            )

        if self.cov_filter:
            CoV_condition = self.decomp_dict["CoVs"][interval, :] <= self.cov_thr
            final_condition = SIL_condition & CoV_condition
            logger.info(f"Units meeting both criteria: {np.sum(final_condition)}/{self.its}")

            # Save CoV condition and final condition
            if self.save_intermediate:
                self.save_intermediate_output(
                    {
                        "CoV_condition": CoV_condition.copy(),
                        "cov_thr": self.cov_thr,
                        "final_condition": final_condition.copy(),
                        "units_meeting_criteria": np.sum(final_condition)
                    },
                    "fast_ICA_and_CKC", g, interval, self.its+2, 1
                )

        mask = np.broadcast_to(
            final_condition.reshape(1, -1), (np.shape(self.decomp_dict["whitened_obvs"][interval])[0], self.its)
        )

        # Save mask
        if self.save_intermediate:
            self.save_intermediate_output(
                {"mask": mask.copy()},
                "fast_ICA_and_CKC", g, interval, self.its+2, 2
            )

        if np.sum(final_condition) > 0:
            masked_filters = self.decomp_dict["MU_filters"][interval][mask].reshape(
                np.shape(self.decomp_dict["whitened_obvs"][interval])[0], np.sum(mask, axis=1)[0]
            )
            self.decomp_dict["masked_mu_filters"].append(masked_filters)
            logger.info(f"Extracted {np.sum(final_condition)} motor units that meet thresholds")

            # Save masked filters
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"masked_mu_filters": masked_filters.copy()},
                    "fast_ICA_and_CKC", g, interval, self.its+2, 3
                )
        else:
            # Create an empty array with proper dimensions to avoid errors later
            empty_array = np.zeros((np.shape(self.decomp_dict["whitened_obvs"][interval])[0], 0))
            self.decomp_dict["masked_mu_filters"].append(empty_array)
            logger.warning("No motor units met the threshold criteria")

            # Save empty array
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"empty_masked_mu_filters": empty_array.copy()},
                    "fast_ICA_and_CKC", g, interval, self.its+2, 4
                )

        # Save final state
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "final_Z": Z.copy(),
                    "final_SILs": self.decomp_dict["SILs"][interval, :].copy(),
                    "final_CoVs": self.decomp_dict["CoVs"][interval, :].copy(),
                    "final_MU_filters": self.decomp_dict["MU_filters"][interval].copy(),
                    "final_B_sep_mat": self.decomp_dict["B_sep_mat"].copy()
                },
                "fast_ICA_and_CKC", g, interval, self.its+2, 5
            )

        logger.debug(f"FastICA and CKC completed for electrode {g+1}, interval {interval+1}")

    ################################################## POST PROCESSING #######################################################

    def post_process_EMG(self, electrode):
        logger.debug(f"Starting post-processing for electrode {electrode+1}")

        # Save initial state
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "electrode": electrode,
                    "whitened_obvs_shape": [w.shape if w is not None else None for w in self.decomp_dict["whitened_obvs"]],
                    "masked_mu_filters_shape": [m.shape if m is not None else None for m in self.decomp_dict["masked_mu_filters"]],
                    "plateau_coords": self.plateau_coords.copy() if isinstance(self.plateau_coords, np.ndarray) else self.plateau_coords,
                    "ext_number": self.ext_number,
                    "differential_mode": self.differential_mode
                },
                "post_process_EMG", electrode, 0
            )

        self.mus_in_array = np.zeros(self.signal_dict["ngrid"])
        electrode += 1

        # batch processing over each window
        pulse_trains, discharge_times = batch_process_filters(
            self.decomp_dict["whitened_obvs"],
            self.decomp_dict["masked_mu_filters"],
            self.plateau_coords,
            self.ext_number,
            self.differential_mode,
            np.shape(self.signal_dict["data"])[1],
            self.signal_dict["fsamp"],
        )

        # Save batch process results
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "pulse_trains_shape": pulse_trains.shape if hasattr(pulse_trains, "shape") else None,
                    "discharge_times_length": len(discharge_times) if discharge_times else 0
                },
                "post_process_EMG", electrode, 1
            )

        if pulse_trains.size > 0:  # if there are existing MUs
            logger.info(f"Found {np.shape(pulse_trains)[0]} motor units")
            self.mus_in_array[electrode - 1] = 1

            # removing duplicate MUs
            discharge_times_new, pulse_trains_new, mu_filters_new = remove_duplicates(
                pulse_trains,
                discharge_times,
                discharge_times,
                np.squeeze(self.decomp_dict["masked_mu_filters"]),
                np.round(self.signal_dict["fsamp"] / 40),
                0.00025,
                self.dup_thr,
                self.signal_dict["fsamp"],
            )
            logger.info(f"After duplicate removal: {len(discharge_times_new)} motor units")

            # Save duplicate removal results
            if self.save_intermediate:
                self.save_intermediate_output(
                    {
                        "discharge_times_new_length": len(discharge_times_new),
                        "pulse_trains_new_shape": pulse_trains_new.shape if hasattr(pulse_trains_new, "shape") else None,
                        "mu_filters_new_shape": mu_filters_new.shape if hasattr(mu_filters_new, "shape") else None
                    },
                    "post_process_EMG", electrode, 2
                )

            self.decomp_dict["masked_mu_filters"] = []
            self.decomp_dict["masked_mu_filters"] = mu_filters_new

            if self.refine_mu:
                # removing outliers generating irrelvant discharge rates
                discharge_times_new = remove_outliers(
                    pulse_trains_new, discharge_times_new, self.signal_dict["fsamp"], self.cov_disch_rate_thr
                )

                # Save outlier removal results
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"discharge_times_after_outlier_removal": len(discharge_times_new)},
                        "post_process_EMG", electrode, 3
                    )

                # refining motor units
                pulse_trains_new, discharge_times_new = refine_mus(
                    self.signal_dict["data"][
                        self.chans_per_electrode[electrode - 1]
                        * (electrode - 1) : electrode
                        * self.chans_per_electrode[electrode - 1],
                        :,
                    ],
                    self.rejected_channels[electrode - 1],
                    pulse_trains_new,
                    discharge_times_new,
                    self.signal_dict["fsamp"],
                )

                # Save refine_mus results
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {
                            "pulse_trains_after_refine_shape": pulse_trains_new.shape if hasattr(pulse_trains_new, "shape") else None,
                            "discharge_times_after_refine": len(discharge_times_new)
                        },
                        "post_process_EMG", electrode, 4
                    )

                # removing outliers second pass
                discharge_times_new = remove_outliers(
                    pulse_trains_new, discharge_times_new, self.signal_dict["fsamp"], self.cov_disch_rate_thr
                )

                # Save second outlier removal results
                if self.save_intermediate:
                    self.save_intermediate_output(
                        {"discharge_times_after_second_outlier_removal": len(discharge_times_new)},
                        "post_process_EMG", electrode, 5
                    )

            logger.info(f"Adding {np.shape(pulse_trains_new)[0]} pulse trains to results")
            self.mu_dict["pulse_trains"].append(pulse_trains_new)
        else:
            logger.info(f"No motor units found for electrode {electrode}")

        if electrode != 1:
            self.mu_dict["discharge_times"].append([])

        if not discharge_times_new:
            raise ValueError("No discharge times found")

        for j in range(len(discharge_times_new)):
            self.mu_dict["discharge_times"][electrode - 1].append(discharge_times_new[j])

        # Save final results
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "final_discharge_times_count": len(self.mu_dict["discharge_times"][electrode - 1]),
                    "final_pulse_trains_shape": self.mu_dict["pulse_trains"][-1].shape if hasattr(self.mu_dict["pulse_trains"][-1], "shape") else None,
                    "mus_in_array": self.mus_in_array.copy()
                },
                "post_process_EMG", electrode, 6
            )

        logger.debug(f"Post-processing completed for electrode {electrode}")

    def post_process_EMG_for_biofeedback(self, electrode, interval):
        logger.debug(f"Starting biofeedback post-processing for electrode {electrode+1}")

        # Save initial state
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "electrode": electrode,
                    "interval": interval,
                    "masked_mu_filters_shape": self.decomp_dict["masked_mu_filters"].shape if hasattr(self.decomp_dict["masked_mu_filters"], "shape") else None,
                    "dewhiten_mat_shape": self.decomp_dict["dewhiten_mat"][interval].shape if hasattr(self.decomp_dict["dewhiten_mat"][interval], "shape") else None
                },
                "post_process_EMG_for_biofeedback", electrode, interval, 0
            )

        self.mus_in_array = np.zeros(self.signal_dict["ngrid"])
        electrode += 1

        # Dewhiten MU filters
        self.decomp_dict["masked_mu_filters"] = (
            self.decomp_dict["dewhiten_mat"][interval] @ self.decomp_dict["masked_mu_filters"]
        )

        # Save dewhitened filters
        if self.save_intermediate:
            self.save_intermediate_output(
                {"dewhitened_mu_filters": self.decomp_dict["masked_mu_filters"].copy()},
                "post_process_EMG_for_biofeedback", electrode, interval, 1
            )

        # get the pulse train for the entire signal
        pulse_trains, discharge_times, ext_factor = get_pulse_trains(
            self.signal_dict["data"],
            self.rejected_channels,
            self.decomp_dict["masked_mu_filters"],
            self.chans_per_electrode,
            self.signal_dict["fsamp"],
            electrode - 1,
        )

        # Save pulse trains and discharge times
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "pulse_trains_shape": pulse_trains.shape if hasattr(pulse_trains, "shape") else None,
                    "discharge_times_length": len(discharge_times) if discharge_times else 0,
                    "ext_factor": ext_factor
                },
                "post_process_EMG_for_biofeedback", electrode, interval, 2
            )

        if np.shape(pulse_trains)[0] > 0:  # if there are existing MUs
            logger.info(f"Found {np.shape(pulse_trains)[0]} motor units")
            self.mus_in_array[electrode - 1] = 1

            # removing duplicate MUs
            discharge_times_new, _, _ = remove_duplicates(
                pulse_trains,
                discharge_times,
                discharge_times,
                np.squeeze(self.decomp_dict["masked_mu_filters"]),
                np.round(self.signal_dict["fsamp"] / 40),
                0.00025,
                self.dup_thr,
                self.signal_dict["fsamp"],
            )
            logger.info(f"After duplicate removal: {len(discharge_times_new)} motor units")

            # Save after duplicate removal
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"discharge_times_new_length": len(discharge_times_new)},
                    "post_process_EMG_for_biofeedback", electrode, interval, 3
                )

            del pulse_trains, discharge_times

            # get the decomposition parameters for the biofeedback
            new_mu_filters = get_mu_filters(
                self.signal_dict["data"],
                self.rejected_channels,
                discharge_times_new,
                self.chans_per_electrode,
                electrode - 1,
            )

            # Save new MU filters
            if self.save_intermediate:
                self.save_intermediate_output(
                    {"new_mu_filters_shape": new_mu_filters.shape if hasattr(new_mu_filters, "shape") else None},
                    "post_process_EMG_for_biofeedback", electrode, interval, 4
                )

            # find the pulse trains again
            pulse_trains, discharge_times, _ = get_pulse_trains(
                self.signal_dict["data"],
                self.rejected_channels,
                self.decomp_dict["masked_mu_filters"],
                self.chans_per_electrode,
                self.signal_dict["fsamp"],
                electrode - 1,
            )

            # Save new pulse trains
            if self.save_intermediate:
                self.save_intermediate_output(
                    {
                        "pulse_trains_new_shape": pulse_trains.shape if hasattr(pulse_trains, "shape") else None,
                        "discharge_times_new_length": len(discharge_times) if discharge_times else 0
                    },
                    "post_process_EMG_for_biofeedback", electrode, interval, 5
                )

            # get online parameters
            _, inv_extended_data, norm, centroids = get_online_parameters(
                self.signal_dict["data"],
                self.rejected_channels,
                new_mu_filters,
                self.chans_per_electrode,
                self.signal_dict["fsamp"],
                electrode - 1,
            )

            # Save online parameters
            if self.save_intermediate:
                self.save_intermediate_output(
                    {
                        "inv_extended_data_shape": inv_extended_data.shape if hasattr(inv_extended_data, "shape") else None,
                        "norm_shape": norm.shape if hasattr(norm, "shape") else None,
                        "centroids_shape": centroids.shape if hasattr(centroids, "shape") else None
                    },
                    "post_process_EMG_for_biofeedback", electrode, interval, 6
                )

            # Save parameters to MU dictionary
            self.mu_dict["pulse_trains"].append(pulse_trains)
            self.mu_dict["inv_extended_data"].append(inv_extended_data)
            self.mu_dict["norm"].append(norm)
            self.mu_dict["centroids"].append(centroids)
            self.mu_dict["mu_filters"].append(new_mu_filters)
        else:
            logger.info(f"No motor units found for electrode {electrode}")

        if electrode != 1:
            self.mu_dict["discharge_times"].append([])

        for j in range(len(discharge_times)):
            self.mu_dict["discharge_times"][electrode - 1].append(discharge_times[j])

        # Save final state
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "final_discharge_times_count": len(self.mu_dict["discharge_times"][electrode - 1]),
                    "final_pulse_trains_shape": self.mu_dict["pulse_trains"][-1].shape if len(self.mu_dict["pulse_trains"]) > 0 and hasattr(self.mu_dict["pulse_trains"][-1], "shape") else None,
                    "mus_in_array": self.mus_in_array.copy()
                },
                "post_process_EMG_for_biofeedback", electrode, interval, 7
            )

        logger.debug(f"Biofeedback post-processing completed for electrode {electrode}")

    def post_process_across_arrays(self):
        logger.debug("Starting post-processing across arrays")
        logger.debug(f"Duplicate between grids: {self.dup_bgrids}")

        # Save initial parameters
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "dup_bgrids": self.dup_bgrids,
                    "dup_thr": self.dup_thr,
                    "fsamp": self.signal_dict["fsamp"]
                },
                "post_process_across_arrays", 0
            )
    
        if not hasattr(self, 'mu_dict') or not isinstance(self.mu_dict, dict):
            logger.warning("mu_dict not properly initialized")
            self.mu_dict = {"pulse_trains": [], "discharge_times": []}
        
        if "pulse_trains" not in self.mu_dict or not isinstance(self.mu_dict["pulse_trains"], list):
            logger.warning("pulse_trains not properly initialized")
            self.mu_dict["pulse_trains"] = []
            
        if "discharge_times" not in self.mu_dict or not isinstance(self.mu_dict["discharge_times"], list):
            logger.warning("discharge_times not properly initialized")
            self.mu_dict["discharge_times"] = []

        mu_count = 0
        no_arrays = len(self.mu_dict["pulse_trains"])
        logger.info(f"Found {no_arrays} electrode arrays with data")

        # save array counts with bounds checking
        array_motor_unit_counts = []

        for i in range(no_arrays):
            if (i < len(self.mu_dict["pulse_trains"]) and 
                isinstance(self.mu_dict["pulse_trains"][i], np.ndarray) and 
                self.mu_dict["pulse_trains"][i].size > 0):
                
                motor_unit_count = (
                    self.mu_dict["pulse_trains"][i].shape[0]
                    if hasattr(self.mu_dict["pulse_trains"][i], "shape")
                    else len(self.mu_dict["pulse_trains"][i])
                )
                logger.info(f"Array {i+1} has {motor_unit_count} motor units")
                array_motor_unit_counts.append(motor_unit_count)
                mu_count += motor_unit_count
            else:
                logger.info(f"Array {i+1} has no motor units")
                array_motor_unit_counts.append(0)

        logger.info(f"Total motor unit count: {mu_count}")

        # Save motor unit counts
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "no_arrays": no_arrays,
                    "array_motor_unit_counts": array_motor_unit_counts,
                    "total_mu_count": mu_count
                },
                "post_process_across_arrays", 1
            )

        if mu_count == 0:
            logger.debug("No motor units found, skipping cross-array processing")
            self.mu_dict["muscle"] = np.array([])
            return

        # ensure signal target exists and has proper shape
        if "target" not in self.signal_dict or self.signal_dict["target"] is None:
            logger.warning("No target signal found, using default size")
            if "data" in self.signal_dict and self.signal_dict["data"] is not None:
                signal_length = self.signal_dict["data"].shape[1]
            else:
                signal_length = 1000
        else:
            signal_length = np.shape(self.signal_dict["target"])[0]

        all_pulse_trains = np.zeros([mu_count, signal_length])
        all_discharge_times = []
        muscle = np.zeros(mu_count, dtype=int)

        mu = 0
        logger.debug("Consolidating motor units from all arrays...")
        for i in range(no_arrays):  # iterating over arrays
            # bounds check for pulse_trains
            if (i < len(self.mu_dict["pulse_trains"]) and 
                isinstance(self.mu_dict["pulse_trains"][i], np.ndarray) and 
                self.mu_dict["pulse_trains"][i].size > 0):
                
                motor_unit_count = (
                    self.mu_dict["pulse_trains"][i].shape[0]
                    if hasattr(self.mu_dict["pulse_trains"][i], "shape")
                    else len(self.mu_dict["pulse_trains"][i])
                )

                # iterating over the mus per array
                for j in range(motor_unit_count):
                    # bounds check for both pulse_trains and discharge_times
                    if (mu < mu_count and 
                        j < self.mu_dict["pulse_trains"][i].shape[0] and
                        i < len(self.mu_dict["discharge_times"]) and
                        j < len(self.mu_dict["discharge_times"][i])):
                        
                        # additional shape check for pulse train
                        pulse_train = self.mu_dict["pulse_trains"][i][j]
                        if len(pulse_train) <= signal_length:
                            all_pulse_trains[mu, :len(pulse_train)] = pulse_train
                        else:
                            # truncate if pulse train is longer than expected
                            all_pulse_trains[mu, :] = pulse_train[:signal_length]
                        
                        all_discharge_times.append(self.mu_dict["discharge_times"][i][j])
                        muscle[mu] = i
                        mu += 1
                    else:
                        logger.warning(f"Skipping MU {j} in array {i} due to bounds check failure")

        # Save consolidated data
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "all_pulse_trains_shape": all_pulse_trains.shape,
                    "all_discharge_times_length": len(all_discharge_times),
                    "muscle": muscle.copy()
                },
                "post_process_across_arrays", 2
            )

        logger.debug("Removing duplicates across arrays...")
        discharge_times_new, pulse_trains_new, muscle_new = remove_duplicates_between_arrays(
            all_pulse_trains,
            all_discharge_times,
            muscle,
            np.round(self.signal_dict["fsamp"] / 40),
            0.00025,
            self.dup_thr,
            self.signal_dict["fsamp"],
        )
        logger.info(f"After duplicate removal: {len(discharge_times_new)} motor units")

        # Save after duplicate removal
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "discharge_times_new_length": len(discharge_times_new),
                    "pulse_trains_new_shape": pulse_trains_new.shape,
                    "muscle_new": muscle_new.copy()
                },
                "post_process_across_arrays", 3
            )

        # Regroup motor units by electrode
        logger.debug("Regrouping motor units by electrode...")
        del self.mu_dict["discharge_times"]
        self.mu_dict["discharge_times"] = [[]]  # empty nested list

        del self.mu_dict["pulse_trains"]
        self.mu_dict["pulse_trains"] = []

        # Save regrouping initialization
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "discharge_times_initialized": True,
                    "pulse_trains_initialized": True
                },
                "post_process_across_arrays", 4
            )

        for i in range(no_arrays):
            if i != 0:
                self.mu_dict["discharge_times"].append([])

            idx = np.where(muscle_new == i)[0]  # find the indices for mu -> array mapping
            logger.info(f"Found {len(idx)} MUs for array {i+1}")

            # bounds check for pulse_trains_new
            if len(idx) > 0 and all(j < len(pulse_trains_new) for j in idx):
                self.mu_dict["pulse_trains"].append(pulse_trains_new[idx])
            else:
                # create empty array with proper dimensions
                self.mu_dict["pulse_trains"].append(np.zeros((0, signal_length)))
                logger.warning(f"Created empty pulse_trains for array {i+1}")

            # Get number of motor units safely
            motor_unit_count = 0
            if hasattr(self.mu_dict["pulse_trains"][i], "shape"):
                motor_unit_count = self.mu_dict["pulse_trains"][i].shape[0]
            elif hasattr(self.mu_dict["pulse_trains"][i], "__len__"):
                motor_unit_count = len(self.mu_dict["pulse_trains"][i])

            # bounds check for discharge_times access
            for j in range(motor_unit_count):
                if (j < len(idx) and 
                    idx[j] < len(discharge_times_new) and
                    i < len(self.mu_dict["discharge_times"])):
                    self.mu_dict["discharge_times"][i].append(discharge_times_new[idx[j]])
                else:
                    # add empty discharge times if bounds check fails
                    self.mu_dict["discharge_times"][i].append(np.array([]))
                    logger.warning(f"Added empty discharge_times for array {i+1}, MU {j}")

            # Save per-electrode regrouping
            if self.save_intermediate:
                self.save_intermediate_output(
                    {
                        f"electrode_{i}_idx": idx.copy() if isinstance(idx, np.ndarray) else idx,
                        f"electrode_{i}_pulse_trains_shape": self.mu_dict["pulse_trains"][i].shape if hasattr(self.mu_dict["pulse_trains"][i], "shape") else None,
                        f"electrode_{i}_discharge_times_length": len(self.mu_dict["discharge_times"][i])
                    },
                    "post_process_across_arrays", 5, i
                )

        self.mu_dict["muscle"] = muscle_new

        # Save final state
        if self.save_intermediate:
            self.save_intermediate_output(
                {
                    "final_muscle": muscle_new.copy(),
                    "final_pulse_trains_count": len(self.mu_dict["pulse_trains"]),
                    "final_discharge_times_count": len(self.mu_dict["discharge_times"])
                },
                "post_process_across_arrays", 6
            )

        logger.debug("Processing across electrodes complete")

    # TODO: merge these, right now they've just been pulled out of their previous
    # tightly-coupled homes (DecompositionWorker and DecompositionApp) without any
    # modification.
    def format_results_1(self):
        """Format results from offline_EMG to match MUedit's expected format."""
        # Create a clean output structure
        result = {}

        # Copy essential fields from the original signal
        for field in self.signal_dict:
            if field not in [
                "batched_data",
                "extend_obvs",
                "extend_obvs_old",
                "filtered_data",
                "sq_extend_obvs",
                "inv_extend_obvs",
                "diff_data",
            ]:
                result[field] = self.signal_dict[field]

        # Add spatial information
        if hasattr(self, "coordinates"):
            result["coordinates"] = self.coordinates
        if hasattr(self, "ied"):
            result["IED"] = self.ied
            if hasattr(self, "rejected_channels"):
                result["EMGmask"] = self.rejected_channels

        # Format pulse trains and discharge times using the exact format expected by MUedit
        result["Pulsetrain"] = {}
        result["Dischargetimes"] = {}

        if len(self.mu_dict["pulse_trains"]) > 0:
            for electrode, pulse_trains in enumerate(self.mu_dict["pulse_trains"]):
                if isinstance(pulse_trains, np.ndarray) and pulse_trains.shape[0] > 0:
                    result["Pulsetrain"][electrode] = pulse_trains

                    # Check if discharge_times is available for this electrode
                    if electrode < len(self.mu_dict["discharge_times"]):
                        for mu, discharge_times in enumerate(self.mu_dict["discharge_times"][electrode]):
                            if discharge_times is not None and len(discharge_times) > 0:
                                result["Dischargetimes"][(electrode, mu)] = discharge_times

        return result

def format_results_2(result):
    """
    Returns the results of decomposition in the same format as MATLAB's `signal`
    structure.
    """
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

    return formatted_result
