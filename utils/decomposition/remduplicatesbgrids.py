import numpy as np
from scipy.signal import correlate
import time


def xcorr(x, y, max_lag=None):
    """
    Calculate the cross-correlation between two signals.

    Args:
        x: First signal
        y: Second signal
        max_lag: Maximum lag to consider

    Returns:
        xcorrvalues: Cross-correlation values
        lags: Corresponding lags
    """
    # Calculate correlation (normalized)
    correlation = correlate(x, y, mode="full", method="fft")
    correlation = correlation / np.max(np.abs(correlation))

    # Get lags
    lags = np.arange(-len(y) + 1, len(x))

    # Limit to max_lag if specified
    if max_lag is not None:
        valid_indices = np.abs(lags) <= max_lag
        correlation = correlation[valid_indices]
        lags = lags[valid_indices]

    return correlation, lags


def remduplicatesbgrids(PulseT, Distim, muscle, maxlag, jitter, tol, fsamp):
    """
    Remove duplicated motor units between different grids based on discharge pattern similarity.
    Fixed the indexing issue when removing elements during iteration.

    Args:
        PulseT: Motor unit pulse trains
        Distim: List of discharge times for each motor unit
        muscle: Array of muscle indices for each motor unit
        maxlag: Maximum lag for cross-correlation
        jitter: Jitter tolerance in seconds
        tol: Threshold for considering units as duplicates
        fsamp: Sampling frequency

    Returns:
        Filtered pulse trains, discharge times, and muscle indices
    """
    # Early exit for empty input
    if PulseT.shape[0] == 0 or len(Distim) == 0:
        print("No motor units to process")
        return PulseT, Distim, muscle

    # Convert jitter to samples
    jit = round(jitter * fsamp)

    # Keep track of which MUs have been processed
    mu_count = PulseT.shape[0]
    processed = np.zeros(mu_count, dtype=bool)

    # Generate binary spike trains
    firings = np.zeros_like(PulseT, dtype=bool)
    jittered_times = []

    # Fill firing arrays and create jittered versions
    for i in range(mu_count):
        # Check if Distim is valid for this motor unit
        if i >= len(Distim) or Distim[i] is None or len(Distim[i]) == 0:
            jittered_times.append(np.array([], dtype=int))
            continue

        # Create binary firing array
        spikes = Distim[i]
        valid_spikes = [s for s in spikes if 0 <= s < PulseT.shape[1]]

        # Check for valid spikes
        if len(valid_spikes) == 0:
            jittered_times.append(np.array([], dtype=int))
            continue

        # Set spikes in firing array
        firings[i, valid_spikes] = 1

        # Create jittered times for this MU
        jitter_set = set()
        for j in range(1, jit + 1):
            for s in valid_spikes:
                if s - j >= 0:
                    jitter_set.add(s - j)
                if s + j < PulseT.shape[1]:
                    jitter_set.add(s + j)

        # Add original spikes
        for s in valid_spikes:
            jitter_set.add(s)

        # Convert to sorted array
        jittered_times.append(np.array(sorted(jitter_set), dtype=int))

    # Initialize output arrays
    pulseT_new = []
    distim_new = []
    muscle_new = []

    # Process each MU
    while not np.all(processed):
        # Find first unprocessed MU
        reference_idx = np.argmin(processed)
        reference_muscle = muscle[reference_idx]

        # Find all duplicates of this MU in different muscles
        duplicate_indices = [reference_idx]  # Always include the reference

        # Calculate cross-correlations
        for j in range(mu_count):
            # Skip if already processed, same as reference, or empty
            if processed[j] or j == reference_idx or len(Distim[j]) == 0:
                continue

            # Skip if same muscle (only looking for cross-electrode duplicates)
            if muscle[j] == reference_muscle:
                continue

            # Calculate cross-correlation
            c, lags = xcorr(firings[reference_idx], firings[j], maxlag)

            # Find optimal lag
            idx = np.argmax(np.abs(c))
            max_corr = c[idx]
            lag = lags[idx]

            # Skip if correlation is not significant
            if abs(max_corr) < 0.2:
                continue

            # Calculate similarity with optimal lag
            shifted = np.array([t + lag for t in jittered_times[j] if 0 <= t + lag < PulseT.shape[1]])
            common = np.intersect1d(jittered_times[reference_idx], shifted)

            # Remove consecutive common times
            if len(common) > 1:
                mask = np.concatenate(([True], np.diff(common) > 1))
                common = common[mask]

            # Calculate similarity
            similarity = len(common) / max(len(Distim[reference_idx]), len(Distim[j]))

            # If similarity is high enough, mark as duplicate
            if similarity >= tol:
                duplicate_indices.append(j)  # type:ignore
                print(f"  MU #{j+1} is a DUPLICATE of MU #{reference_idx+1}")

        # If we found duplicates, select the best one
        if len(duplicate_indices) > 0:
            # Calculate CoV for all duplicates
            CoVs = {}
            for idx in duplicate_indices:
                if len(Distim[idx]) > 1:
                    isi = np.diff(Distim[idx])
                    mean_isi = np.mean(isi)
                    if mean_isi > 0:
                        CoVs[idx] = np.std(isi) / mean_isi
                    else:
                        CoVs[idx] = float("inf")
                else:
                    CoVs[idx] = float("inf")

            # Find MU with lowest CoV
            best_idx = min(CoVs, key=CoVs.get)  # type:ignore

            # Save the best MU
            pulseT_new.append(PulseT[best_idx])
            distim_new.append(Distim[best_idx])
            muscle_new.append(muscle[best_idx])

        # Mark all duplicates as processed
        for idx in duplicate_indices:
            processed[idx] = True

    # Convert results to appropriate formats
    if len(pulseT_new) > 0:
        pulseT_out = np.vstack(pulseT_new)
        muscle_out = np.array(muscle_new)
    else:
        pulseT_out = np.zeros((0, PulseT.shape[1]))
        muscle_out = np.array([])
        print("No MUs found")

    return pulseT_out, distim_new, muscle_out
