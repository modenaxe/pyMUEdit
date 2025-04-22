import scipy
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union

from .utils.config_and_input.open_otb import open_otb
from .utils.config_and_input.electrode_formatter import electrode_formatter
from .utils.decomposition.notch_filter import notch_filter
from .utils.decomposition.bandpass_filter import bandpass_filter
from .utils.decomposition.extend_emg import extend_emg
from .utils.decomposition.whiten_emg import whiten_emg
from .utils.decomposition.get_spikes import get_spikes
from .utils.decomposition.min_cov_isi import min_cov_isi
from .utils.decomposition.get_silhouette import get_silhouette
from .utils.decomposition.peel_off import peel_off
from .utils.decomposition.batch_process_filters import batch_process_filters
from .utils.decomposition.remove_duplicates import remove_duplicates
from .utils.decomposition.remove_duplicates_between_arrays import remove_duplicates_between_arrays
from .utils.decomposition.remove_outliers import remove_outliers
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

np.random.seed(1337)  # Fixes random generation to get same results each time the script is run


class EMG:
    def __init__(self):
        print("Initializing EMG base class")
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
        self.refine_mu = 1
        self.dup_bgrids = 0
        print(f"EMG initialization parameters: its={self.its}, sil_thr={self.sil_thr}, cov_thr={self.cov_thr}")


#######################################################################################################
########################################## OFFLINE EMG ################################################
#######################################################################################################


