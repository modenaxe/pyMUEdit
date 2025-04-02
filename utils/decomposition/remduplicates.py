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


def remduplicates(PulseT, distime, distime2, maxlag, jitter_val, tol, fsamp):
    """
    Remove duplicated motor units based on discharge pattern similarity.
    Fixed the indexing issue when removing elements during iteration.

    Args:
        PulseT: Motor unit pulse trains
        distime: List of discharge times for each motor unit
        distime2: Second list of discharge times (used for alignment)
        maxlag: Maximum lag for cross-correlation
        jitter_val: Jitter tolerance in seconds
        tol: Threshold for considering units as duplicates
        fsamp: Sampling frequency

    Returns:
        Filtered pulse trains and discharge times
    """
    # Convert jitter to samples
    jit = round(jitter_val * fsamp)

    # Make copies of input so we don't modify the original
    pulse_trains_copy = PulseT.copy()

    # Flag array to mark which MUs have been processed
    processed = np.zeros(len(distime), dtype=bool)

    # Output arrays
    distimenew = []
    Pulsenew = []

    # Prepare for pairwise comparisons
    mu_count = len(distime)

    # Create binary spike trains for all MUs
    firings = np.zeros((mu_count, PulseT.shape[1]), dtype=bool)
    jittered_times = []

    for i in range(mu_count):
        if distime2[i] is None or len(distime2[i]) == 0:
            print(f"  MU #{i+1}: No spikes to process")
            jittered_times.append(np.array([], dtype=int))
            continue

        # Create binary spike train
        spikes = distime2[i]
        valid_indices = spikes < PulseT.shape[1]
        valid_spikes = spikes[valid_indices]

        if len(valid_spikes) > 0:
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
        else:
            print(f"  MU #{i+1}: No valid spikes")
            jittered_times.append(np.array([], dtype=int))

    # Continue until all MUs have been processed
    while not np.all(processed):
        # Find the first unprocessed MU
        reference_idx = np.argmin(processed)

        # Skip if it has no discharges
        if len(distime[reference_idx]) == 0:
            processed[reference_idx] = True
            print(f"  Skipping MU #{reference_idx+1} - no discharge times")
            continue

        # Find all duplicates of this MU
        duplicate_indices = [reference_idx]  # Always include self

        # Calculate shifted times for all other unprocessed MUs
        shifted_times = {}
        similarities = {}

        for j in range(mu_count):
            # Skip if already processed or same as reference
            if processed[j] or j == reference_idx:
                continue

            # Skip if no discharge times
            if len(distime[j]) == 0 or len(jittered_times[j]) == 0:
                print(f"  Skipping MU #{j+1} - no discharge times")
                continue

            # Calculate cross-correlation
            c, lags = xcorr(firings[reference_idx], firings[j], maxlag)

            # Find optimal lag
            idx = np.argmax(np.abs(c))
            max_corr = c[idx]
            lag = lags[idx]

            # Calculate similarity with optimal lag
            shifted = np.array([t + lag for t in jittered_times[j] if 0 <= t + lag < PulseT.shape[1]])
            common = np.intersect1d(jittered_times[reference_idx], shifted)

            # Remove consecutive common times
            if len(common) > 1:
                mask = np.concatenate(([True], np.diff(common) > 1))
                common = common[mask]

            # Calculate similarity
            if len(distime[reference_idx]) > 0 and len(distime[j]) > 0:
                similarity = len(common) / max(len(distime[reference_idx]), len(distime[j]))
                similarities[j] = similarity
                shifted_times[j] = shifted

                # If similar enough, mark as duplicate
                if similarity >= tol:
                    duplicate_indices.append(j)  # type:ignore
                    print(f"  MU #{j+1} is a DUPLICATE of MU #{reference_idx+1}")

        # If we found duplicates, select the best one
        if len(duplicate_indices) > 1:
            print(f"  Found {len(duplicate_indices)} duplicates: {duplicate_indices}")

            # Calculate CoV for all duplicates
            CoVs = {}
            for idx in duplicate_indices:
                if len(distime[idx]) > 1:
                    isi = np.diff(distime[idx])
                    mean_isi = np.mean(isi)
                    if mean_isi > 0:
                        CoVs[idx] = np.std(isi) / mean_isi
                    else:
                        CoVs[idx] = float("inf")
                else:
                    CoVs[idx] = float("inf")

            # Find MU with minimum CoV
            best_idx = min(CoVs, key=CoVs.get)  # type:ignore

            # Save the best MU
            distimenew.append(distime[best_idx])
            Pulsenew.append(pulse_trains_copy[best_idx])
        else:
            distimenew.append(distime[reference_idx])
            Pulsenew.append(pulse_trains_copy[reference_idx])

        # Mark all duplicates as processed
        for idx in duplicate_indices:
            processed[idx] = True

    # Convert to numpy array
    if Pulsenew:
        Pulsenew = np.vstack(Pulsenew)
        print(f"Final shape of pulse trains: {Pulsenew.shape}")
    else:
        Pulsenew = np.zeros((0, PulseT.shape[1]))
        print("No pulse trains survived")

    return distimenew, Pulsenew
