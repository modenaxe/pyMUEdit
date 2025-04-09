import numpy as np

from utils.decomposition.bandpassingals import bandpassingals
from utils.decomposition.batchprocessfilters import batchprocessfilters
from utils.decomposition.calcSIL import calcSIL
from utils.decomposition.demean import demean
from utils.decomposition.extend import extend
from utils.decomposition.fixedpointalg import fixedpointalg
from utils.decomposition.formatsignalHDEMG import formatsignalHDEMG
from utils.decomposition.getspikes import getspikes
from utils.decomposition.minimizeCOVISI import minimizeCOVISI
from utils.decomposition.notchsignals import notchsignals
from utils.decomposition.peeloff import peeloff
from utils.decomposition.refineMUs import refineMUs
from utils.decomposition.remduplicates import remduplicates
from utils.decomposition.remduplicatesbgrids import remduplicatesbgrids
from utils.decomposition.remoutliers import remoutliers
from utils.decomposition.whiteesig import whiteesig


class DecompositionResults:
    """Container for decomposition results and progress callbacks"""

    def __init__(self):
        self.is_running = False
        self.progress_callback = None
        self.plot_callback = None

    def set_progress_callback(self, callback):
        """Set callback for progress updates"""
        self.progress_callback = callback

    def set_plot_callback(self, callback):
        """Set callback for plot updates during decomposition"""
        self.plot_callback = callback

    def update_progress(self, message, progress=None):
        """Update progress information"""
        if self.progress_callback:
            self.progress_callback(message, progress)

    def update_plot(self, time, target, plateau_coords, icasig=None, spikes=None, time2=None, sil=None, cov=None):
        """Update plots during decomposition"""
        if self.plot_callback:
            self.plot_callback(time, target, plateau_coords, icasig, spikes, time2, sil, cov)