class offline_EMG(EMG):
    def __init__(self, save_dir: str, to_filter: bool):
        print(f"Initializing offline_EMG with save_dir={save_dir}, to_filter={to_filter}")
        super().__init__()
        self.save_dir = save_dir  # directory at which final discharges will be saved
        self.to_filter = to_filter  # whether or not you notch and butter filter the

        # Initialize attributes that will be set later
        self.signal_dict: Dict[str, Any] = {}
        self.decomp_dict: Dict[str, Any] = {}
        self.mu_dict: Dict[str, Any] = {}
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

    def open_otb(self, inputfile: str) -> None:
        """
        Opens OTB file and extracts data.
        This is now a wrapper around the standalone open_otb function.
        """
        print(f"Opening OTB file: {inputfile}")
        return open_otb(self, inputfile)

    def electrode_formatter(self) -> None:
        """
        Match up the signals with the electrode shape and numbering.
        This is now a wrapper around the standalone electrode_formatter function.
        """
        print("Starting electrode formatting")
        return electrode_formatter(self)

    def manual_rejection(self):
        """Manual rejection for channels with noise/artificats by inspecting plots of the electrode channels"""
        print("Starting manual channel rejection")
        print("Automatic channel acceptance - no channels will be rejected")

        for i in range(self.signal_dict["nelectrodes"]):
            # Make sure rejected_channels is initialized
            if len(self.rejected_channels) <= i:
                self.rejected_channels.append(np.zeros(self.chans_per_electrode[i] + 1))
            else:
                # Reset any previously rejected channels to zero
                self.rejected_channels[i][:] = 0

            self.rejected_channels[i] = self.rejected_channels[i][1:]

        print("Channel rejection completed - all channels accepted")

    def batch_w_target(self):
        print("Starting signal batching with target")

        plateau = np.where(self.signal_dict["target"] >= max(self.signal_dict["target"]) * self.target_thres)[0]
        print(f"Plateau range: {plateau[0]} to {plateau[-1]}, length: {len(plateau)}")

        discontinuity = np.where(np.diff(plateau) > 1)[0]

        if self.windows > 1 and not discontinuity.size:
            print(f"Multiple windows ({self.windows}) with continuous plateau")
            plat_len = plateau[-1] - plateau[0]
            wind_len = np.floor(plat_len / self.windows)
            batch = np.zeros(self.windows * 2)

            for i in range(self.windows):
                batch[i * 2] = plateau[0] + i * wind_len + 1
                batch[(i + 1) * 2 - 1] = plateau[0] + (i + 1) * wind_len

            self.plateau_coords = batch

        elif self.windows >= 1 and discontinuity.any():
            print(f"Multiple windows with discontinuous plateau")
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
            print(f"Single window with continuous plateau")
            batch = [plateau[0], plateau[-1]]
            self.plateau_coords = batch

        # with the markers for windows and plateau discontinuities, batch the emg data ready for decomposition
        tracker = 0
        n_intervals = int(len(self.plateau_coords) / 2)
        print(f"Number of intervals: {n_intervals}")
        batched_data = [None] * (self.signal_dict["nelectrodes"] * n_intervals)

        for i in range(int(self.signal_dict["nelectrodes"])):
            print(f"Batching electrode {i+1}/{self.signal_dict['nelectrodes']}")
            electrode = i + 1
            for interval in range(n_intervals):
                start_idx = int(self.plateau_coords[interval * 2])
                end_idx = int(self.plateau_coords[(interval + 1) * 2 - 1]) + 1

                data_slice = self.signal_dict["data"][
                    self.chans_per_electrode[i] * (electrode - 1) : electrode * self.chans_per_electrode[i],
                    start_idx:end_idx,
                ]

                rejected_channels_slice = self.rejected_channels[i] == 1

                # Remove rejected channels
                batched_data[tracker] = np.delete(data_slice, rejected_channels_slice, 0)
                tracker += 1

        self.signal_dict["batched_data"] = batched_data
        print(f"Created {len(batched_data)} batched data segments")

    def batch_wo_target(self):
        print("Starting signal batching without target")
        print("Warning: Manual window selection not implemented in non-interactive mode")

        # Create default window using the entire signal
        start_idx = 0
        end_idx = self.signal_dict["data"].shape[1] - 1

        self.plateau_coords = np.array([start_idx, end_idx])

        # Process similarly to the batched version
        tracker = 0
        n_intervals = int(len(self.plateau_coords) / 2)
        batched_data = [None] * (self.signal_dict["nelectrodes"] * n_intervals)

        for i in range(int(self.signal_dict["nelectrodes"])):
            print(f"Batching electrode {i+1}/{self.signal_dict['nelectrodes']}")
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
        print(f"Created {len(batched_data)} batched data segments")

    ################################ CONVOLUTIVE SPHERING ########################################
    def convul_sphering(self, g, interval, tracker):
        print(f"Starting convolutive sphering for electrode {g+1}, interval {interval+1}")

        """
        1) Filter the batched EMG data 
        2) Extend to improve speed of convergence/reduce numerical instability 
        3) Remove any DC component  
        4) Whiten
        """

        if self.to_filter:
            # Apply notch and bandpass filters
            self.signal_dict["batched_data"][tracker] = notch_filter(
                self.signal_dict["batched_data"][tracker], self.signal_dict["fsamp"]
            )
            self.signal_dict["batched_data"][tracker] = bandpass_filter(
                self.signal_dict["batched_data"][tracker], self.signal_dict["fsamp"], emg_type=self.emgopt[g]
            )

        # differentiation - typical EMG generation model treats low amplitude spikes/MUs as noise
        if self.differential_mode:  # just a basic 1st order differential (bipolar processing)
            self.signal_dict["batched_data"][tracker] = np.diff(self.signal_dict["batched_data"][tracker], n=1, axis=-1)

        # signal extension - increasing the number of channels to 1000
        # Holobar 2007 -  Multichannel Blind Source Separation using Convolutive Kernel Compensation
        extension_factor = int(np.round(self.ext_factor / len(self.signal_dict["batched_data"][tracker])))
        self.ext_number = extension_factor

        # Extend EMG observations
        self.signal_dict["extend_obvs_old"][interval] = extend_emg(
            self.signal_dict["extend_obvs_old"][interval], self.signal_dict["batched_data"][tracker], extension_factor
        )

        # Compute signal covariance matrix
        self.signal_dict["sq_extend_obvs"][interval] = (
            self.signal_dict["extend_obvs_old"][interval] @ self.signal_dict["extend_obvs_old"][interval].T
        ) / np.shape(self.signal_dict["extend_obvs_old"][interval])[1]

        # Compute pseudoinverse
        self.signal_dict["inv_extend_obvs"][interval] = np.linalg.pinv(self.signal_dict["sq_extend_obvs"][interval])

        # de-mean the extended emg observation matrix
        self.signal_dict["extend_obvs_old"][interval] = scipy.signal.detrend(
            self.signal_dict["extend_obvs_old"][interval], axis=-1, type="constant", bp=0
        )

        # whiten the signal
        (
            self.decomp_dict["whitened_obvs_old"][interval],
            self.decomp_dict["whiten_mat"][interval],
            self.decomp_dict["dewhiten_mat"][interval],
        ) = whiten_emg(self.signal_dict["extend_obvs_old"][interval])

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

        # Update plateau coordinates for first electrode only
        if g == 0:
            old_start = self.plateau_coords[interval * 2]
            old_end = self.plateau_coords[(interval + 1) * 2 - 1]

            self.plateau_coords[interval * 2] = old_start + edge_samples - 1
            self.plateau_coords[(interval + 1) * 2 - 1] = old_end - edge_samples

        print(f"Completed convolutive sphering for electrode {g+1}, interval {interval+1}")

    ######################### FAST ICA AND CONVOLUTIVE KERNEL COMPENSATION  ############################################

    def fast_ICA_and_CKC(self, g, interval, tracker, cf_type="square", plot_callback=None):
        print(f"Starting FastICA for electrode {g+1}, interval {interval+1}, contrast={cf_type}, iterations={self.its}")

        init_its = np.zeros([self.its], dtype=int)  # tracker of initialisaitons of separation vectors across iterations
        fpa_its = 500  # maximum number of iterations for the fixed point algorithm

        Z = np.array(self.decomp_dict["whitened_obvs"][interval]).copy()
        time_axis = np.linspace(0, np.shape(Z)[1], np.shape(Z)[1]) / self.signal_dict["fsamp"]

        # Choose contrast function
        if cf_type == "square":
            cf, dot_cf = square, dot_square
        elif cf_type == "skew":
            cf, dot_cf = skew, dot_skew
        elif cf_type == "exp":
            cf, dot_cf = exp, dot_exp
        elif cf_type == "logcosh":
            cf, dot_cf = logcosh, dot_logcosh

        for i in range(self.its):

            #################### FIXED POINT ALGORITHM #################################
            if self.initialisation:
                # generate a random vector
                random_init = np.random.randn(
                    self.decomp_dict["whitened_obvs"][interval].shape[0],
                    self.decomp_dict["whitened_obvs"][interval].shape[0],
                )
                self.decomp_dict["w_sep_vect"] = random_init[:, 0]
            else:
                if i == 0:
                    # identify the time instant at which the maximum of the squared summation of all whitened extended observation vectors
                    sort_sq_sum_Z = np.argsort(np.square(np.sum(Z, axis=0)))

                init_its[i] = sort_sq_sum_Z[-(i + 1)]
                self.decomp_dict["w_sep_vect"] = Z[:, int(init_its[i])].copy()

            # orthogonalise and normalize separation vector
            self.decomp_dict["w_sep_vect"] -= np.dot(
                self.decomp_dict["B_sep_mat"] @ self.decomp_dict["B_sep_mat"].T, self.decomp_dict["w_sep_vect"]
            )
            self.decomp_dict["w_sep_vect"] /= np.linalg.norm(self.decomp_dict["w_sep_vect"])

            # use the fixed point algorithm to identify consecutive separation vectors
            self.decomp_dict["w_sep_vect"] = fixed_point_alg(
                self.decomp_dict["w_sep_vect"], self.decomp_dict["B_sep_mat"], Z, cf, dot_cf, fpa_its
            )

            # get the first iteration of spikes using k means ++
            fICA_source, spikes = get_spikes(self.decomp_dict["w_sep_vect"], Z, self.signal_dict["fsamp"])

            ################# MINIMISATION OF COV OF DISCHARGES ############################
            if len(spikes) > 1:
                # determine the interspike interval
                ISI = np.diff(spikes / self.signal_dict["fsamp"])
                # determine the coefficient of variation
                CoV = np.std(ISI) / np.mean(ISI)

                # update the sepearation vector by summing all the spikes
                w_n_p1 = np.sum(Z[:, spikes], axis=1)

                # minimisation of covariance of interspike intervals
                self.decomp_dict["MU_filters"][interval][:, i], spikes, self.decomp_dict["CoVs"][interval, i] = (
                    min_cov_isi(w_n_p1, self.decomp_dict["B_sep_mat"], Z, self.signal_dict["fsamp"], CoV, spikes)
                )

                self.decomp_dict["B_sep_mat"][:, i] = self.decomp_dict["w_sep_vect"].real

                # calculate SIL
                fICA_source, spikes, self.decomp_dict["SILs"][interval, i] = get_silhouette(
                    self.decomp_dict["MU_filters"][interval][:, i], Z, self.signal_dict["fsamp"]
                )

                # peel off
                if self.peel_off == 1 and self.decomp_dict["SILs"][interval, i] > self.sil_thr:
                    Z = peel_off(Z, spikes, self.signal_dict["fsamp"])

                print(
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

                # Call the plot callback if provided
                if plot_callback is not None and self.drawing_mode:
                    plot_callback(
                        time_axis,
                        self.signal_dict["target"],
                        self.plateau_coords,
                        fICA_source,
                        spikes,
                        time_axis,
                        self.decomp_dict["SILs"][interval, i],
                        self.decomp_dict["CoVs"][interval, i],
                    )

            else:
                print(f"Electrode #{g+1} - Iteration #{i+1} - less than 10 spikes")
                # without enough spikes, we skip minimising the covariation of discharges
                self.decomp_dict["B_sep_mat"][:, i] = self.decomp_dict["w_sep_vect"].real

        ####################################### MU FILTER THRESHOLDING ###############################################

        # Apply thresholds
        print("\nApplying thresholds to MU filters...")
        SIL_condition = self.decomp_dict["SILs"][interval, :] >= self.sil_thr
        final_condition = SIL_condition.copy()

        if self.cov_filter:
            CoV_condition = self.decomp_dict["CoVs"][interval, :] <= self.cov_thr
            final_condition = SIL_condition & CoV_condition
            print(f"Units meeting both criteria: {np.sum(final_condition)}/{self.its}")

        mask = np.broadcast_to(
            final_condition.reshape(1, -1), (np.shape(self.decomp_dict["whitened_obvs"][interval])[0], self.its)
        )

        if np.sum(final_condition) > 0:
            self.decomp_dict["masked_mu_filters"].append(
                self.decomp_dict["MU_filters"][interval][mask].reshape(
                    np.shape(self.decomp_dict["whitened_obvs"][interval])[0], np.sum(mask, axis=1)[0]
                )
            )
            print(f"Extracted {np.sum(final_condition)} motor units that meet thresholds")
        else:
            # Create an empty array with proper dimensions to avoid errors later
            self.decomp_dict["masked_mu_filters"].append(
                np.zeros((np.shape(self.decomp_dict["whitened_obvs"][interval])[0], 0))
            )
            print("WARNING: No motor units met the threshold criteria")

        print(f"FastICA and CKC completed for electrode {g+1}, interval {interval+1}")

    ################################################## POST PROCESSING #######################################################

    def post_process_EMG(self, electrode):
        print(f"Starting post-processing for electrode {electrode+1}")

        self.mus_in_array = np.zeros(self.signal_dict["nelectrodes"])
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

        if pulse_trains.size > 0:  # if there are existing MUs
            print(f"Found {np.shape(pulse_trains)[0]} motor units")
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
            print(f"After duplicate removal: {len(discharge_times_new)} motor units")

            self.decomp_dict["masked_mu_filters"] = []
            self.decomp_dict["masked_mu_filters"] = mu_filters_new

            if self.refine_mu:
                # removing outliers generating irrelvant discharge rates
                discharge_times_new = remove_outliers(
                    pulse_trains_new, discharge_times_new, self.signal_dict["fsamp"], self.cov_thr
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

                # removing outliers second pass
                discharge_times_new = remove_outliers(
                    pulse_trains_new, discharge_times_new, self.signal_dict["fsamp"], self.cov_thr
                )

            print(f"Adding {np.shape(pulse_trains_new)[0]} pulse trains to results")
            self.mu_dict["pulse_trains"].append(pulse_trains_new)
        else:
            print(f"No motor units found for electrode {electrode}")

        if electrode != 1:
            self.mu_dict["discharge_times"].append([])

        if not discharge_times_new:
            raise ValueError("No discharge times found")

        for j in range(len(discharge_times_new)):
            self.mu_dict["discharge_times"][electrode - 1].append(discharge_times_new[j])

        print(f"Post-processing completed for electrode {electrode}")

    def post_process_EMG_for_biofeedback(self, electrode, interval):
        print(f"Starting biofeedback post-processing for electrode {electrode+1}")

        self.mus_in_array = np.zeros(self.signal_dict["nelectrodes"])
        electrode += 1

        # Dewhiten MU filters
        self.decomp_dict["masked_mu_filters"] = (
            self.decomp_dict["dewhiten_mat"][interval] @ self.decomp_dict["masked_mu_filters"]
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

        if np.shape(pulse_trains)[0] > 0:  # if there are existing MUs
            print(f"Found {np.shape(pulse_trains)[0]} motor units")
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
            print(f"After duplicate removal: {len(discharge_times_new)} motor units")

            del pulse_trains, discharge_times

            # get the decomposition parameters for the biofeedback
            new_mu_filters = get_mu_filters(
                self.signal_dict["data"],
                self.rejected_channels,
                discharge_times_new,
                self.chans_per_electrode,
                electrode - 1,
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

            # get online parameters
            _, inv_extended_data, norm, centroids = get_online_parameters(
                self.signal_dict["data"],
                self.rejected_channels,
                new_mu_filters,
                self.chans_per_electrode,
                self.signal_dict["fsamp"],
                electrode - 1,
            )

            # Save parameters to MU dictionary
            self.mu_dict["pulse_trains"].append(pulse_trains)
            self.mu_dict["inv_extended_data"].append(inv_extended_data)
            self.mu_dict["norm"].append(norm)
            self.mu_dict["centroids"].append(centroids)
            self.mu_dict["mu_filters"].append(new_mu_filters)
        else:
            print(f"No motor units found for electrode {electrode}")

        if electrode != 1:
            self.mu_dict["discharge_times"].append([])

        for j in range(len(discharge_times)):
            self.mu_dict["discharge_times"][electrode - 1].append(discharge_times[j])

        print(f"Biofeedback post-processing completed for electrode {electrode}")

    def post_process_across_arrays(self):
        print("Starting post-processing across arrays")
        print(f"Duplicate between grids: {self.dup_bgrids}")

        mu_count = 0
        no_arrays = len(self.mu_dict["pulse_trains"])
        print(f"Found {no_arrays} electrode arrays with data")

        for i in range(no_arrays):
            if isinstance(self.mu_dict["pulse_trains"][i], np.ndarray) and self.mu_dict["pulse_trains"][i].size > 0:
                motor_unit_count = (
                    self.mu_dict["pulse_trains"][i].shape[0]
                    if hasattr(self.mu_dict["pulse_trains"][i], "shape")
                    else len(self.mu_dict["pulse_trains"][i])
                )
                print(f"Array {i+1} has {motor_unit_count} motor units")
                mu_count += motor_unit_count
            else:
                print(f"Array {i+1} has no motor units")

        print(f"Total motor unit count: {mu_count}")
        if mu_count == 0:
            print("No motor units found, skipping cross-array processing")
            return

        all_pulse_trains = np.zeros([mu_count, np.shape(self.signal_dict["target"])[0]])
        all_discharge_times = []  # different mus will have discharge time arrays of different lengths
        muscle = np.zeros(mu_count, dtype=int)

        mu = 0
        print("Consolidating motor units from all arrays...")
        for i in range(no_arrays):  # iterating over arrays
            if isinstance(self.mu_dict["pulse_trains"][i], np.ndarray) and self.mu_dict["pulse_trains"][i].size > 0:
                motor_unit_count = (
                    self.mu_dict["pulse_trains"][i].shape[0]
                    if hasattr(self.mu_dict["pulse_trains"][i], "shape")
                    else len(self.mu_dict["pulse_trains"][i])
                )

                for j in range(motor_unit_count):  # iterating over the mus per array
                    all_pulse_trains[mu, :] = self.mu_dict["pulse_trains"][i][j]
                    all_discharge_times.append(self.mu_dict["discharge_times"][i][j])
                    muscle[mu] = i
                    mu += 1

        print("Removing duplicates across arrays...")
        discharge_times_new, pulse_trains_new, muscle_new = remove_duplicates_between_arrays(
            all_pulse_trains,
            all_discharge_times,
            muscle,
            np.round(self.signal_dict["fsamp"] / 40),
            0.00025,
            self.dup_thr,
            self.signal_dict["fsamp"],
        )
        print(f"After duplicate removal: {len(discharge_times_new)} motor units")

        # Regroup motor units by electrode
        print("Regrouping motor units by electrode...")
        del self.mu_dict["discharge_times"]
        self.mu_dict["discharge_times"] = [[]]  # empty nested list

        del self.mu_dict["pulse_trains"]
        self.mu_dict["pulse_trains"] = []

        for i in range(no_arrays):
            if i != 0:
                self.mu_dict["discharge_times"].append([])

            idx = np.where(muscle_new == i)[0]  # find the indices for mu -> array mapping
            print(f"Found {len(idx)} MUs for array {i+1}")

            self.mu_dict["pulse_trains"].append(pulse_trains_new[idx])

            # Get number of motor units safely
            motor_unit_count = 0
            if hasattr(self.mu_dict["pulse_trains"][i], "shape"):
                motor_unit_count = self.mu_dict["pulse_trains"][i].shape[0]
            elif hasattr(self.mu_dict["pulse_trains"][i], "__len__"):
                motor_unit_count = len(self.mu_dict["pulse_trains"][i])

            for j in range(motor_unit_count):
                if j < len(idx) and idx[j] < len(discharge_times_new):
                    self.mu_dict["discharge_times"][i].append(discharge_times_new[idx[j]])

        self.mu_dict["muscle"] = muscle_new
        print("Processing across electrodes complete")