class EMGDecomposition:
    """Core EMG decomposition class based on emg_decomposition.py"""

    def __init__(self, parameters, results=None):
        """
        Initialize EMG decomposition with parameters.

        Args:
            parameters: Dictionary of algorithm parameters
            results: Optional DecompositionResults object for progress and plot updates
        """
        print("==== Initializing EMG Decomposition ====")
        print(f"Parameters: {parameters}")

        self.parameters = parameters
        self.results = results if results is not None else DecompositionResults()

        # Main dictionaries to store data
        self.signal_dict = {}
        self.decomp_dict = {}
        self.mu_dict = {"pulse_trains": [], "discharge_times": [[] for _ in range(1)]}

        # Coordinates and rejection info
        self.coordinates = []
        self.ied = []
        self.rejected_channels = []
        self.emgopt = []
        self.mus_in_array = []

        print("Initialization complete")

    def prepare_signal_data(self, signal_data):
        """
        Prepare signal data for decomposition.

        Args:
            signal_data: The signal data loaded from a file (as a dictionary)
        """
        print("\n==== Preparing Signal Data ====")

        # Copy signal data to our internal dictionary
        self.signal_dict = signal_data.copy()

        coordinates, ied, emg_mask, emgtype = formatsignalHDEMG(
            self.signal_dict["data"],
            self.signal_dict["gridname"],
            self.signal_dict["fsamp"],
            self.parameters.get("checkEMG", 0),
        )

        # Store values in both class attributes and signal_dict
        self.coordinates = coordinates
        self.signal_dict["coordinates"] = coordinates
        self.ied = ied
        self.signal_dict["IED"] = ied
        self.rejected_channels = emg_mask
        self.signal_dict["EMGmask"] = emg_mask
        self.emgopt = ["surface" if t == 1 else "intra" for t in emgtype]
        self.signal_dict["emgtype"] = emgtype

        # Initialize mus_in_array with correct length based on ngrid
        self.mus_in_array = np.zeros(self.signal_dict["ngrid"])

        # Report progress
        self.results.update_progress("Signal data prepared")

    def batch_with_target(self):
        """
        Segment the EMG signal based on target reference.
        Similar to batch_w_target in emg_decomposition.py.
        """
        print("\n==== Batching Signal With Target ====")

        if "target" not in self.signal_dict:
            print("No target found. Using default segmentation.")
            self.batch_without_target()
            return

        # Print target stats for debugging
        target_len = len(self.signal_dict["target"])
        target_min = np.min(self.signal_dict["target"])
        target_max = np.max(self.signal_dict["target"])
        print(f"Target signal length: {target_len}, min: {target_min}, max: {target_max}")

        # Make sure target has some variation
        target_range = target_max - target_min
        if target_range < 0.001:
            print("Target signal has no meaningful variation. Using default segmentation.")
            self.batch_without_target()
            return

        # Calculate plateau threshold
        threshold = target_min + target_range * self.parameters["thresholdtarget"]
        print(f"Using plateau threshold: {threshold:.4f}")

        # Calculate plateau
        plateau = np.where(self.signal_dict["target"] >= threshold)[0]
        print(f"Found {len(plateau)} points above threshold")

        if len(plateau) < 100:  # Require at least 100 samples
            print(f"Plateau too small ({len(plateau)} samples). Using default segmentation.")
            self.batch_without_target()
            return

        print(f"Plateau range: {plateau[0]}-{plateau[-1]} ({plateau[-1] - plateau[0]} samples)")

        # Find discontinuities
        discontinuity = np.where(np.diff(plateau) > 1)[0]
        print(f"Found {len(discontinuity)} discontinuities in plateau")

        # Process according to windows and discontinuities
        nwindows = self.parameters["nwindows"]
        print(f"Number of requested windows: {nwindows}")

        if nwindows > 1 and not discontinuity.size:
            # Single continuous plateau with multiple windows
            print("Creating multiple windows for continuous plateau")
            plat_len = plateau[-1] - plateau[0]
            wind_len = int(np.floor(plat_len / nwindows))

            # Make sure windows aren't too small
            if wind_len < 2048:
                print(f"Window length too small ({wind_len}), adjusting number of windows")
                wind_len = int(np.floor(plat_len / min(nwindows, plat_len // 2048)))
                print(f"New window length: {wind_len}")

            batch = np.zeros(nwindows * 2, dtype=int)
            print(f"Creating {nwindows} windows of length {wind_len}")

            for i in range(nwindows):
                batch[i * 2] = plateau[0] + i * wind_len
                batch[(i + 1) * 2 - 1] = plateau[0] + (i + 1) * wind_len - 1
                print(f"Window {i+1}: {batch[i*2]}-{batch[(i+1)*2-1]} ({batch[(i+1)*2-1] - batch[i*2]} samples)")

            self.plateau_coords = batch

        elif nwindows >= 1 and len(discontinuity) > 0:
            # Multiple discontinuous plateaus
            print(f"Processing {len(discontinuity) + 1} separate plateaus")
            prebatch = np.zeros((len(discontinuity) + 1, 2), dtype=int)

            prebatch[0, :] = [plateau[0], plateau[discontinuity[0]]]
            n = len(discontinuity)

            for i, d in enumerate(discontinuity):
                if i < n - 1:
                    prebatch[i + 1, :] = [plateau[d + 1], plateau[discontinuity[i + 1]]]
                else:
                    prebatch[i + 1, :] = [plateau[d + 1], plateau[-1]]
                print(
                    f"Plateau {i+1}: {prebatch[i+1,0]}-{prebatch[i+1,1]} ({prebatch[i+1,1] - prebatch[i+1,0]} samples)"
                )

            # Check each segment's length
            plat_lens = prebatch[:, 1] - prebatch[:, 0]
            valid_segments = plat_lens >= 2048
            print(f"Segments with valid length (>=2048): {np.sum(valid_segments)}/{len(valid_segments)}")

            if not np.any(valid_segments):
                print("No valid segments found. Using default segmentation.")
                self.batch_without_target()
                return

            # Use only valid segments
            prebatch = prebatch[valid_segments]
            plat_lens = plat_lens[valid_segments]

            # Calculate window sizes for each plateau
            wind_lens = np.floor(plat_lens / nwindows).astype(int)
            batch = []

            for i, (start, end) in enumerate(prebatch):
                for j in range(nwindows):
                    window_start = start + j * wind_lens[i]
                    window_end = start + (j + 1) * wind_lens[i] - 1
                    if window_end > end:
                        window_end = end
                    if window_end - window_start >= 2048:  # Only add if window is at least 2048 samples
                        batch.extend([window_start, window_end])
                        print(
                            f"Plateau {i+1}, Window {j+1}: {window_start}-{window_end} ({window_end - window_start} samples)"
                        )

            if not batch:
                print("No valid windows found. Using default segmentation.")
                self.batch_without_target()
                return

            self.plateau_coords = np.array(batch)

        else:
            # One window, no discontinuity
            print("Using one window for plateau")
            # Make sure we have a substantial plateau
            if plateau[-1] - plateau[0] < 2048:
                print(f"Plateau too small ({plateau[-1] - plateau[0]} samples). Using default segmentation.")
                self.batch_without_target()
                return

            batch = np.array([plateau[0], plateau[-1]], dtype=int)
            print(f"Window: {batch[0]}-{batch[1]} ({batch[1] - batch[0]} samples)")
            self.plateau_coords = batch

        print(f"Created {len(self.plateau_coords) // 2} windows")
        print(f"Plateau coordinates: {self.plateau_coords}")

        self.batch_emg_data()
        self.results.update_progress("Signal batched based on target")

    def batch_without_target(self):
        """
        Segment the EMG signal without target reference.
        Similar to batch_wo_target in emg_decomposition.py.
        """
        print("\n==== Batching Signal Without Target ====")

        # Create default plateau coordinates using full signal length
        nwindows = self.parameters["nwindows"]
        signal_length = self.signal_dict["data"].shape[1]

        print(f"Creating {nwindows} equal windows for signal length {signal_length}")

        # Make sure we have enough data for meaningful windows
        if signal_length < 2048 * nwindows:
            nwindows = max(1, signal_length // 2048)
            print(f"Signal too short for requested windows. Adjusted to {nwindows} windows.")

        # Divide signal into equal windows
        wind_len = signal_length // nwindows
        batch = []

        for i in range(nwindows):
            start = i * wind_len
            end = (i + 1) * wind_len - 1

            # Ensure last window gets remaining samples
            if i == nwindows - 1:
                end = signal_length - 1

            batch.extend([start, end])
            print(f"Window {i+1}: {start}-{end} ({end - start} samples)")

        self.plateau_coords = np.array(batch, dtype=int)

        print(f"Created {nwindows} windows with coordinates: {self.plateau_coords}")

        self.batch_emg_data()
        self.results.update_progress("Signal batched using equal windows")

    def batch_emg_data(self):
        """
        Batch the EMG data according to plateau coordinates.
        Shared code from batch_w_target and batch_wo_target.
        """
        print("\n==== Batching EMG Data ====")

        nintervals = int(len(self.plateau_coords) / 2)
        self.signal_dict["batched_data"] = []

        print(f"Batching EMG data for {nintervals} intervals")
        print(f"EMG data shape: {self.signal_dict['data'].shape}")

        # Loop through electrodes and intervals
        for electrode in range(self.signal_dict["ngrid"]):
            print(f"\nProcessing electrode {electrode+1}/{self.signal_dict['ngrid']}")

            for interval in range(nintervals):
                # Get start and end indices
                start_idx = max(0, int(self.plateau_coords[interval * 2]))
                end_idx = min(
                    self.signal_dict["data"].shape[1] - 1, int(self.plateau_coords[(interval + 1) * 2 - 1]) + 1
                )

                # Ensure minimum window size (2048 samples ≈ 1 second at 2kHz)
                if end_idx - start_idx < 2048:
                    print(f"Warning: Interval {interval+1} too short ({end_idx - start_idx} samples). Extending...")
                    # Try to extend window to 2048 samples
                    midpoint = (start_idx + end_idx) // 2
                    start_idx = max(0, midpoint - 1024)
                    end_idx = min(self.signal_dict["data"].shape[1], midpoint + 1024)

                    # If still too small, use first 2048 samples or all available
                    if end_idx - start_idx < 2048:
                        start_idx = 0
                        end_idx = min(2048, self.signal_dict["data"].shape[1])
                        print(f"Using interval: {start_idx}-{end_idx} ({end_idx - start_idx} samples)")

                print(
                    f"Extracting window for electrode {electrode+1}, interval {interval+1}: {start_idx}-{end_idx} ({end_idx - start_idx} samples)"
                )

                # Get data for this electrode using channels
                channels = []

                # If we have rejected channels info, use it
                if len(self.rejected_channels) > electrode:
                    # Get channel indices that aren't rejected
                    electrode_start = 0
                    for e in range(electrode):
                        if e < len(self.rejected_channels):
                            electrode_start += np.sum(self.rejected_channels[e] == 0)

                    # Count channels in this electrode that aren't rejected
                    channel_count = np.sum(self.rejected_channels[electrode] == 0)
                    print(f"Electrode {electrode+1} has {channel_count} non-rejected channels")

                    if channel_count > 0:
                        # Get the actual channel indices
                        channel_indices = np.where(self.rejected_channels[electrode] == 0)[0]
                        for ch_idx in channel_indices:
                            channels.append(electrode_start + ch_idx)
                    else:
                        # If all channels are rejected, use a default
                        print(f"Warning: All channels rejected for electrode {electrode+1}. Using default channels.")
                        channels = list(range(64))  # Assume 64 channels as default
                else:
                    # Without rejection info, use channel position estimation
                    channels_per_electrode = 64  # Default assumption for HDEMG
                    channels = list(range(electrode * channels_per_electrode, (electrode + 1) * channels_per_electrode))
                    print(f"No rejection information. Using {len(channels)} channels for electrode {electrode+1}")

                # Limit to available channels
                channels = [ch for ch in channels if ch < self.signal_dict["data"].shape[0]]
                print(f"Using {len(channels)} valid channels for electrode {electrode+1}")

                # Extract data slice
                if channels:
                    try:
                        data_slice = self.signal_dict["data"][channels, start_idx:end_idx].copy()
                        print(f"Extracted data slice with shape {data_slice.shape}")
                    except Exception as e:
                        print(f"Error extracting data: {e}")
                        # Create dummy data
                        data_slice = np.random.randn(len(channels), end_idx - start_idx) * 0.01
                        print(f"Created dummy data with shape {data_slice.shape}")
                else:
                    print(f"Warning: No valid channels for electrode {electrode+1}")
                    # Create dummy data
                    data_slice = np.random.randn(64, end_idx - start_idx) * 0.01
                    print(f"Created dummy data with shape {data_slice.shape}")

                # Check if slice is valid
                if data_slice.size == 0 or data_slice.shape[1] < 100:
                    print(f"Warning: Invalid data slice for electrode {electrode+1}, interval {interval+1}")
                    # Create dummy data
                    data_slice = np.random.randn(data_slice.shape[0] if data_slice.size > 0 else 64, 2048) * 0.01
                    print(f"Created dummy data with shape {data_slice.shape}")

                # Add to batched data
                self.signal_dict["batched_data"].append(data_slice)
                print(f"Added data slice with shape {data_slice.shape}")

        print(f"Created {len(self.signal_dict['batched_data'])} batched data arrays")

        # Validate all batches
        print("\nSummary of all batched data arrays:")
        for i, batch in enumerate(self.signal_dict["batched_data"]):
            print(f"Batch {i+1}: shape={batch.shape}, min={np.min(batch):.4f}, max={np.max(batch):.4f}")

    def convolutive_sphering(self, electrode, interval, tracker):
        """
        Apply convolutive sphering to the batched EMG data.
        """
        print(f"\n==== Convolutive Sphering for Electrode {electrode+1}, Interval {interval+1} ====")

        # Check that we have valid batched data
        if tracker >= len(self.signal_dict["batched_data"]):
            raise ValueError(
                f"Tracker index {tracker} out of range for batched data (length: {len(self.signal_dict['batched_data'])})"
            )

        # Get data shape
        data_shape = self.signal_dict["batched_data"][tracker].shape
        print(f"Starting convolutive sphering for data with shape {data_shape}")

        # Initialize output structures if not already created
        if "extend_obvs_old" not in self.signal_dict:
            nwins = int(len(self.plateau_coords) / 2)
            # Initialize lists instead of pre-allocated arrays
            self.signal_dict["extend_obvs_old"] = [None] * nwins
            self.decomp_dict["whitened_obvs_old"] = [None] * nwins
            self.signal_dict["sq_extend_obvs"] = [None] * nwins
            self.signal_dict["inv_extend_obvs"] = [None] * nwins
            self.decomp_dict["dewhiten_mat"] = [None] * nwins
            self.decomp_dict["whiten_mat"] = [None] * nwins
            self.signal_dict["extend_obvs"] = [None] * nwins
            self.decomp_dict["whitened_obvs"] = [None] * nwins

        # Apply filtering regardless of checkEMG
        emg_type = self.emgopt[electrode] if len(self.emgopt) > electrode else "surface"
        print(f"EMG type: {emg_type}")

        self.signal_dict["batched_data"][tracker] = notchsignals(
            self.signal_dict["batched_data"][tracker], self.signal_dict["fsamp"]
        )
        print(f"Notch filtering completed")

        self.signal_dict["batched_data"][tracker] = bandpassingals(
            self.signal_dict["batched_data"][tracker], self.signal_dict["fsamp"], 1 if emg_type == "surface" else 2
        )
        print(f"Bandpass filtering completed")

        # Apply differentiation if enabled
        if self.parameters["differentialmode"] == 1:

            self.signal_dict["batched_data"][tracker] = np.diff(self.signal_dict["batched_data"][tracker], axis=1)
            print(f"Differentiation completed")

        # Signal extension
        channels = self.signal_dict["batched_data"][tracker].shape[0]
        extension_factor = round(self.parameters["nbextchan"] / channels)
        self.ext_number = extension_factor

        # Extend the EMG signal
        self.signal_dict["extend_obvs_old"][interval] = extend(
            self.signal_dict["batched_data"][tracker], extension_factor
        )
        print(f"Signal extension completed")

        # Calculate covariance matrix and pseudo-inverse
        self.signal_dict["sq_extend_obvs"][interval] = (
            np.matmul(self.signal_dict["extend_obvs_old"][interval], self.signal_dict["extend_obvs_old"][interval].T)
            / self.signal_dict["extend_obvs_old"][interval].shape[1]
        )
        print(f"Covariance matrix calculation completed")

        self.signal_dict["inv_extend_obvs"][interval] = np.linalg.pinv(self.signal_dict["sq_extend_obvs"][interval])
        print(f"Pseudo-inverse calculation completed")

        # De-mean the signal
        self.signal_dict["extend_obvs_old"][interval] = demean(self.signal_dict["extend_obvs_old"][interval])
        print(f"De-meaning completed")

        # Whiten the signal
        (
            self.decomp_dict["whitened_obvs_old"][interval],
            self.decomp_dict["whiten_mat"][interval],
            self.decomp_dict["dewhiten_mat"][interval],
        ) = whiteesig(self.signal_dict["extend_obvs_old"][interval])
        print(f"Whitening completed")

        # Remove edges from the signal
        edge_samples = int(np.round(self.signal_dict["fsamp"] * self.parameters["edges"]))

        # Only apply edge removal if the signal is long enough
        if edge_samples > 0 and self.decomp_dict["whitened_obvs_old"][interval].shape[1] > 2 * edge_samples:
            self.signal_dict["extend_obvs"][interval] = self.signal_dict["extend_obvs_old"][interval][
                :, edge_samples:-edge_samples
            ]

            self.decomp_dict["whitened_obvs"][interval] = self.decomp_dict["whitened_obvs_old"][interval][
                :, edge_samples:-edge_samples
            ]
            print(f"Edge removal applied")
        else:
            # If signal is too short for edge removal, just copy
            self.signal_dict["extend_obvs"][interval] = self.signal_dict["extend_obvs_old"][interval].copy()
            self.decomp_dict["whitened_obvs"][interval] = self.decomp_dict["whitened_obvs_old"][interval].copy()
            print(f"Signal too short for edge removal. Keeping original")

        # Adjust plateau coordinates only once
        if electrode == 0 and edge_samples > 0:
            old_start = self.plateau_coords[interval * 2]
            old_end = self.plateau_coords[(interval + 1) * 2 - 1]
            self.plateau_coords[interval * 2] = old_start + edge_samples - 1
            self.plateau_coords[(interval + 1) * 2 - 1] = old_end - edge_samples
            print(
                f"Adjusted plateau coordinates: {old_start}-{old_end} → {self.plateau_coords[interval * 2]}-{self.plateau_coords[(interval + 1) * 2 - 1]}"
            )

        print(f"Convolutive sphering completed for electrode {electrode+1}, interval {interval+1}")

        self.results.update_progress(
            f"Signal extension and whitening completed for electrode {electrode+1}, interval {interval+1}"
        )

    def fast_ica_and_ckc(self, electrode, interval, tracker):
        """
        Apply FastICA and Convolutive Kernel Compensation.
        """
        print(f"\n==== FastICA and CKC for Electrode {electrode+1}, Interval {interval+1} ====")

        # Choose contrast function
        cf_type = self.parameters["contrastfunc"]

        # Initialize tracking arrays
        init_its = np.zeros(self.parameters["NITER"], dtype=int)
        fpa_its = 500  # maximum number of iterations for fixed point algorithm

        # Get whitened signal
        Z = self.decomp_dict["whitened_obvs"][interval].copy()
        time_axis = np.linspace(0, Z.shape[1] / self.signal_dict["fsamp"], Z.shape[1])

        # Initialize separation matrices
        if "B_sep_mat" not in self.decomp_dict:
            self.decomp_dict["B_sep_mat"] = np.zeros((Z.shape[0], self.parameters["NITER"]))
            self.decomp_dict["w_sep_vect"] = np.zeros((Z.shape[0], 1))
            self.decomp_dict["MU_filters"] = np.zeros(
                (len(self.plateau_coords) // 2, Z.shape[0], self.parameters["NITER"])
            )
            self.decomp_dict["SILs"] = np.zeros((len(self.plateau_coords) // 2, self.parameters["NITER"]))
            self.decomp_dict["CoVs"] = np.zeros((len(self.plateau_coords) // 2, self.parameters["NITER"]))
            self.decomp_dict["masked_mu_filters"] = []

        # FastICA iterations
        for i in range(self.parameters["NITER"]):
            print(f"\n--- FastICA Iteration {i+1}/{self.parameters['NITER']} ---")

            # Initialize separation vector
            if i == 0:
                if self.parameters["initialization"] == 0:  # EMG max
                    sort_sq_sum_Z = np.argsort(np.square(np.sum(Z, axis=0)))
                    init_its[i] = sort_sq_sum_Z[-(i + 1)]
                    self.decomp_dict["w_sep_vect"] = Z[:, int(init_its[i])].copy().reshape(-1, 1)
                else:  # Random
                    self.decomp_dict["w_sep_vect"] = np.random.randn(Z.shape[0], 1)
            else:
                if self.parameters["initialization"] == 0:
                    if i < len(sort_sq_sum_Z):
                        init_its[i] = sort_sq_sum_Z[-(i + 1)]
                        self.decomp_dict["w_sep_vect"] = Z[:, int(init_its[i])].copy().reshape(-1, 1)
                    else:
                        print("Using random initialization (ran out of EMG max points)")
                        self.decomp_dict["w_sep_vect"] = np.random.randn(Z.shape[0], 1)
                else:
                    self.decomp_dict["w_sep_vect"] = np.random.randn(Z.shape[0], 1)

            # Orthogonalize and normalize
            self.decomp_dict["w_sep_vect"] = self.decomp_dict["w_sep_vect"].reshape(-1, 1)
            self.decomp_dict["w_sep_vect"] -= np.dot(
                self.decomp_dict["B_sep_mat"] @ self.decomp_dict["B_sep_mat"].T, self.decomp_dict["w_sep_vect"]
            )
            w_norm = np.linalg.norm(self.decomp_dict["w_sep_vect"])
            self.decomp_dict["w_sep_vect"] /= w_norm

            # Run fixed point algorithm
            self.decomp_dict["w_sep_vect"] = fixedpointalg(
                self.decomp_dict["w_sep_vect"].flatten(),
                Z,  # X parameter - whitened signal matrix
                self.decomp_dict["B_sep_mat"],  # B parameter - basis matrix
                fpa_its,  # maxiter parameter - maximum iterations
                cf_type,  # contrastfunc parameter - contrast function name
            ).reshape(-1, 1)
            print(f"Fixed point algorithm completed")

            # Get initial spikes
            icasig, spikes = getspikes(self.decomp_dict["w_sep_vect"], Z, self.signal_dict["fsamp"])

            # Check for at least 10 spikes
            if len(spikes) > 10:
                # Calculate CoV
                ISI = np.diff(spikes / self.signal_dict["fsamp"])
                CoV = np.std(ISI) / np.mean(ISI)

                # Update separation vector by summing spikes
                w_n_p1 = np.sum(Z[:, spikes], axis=1).reshape(-1, 1)

                # Minimize CoV
                self.decomp_dict["MU_filters"][interval, :, i], spikes, self.decomp_dict["CoVs"][interval, i] = (
                    minimizeCOVISI(w_n_p1, Z, CoV, self.signal_dict["fsamp"])
                )
                print(f"CoV minimization completed")

                # Store separation vector
                self.decomp_dict["B_sep_mat"][:, i] = self.decomp_dict["w_sep_vect"].flatten()

                # Calculate SIL
                icasig, spikes, self.decomp_dict["SILs"][interval, i] = calcSIL(
                    Z, self.decomp_dict["MU_filters"][interval, :, i], self.signal_dict["fsamp"]
                )
                print(f"SIL calculation completed")
                print(
                    f"SIL: {self.decomp_dict['SILs'][interval, i]:.4f} - CoV: {self.decomp_dict['CoVs'][interval, i]:.4f}"
                )

                # Peel off if enabled
                if (
                    self.parameters["peeloff"] == 1
                    and self.decomp_dict["SILs"][interval, i] > self.parameters["silthr"]
                ):
                    print(
                        f"Peeling off spikes (SIL={self.decomp_dict['SILs'][interval, i]:.4f} > threshold={self.parameters['silthr']:.4f})"
                    )
                    Z = peeloff(Z, spikes, self.signal_dict["fsamp"], self.parameters["peeloffwin"])
                    print(f"Peel-off completed")

                # Update plot if callback is available
                if self.results.plot_callback and self.parameters.get("drawingmode", 1) == 1:
                    time_vector = np.linspace(
                        0, len(self.signal_dict["target"]) / self.signal_dict["fsamp"], len(self.signal_dict["target"])
                    )
                    self.results.update_plot(
                        time_vector,
                        self.signal_dict["target"],
                        [self.plateau_coords[interval * 2], self.plateau_coords[(interval + 1) * 2 - 1]],
                        icasig,
                        spikes,
                        time_axis,
                        self.decomp_dict["SILs"][interval, i],
                        self.decomp_dict["CoVs"][interval, i],
                    )
                elif self.parameters.get("drawingmode", 1) == 0:
                    print(
                        f"Grid #{electrode+1} - Iteration #{i+1} - "
                        f"SIL = {self.decomp_dict['SILs'][interval, i]:.4f} "
                        f"CoV = {self.decomp_dict['CoVs'][interval, i]:.4f}"
                    )

                self.results.update_progress(
                    f"Electrode #{electrode+1} - Iteration #{i+1} - "
                    f"SIL = {self.decomp_dict['SILs'][interval, i]:.4f} "
                    f"CoV = {self.decomp_dict['CoVs'][interval, i]:.4f}"
                )
            else:
                print(f"Not enough spikes ({len(spikes)}) to calculate CoV")
                self.decomp_dict["B_sep_mat"][:, i] = self.decomp_dict["w_sep_vect"].flatten()
                self.results.update_progress(f"Electrode #{electrode+1} - Iteration #{i+1} - Not enough spikes")

        # Filter MU filters based on SIL and CoV
        print("\n==== Filtering MU filters based on quality metrics ====")
        SIL_condition = self.decomp_dict["SILs"][interval, :] >= self.parameters["silthr"]
        print(
            f"SIL threshold: {self.parameters['silthr']:.4f}, MUs passing: {np.sum(SIL_condition)}/{self.parameters['NITER']}"
        )

        # Create a masked version of MU filters
        masked_filters = self.decomp_dict["MU_filters"][interval].copy()

        if self.parameters["covfilter"] == 1:
            # Add CoV threshold
            CoV_condition = self.decomp_dict["CoVs"][interval, :] <= self.parameters["covthr"]
            print(
                f"CoV threshold: {self.parameters['covthr']:.4f}, MUs passing: {np.sum(CoV_condition)}/{self.parameters['NITER']}"
            )
            final_condition = SIL_condition & CoV_condition
            print(f"MUs passing both SIL and CoV: {np.sum(final_condition)}/{self.parameters['NITER']}")

            # Filter MU filters to remove those that don't meet criteria
            masked_filters = masked_filters[:, final_condition]
        else:
            # Only filter based on SIL
            masked_filters = masked_filters[:, SIL_condition]
            final_condition = SIL_condition

        # Store filtered MU filters
        self.decomp_dict["masked_mu_filters"].append(masked_filters)
        print(
            f"Selected {np.sum(final_condition)} MU filters with shape {self.decomp_dict['masked_mu_filters'][-1].shape}"
        )

        self.results.update_progress(
            f"FastICA completed for electrode {electrode+1}, interval {interval+1}. "
            f"Selected {np.sum(final_condition)} MU filters."
        )
        print(f"FastICA and CKC completed")

    def post_process_emg(self, electrode):
        """
        Post-process the EMG decomposition results with added debug prints.
        """
        print(f"\n==== DEBUG: post_process_emg for Electrode {electrode+1} ====")
        print(f"mus_in_array length: {len(self.mus_in_array)}, electrode: {electrode}")

        if electrode >= len(self.mus_in_array):
            print(f"WARNING: Expanding mus_in_array to accommodate electrode {electrode+1}")
            expanded = np.zeros(electrode + 1)
            expanded[: len(self.mus_in_array)] = self.mus_in_array
            self.mus_in_array = expanded

        # Batch process filters across windows
        print("\nProcessing filters across all windows...")

        # Call batchprocessfilters
        pulse_trains, discharge_times = batchprocessfilters(
            self.decomp_dict["masked_mu_filters"],
            self.decomp_dict["whitened_obvs"],
            self.plateau_coords,
            self.ext_number,
            self.parameters["differentialmode"],
            self.signal_dict["data"].shape[1],
            self.signal_dict["fsamp"],
        )
        print(f"Batch processing completed")
        print(f"Pulse trains shape: {pulse_trains.shape}")
        print(f"Number of discharge time arrays: {len(discharge_times)}")

        if pulse_trains.shape[0] > 0:
            self.mus_in_array[electrode] = 1
            print(f"Found {pulse_trains.shape[0]} MUs for electrode {electrode+1}")

            # Remove duplicate MUs
            print("\nRemoving duplicate MUs...")
            discharge_times_new, pulse_trains_new = remduplicates(
                pulse_trains,
                discharge_times,
                discharge_times,
                round(self.signal_dict["fsamp"] / 40),
                0.00025,
                self.parameters["duplicatesthresh"],
                self.signal_dict["fsamp"],
            )
            print(f"Duplicate removal completed")
            print(f"MUs after duplicate removal: {len(discharge_times_new)}")

            if self.parameters["refineMU"] == 1:
                # Remove outliers
                print("\nRemoving outliers...")
                discharge_times_new = remoutliers(
                    pulse_trains_new, discharge_times_new, self.parameters["CoVDR"], self.signal_dict["fsamp"]
                )
                print(f"Outlier removal completed")

                # Refine MUs
                if len(self.rejected_channels) > electrode:
                    print("\nRefining MUs...")

                    if electrode < len(self.rejected_channels):
                        print(f"  rejected_channels[{electrode}] shape: {self.rejected_channels[electrode].shape}")

                    pulse_trains_new, discharge_times_new = refineMUs(
                        self.signal_dict["data"],
                        self.rejected_channels[electrode],
                        pulse_trains_new,
                        discharge_times_new,
                        self.signal_dict["fsamp"],
                    )
                    print(f"MU refinement completed")

                    # Remove outliers again
                    print("\nRemoving outliers after refinement...")
                    discharge_times_new = remoutliers(
                        pulse_trains_new, discharge_times_new, self.parameters["CoVDR"], self.signal_dict["fsamp"]
                    )
                    print(f"Second outlier removal completed")

            # Store results
            print("\nStoring results:")
            self.mu_dict["pulse_trains"].append(pulse_trains_new)

            # Initialize discharge times array if needed
            if electrode != 0 and len(self.mu_dict["discharge_times"]) <= electrode:
                self.mu_dict["discharge_times"].extend(
                    [[] for _ in range(electrode - len(self.mu_dict["discharge_times"]) + 1)]
                )
                print(f"Initialized discharge times arrays up to electrode {electrode+1}")

            # Store discharge times
            print(f"Storing {len(discharge_times_new)} discharge time arrays")
            for j in range(len(discharge_times_new)):
                if j < len(discharge_times_new):
                    self.mu_dict["discharge_times"][electrode].append(discharge_times_new[j])
        else:
            print(f"No MUs found for electrode {electrode+1}")

        # Report progress
        self.results.update_progress(f"Post-processing completed for electrode {electrode+1}")
        print(f"Post-processing completed")
        print(f"==== END DEBUG: post_process_emg for Electrode {electrode+1} ====\n")

    def post_process_across_arrays(self):
        """
        Process duplicates between arrays.
        Fixed to match correct parameter ordering and avoid indexing issues.
        """
        print("\n==== Post-processing across arrays ====")

        # Count total MUs
        mu_count = 0
        for i in range(len(self.mu_dict["pulse_trains"])):
            if len(self.mu_dict["pulse_trains"][i]) > 0:
                mu_count += self.mu_dict["pulse_trains"][i].shape[0]
        print(f"Total motor units across all electrodes: {mu_count}")

        # Early exit if no MUs
        if mu_count == 0:
            print("No MUs to process")
            return

        # Initialize arrays
        all_pulse_trains = np.zeros((mu_count, self.signal_dict["data"].shape[1]))
        all_discharge_times = []
        muscle = np.zeros(mu_count, dtype=int)

        # Collect all MUs
        mu = 0
        print("\nCollecting MUs from all electrodes:")
        for i in range(len(self.mu_dict["pulse_trains"])):
            if hasattr(self.mu_dict["pulse_trains"][i], "shape") and self.mu_dict["pulse_trains"][i].shape[0] > 0:
                print(f"Electrode {i+1}: {self.mu_dict['pulse_trains'][i].shape[0]} MUs")
                for j in range(self.mu_dict["pulse_trains"][i].shape[0]):
                    all_pulse_trains[mu, :] = self.mu_dict["pulse_trains"][i][j]
                    all_discharge_times.append(self.mu_dict["discharge_times"][i][j])
                    muscle[mu] = i
                    mu += 1
            else:
                print(f"Electrode {i+1}: No MUs")

        # Remove duplicates across arrays
        print("\nRemoving duplicates across arrays...")

        pulse_trains_across_arrays, discharge_times_across_arrays, muscle_across_arrays = remduplicatesbgrids(
            all_pulse_trains,
            all_discharge_times,
            muscle,
            round(self.signal_dict["fsamp"] / 40),
            0.00025,
            self.parameters["duplicatesthresh"],
            self.signal_dict["fsamp"],
        )
        print(f"Cross-array duplicate removal completed")
        print(f"MUs after cross-array duplicate removal: {len(discharge_times_across_arrays)}")

        # Save original electrode count
        num_electrodes = len(self.mu_dict["pulse_trains"])

        # Reset the discharge times and pulse trains
        new_discharge_times = []
        new_pulse_trains = []

        for i in range(num_electrodes):
            # Add empty list for this electrode's discharge times
            new_discharge_times.append([])

            # Get indices for MUs from this electrode
            electrode_indices = np.where(muscle_across_arrays == i)[0]

            if len(electrode_indices) > 0:
                # Get pulses for this electrode
                electrode_pulse_trains = pulse_trains_across_arrays[electrode_indices]
                new_pulse_trains.append(electrode_pulse_trains)

                # Get discharge times for each MU
                for idx in electrode_indices:
                    if idx < len(discharge_times_across_arrays):
                        new_discharge_times[i].append(discharge_times_across_arrays[idx])
            else:
                # No MUs for this electrode, create empty array with correct shape
                if hasattr(pulse_trains_across_arrays, "shape") and pulse_trains_across_arrays.shape[0] > 0:
                    empty_shape = (0, pulse_trains_across_arrays.shape[1])
                else:
                    empty_shape = (0, self.signal_dict["data"].shape[1])

                new_pulse_trains.append(np.zeros(empty_shape))

        # Update the mu_dict with new arrays
        self.mu_dict["discharge_times"] = new_discharge_times
        self.mu_dict["pulse_trains"] = new_pulse_trains
        self.mu_dict["muscle"] = muscle_across_arrays

        print("\nFinal MU counts by electrode:")
        for i in range(len(new_pulse_trains)):
            if hasattr(new_pulse_trains[i], "shape"):
                print(f"Electrode {i+1}: {new_pulse_trains[i].shape[0]} MUs")
            else:
                print(f"Electrode {i+1}: 0 MUs")

        self.results.update_progress("Processing across electrodes complete")
        print(f"Post-processing across arrays completed")

    def run(self):
        """
        Run the EMG decomposition.
        """
        print("\n==== Starting EMG Decomposition ====")

        self.results.is_running = True

        import os

        # Set optimal thread count for matrix operations
        os.environ["OMP_NUM_THREADS"] = "4"
        os.environ["MKL_NUM_THREADS"] = "4"
        os.environ["NUMEXPR_NUM_THREADS"] = "4"
        os.environ["OPENBLAS_NUM_THREADS"] = "4"

        # Optimize numpy settings
        import numpy as np

        np.seterr(all="ignore")

        import gc

        gc.collect()

        self.results.is_running = True

        # Determine if we have a target signal
        has_target = "target" in self.signal_dict and len(self.signal_dict["target"]) > 0
        print(f"Has target signal: {has_target}")
        self.results.update_progress("Starting EMG decomposition")

        # Prepare signal
        print("\n--- Phase 1: Signal Preparation ---")
        if has_target and self.parameters.get("ref_exist", 1) == 1:
            self.batch_with_target()
        else:
            self.batch_without_target()
        print(f"Signal preparation completed")

        # Process each electrode
        print("\n--- Phase 2: Processing Electrodes ---")
        for electrode in range(self.signal_dict["ngrid"]):
            print(f"\n=== Processing Electrode {electrode+1}/{self.signal_dict['ngrid']} ===")
            self.results.update_progress(f"Processing electrode {electrode+1} of {self.signal_dict['ngrid']}")

            # Process each interval for this electrode
            nintervals = len(self.plateau_coords) // 2
            tracker = 0

            for interval in range(nintervals):
                print(f"\n== Processing Interval {interval+1}/{nintervals} ==")

                # Run convolutive sphering
                self.convolutive_sphering(electrode, interval, tracker)

                # Run FastICA and CKC
                self.fast_ica_and_ckc(electrode, interval, tracker)

                tracker += 1
                print(f"Interval {interval+1} processing completed")

            # Post-process this electrode
            self.post_process_emg(electrode)
            print(f"Electrode {electrode+1} processing completed")

        print(f"Electrode processing completed")

        # Process across arrays if enabled
        if self.parameters.get("duplicatesbgrids", 0) == 1 and sum(self.mus_in_array) > 0:
            print("\n--- Phase 3: Cross-Array Processing ---")
            self.post_process_across_arrays()
            print(f"Cross-array processing completed")

        # Copy results back to signal_dict
        print("\n--- Phase 4: Saving Results ---")

        # Create clean output structure
        clean_output = {}

        essential_fields = [
            "data",
            "auxiliary",
            "auxiliaryname",
            "fsamp",
            "nChan",
            "ngrid",
            "gridname",
            "muscle",
            "path",
            "target",
            "coordinates",
            "IED",
            "EMGmask",
            "emgtype",
        ]

        for field in essential_fields:
            if field in self.signal_dict:
                clean_output[field] = self.signal_dict[field]

        # Format Pulsetrain and Dischargetimes properly
        if len(self.mu_dict["pulse_trains"]) > 0:
            clean_output["Pulsetrain"] = {}
            clean_output["Dischargetimes"] = {}

            for electrode in range(len(self.mu_dict["pulse_trains"])):
                if (
                    hasattr(self.mu_dict["pulse_trains"][electrode], "shape")
                    and self.mu_dict["pulse_trains"][electrode].shape[0] > 0
                ):
                    print(f"Saving {self.mu_dict['pulse_trains'][electrode].shape[0]} MUs for electrode {electrode+1}")

                    # Store pulse trains by electrode
                    clean_output["Pulsetrain"][electrode] = self.mu_dict["pulse_trains"][electrode]

                    # Store discharge times by motor unit
                    for j in range(len(self.mu_dict["discharge_times"][electrode])):
                        clean_output["Dischargetimes"][electrode, j] = self.mu_dict["discharge_times"][electrode][j]

        print(f"Results saved")

        self.results.is_running = False
        self.results.update_progress("Decomposition complete")

        print(f"\n==== EMG Decomposition Completed ====")
        print(f"Total MUs found: {sum(len(pulses) for pulses in self.mu_dict['pulse_trains'])}")
        return clean_output


def prepare_parameters(ui_params):
    """Convert UI parameters to algorithm parameters"""
    parameters = {}

    # Convert UI dropdown values to numeric flags
    parameters["checkEMG"] = 1 if ui_params.get("check_emg") == "Yes" else 0
    parameters["peeloff"] = 1 if ui_params.get("peeloff") == "Yes" else 0
    parameters["covfilter"] = 1 if ui_params.get("cov_filter") == "Yes" else 0
    parameters["initialization"] = 0 if ui_params.get("initialization") == "EMG max" else 1
    parameters["refineMU"] = 1 if ui_params.get("refine_mu") == "Yes" else 0
    parameters["duplicatesbgrids"] = 1 if ui_params.get("duplicates_bgrids", "Yes") == "Yes" else 0

    # Set numeric parameters
    parameters["NITER"] = ui_params.get("iterations", 75)
    parameters["nwindows"] = ui_params.get("windows", 1)
    parameters["thresholdtarget"] = ui_params.get("threshold_target", 0.8)
    parameters["nbextchan"] = ui_params.get("extended_channels", 1000)
    parameters["duplicatesthresh"] = ui_params.get("duplicates_threshold", 0.3)
    parameters["silthr"] = ui_params.get("sil_threshold", 0.9)
    parameters["covthr"] = ui_params.get("cov_threshold", 0.5)

    # Set algorithm-specific parameters
    parameters["CoVDR"] = 0.3  # Threshold for CoV of Discharge rate
    parameters["edges"] = 0.5  # Edges to remove (in seconds),
    parameters["contrastfunc"] = ui_params.get("contrast_function", "skew")
    parameters["peeloffwin"] = 0.025  # Window duration for detecting action potentials
    parameters["differentialmode"] = 0  # Default to no differentiation
    parameters["drawingmode"] = 1

    return parameters
