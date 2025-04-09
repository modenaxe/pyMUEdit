import numpy as np
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
from utils.decomposition.extend import extend


def maxk(signal, k):
    """Find the k largest values in the signal"""
    return np.partition(signal, -k, axis=-1)[..., -k:]


def refineMUs(EMG, EMGmask, PulseTold, Distimeold, fsamp):
    """
    Refine motor unit pulse trains by recomputing with the original signal.

    Args:
        EMG: Original EMG signal
        EMGmask: Mask of rejected channels
        PulseTold: Original pulse trains
        Distimeold: Original discharge times
        fsamp: Sampling frequency

    Returns:
        PulseT: Refined pulse trains
        Distime: Refined discharge times
    """
    # Remove masked channels
    try:
        valid_channels = np.where(EMGmask == 0)[0]
        if len(valid_channels) > 0:
            print(f"Using {len(valid_channels)} non-masked channels")
            EMG_valid = EMG[valid_channels, :]
        else:
            print("All channels are masked, using all channels")
            EMG_valid = EMG
    except Exception as e:
        print(f"Error applying mask: {e}. Using all channels.")
        EMG_valid = EMG

    # Signal extension
    try:
        nbextchan = 1500
        channels = EMG_valid.shape[0] if hasattr(EMG_valid, "shape") else 64
        exFactor = round(nbextchan / channels)

        # Extend the EMG signal
        eSIG = extend(EMG_valid, exFactor)

        # Calculate covariance and pseudo-inverse
        ReSIG = eSIG @ eSIG.T / eSIG.shape[1]

        iReSIGt = np.linalg.pinv(ReSIG)
    except Exception as e:
        print(f"Error in signal extension: {e}")
        return PulseTold, Distimeold

    # Initialize output arrays
    PulseT = np.zeros_like(PulseTold)
    Distime = [None] * PulseTold.shape[0]

    # Recalculate MU filters
    for i in range(PulseTold.shape[0]):
        try:
            # Skip if no discharges
            if i >= len(Distimeold) or Distimeold[i] is None or len(Distimeold[i]) == 0:
                print(f"No discharges for MU #{i+1}, skipping")
                continue

            # Remove outliers
            valid_indices = PulseTold[i, Distimeold[i]] <= np.mean(PulseTold[i, Distimeold[i]]) + 3 * np.std(
                PulseTold[i, Distimeold[i]]
            )
            filtered_distime = Distimeold[i][valid_indices]

            if len(filtered_distime) == 0:
                print(f"No valid discharges after outlier removal for MU #{i+1}, skipping")
                continue

            # Calculate motor unit filter
            MUFilters = np.sum(eSIG[:, filtered_distime], axis=1, keepdims=True)

            # Apply filter to signal
            IPTtmp = (MUFilters.T @ iReSIGt) @ eSIG
            if IPTtmp.shape[1] >= EMG.shape[1]:
                PulseT[i, :] = IPTtmp[0, : EMG.shape[1]]
            else:
                print(f"Warning: IPTtmp shape {IPTtmp.shape} doesn't match EMG shape {EMG.shape}")
                PulseT[i, : IPTtmp.shape[1]] = IPTtmp[0, :]

            # Nonlinear transformation (square and rectify)
            PulseT[i, :] = np.abs(PulseT[i, :]) * PulseT[i, :]

            # Peak detection
            peaks, _ = find_peaks(PulseT[i, :], distance=round(fsamp * 0.02))

            # Normalize
            if len(peaks) >= 10:
                max_vals = maxk(PulseT[i, peaks], 10)
                mean_val = np.mean(max_vals)
                if mean_val > 0:
                    PulseT[i, :] = PulseT[i, :] / mean_val
            elif len(peaks) > 0:
                mean_val = np.mean(PulseT[i, peaks])
                if mean_val > 0:
                    PulseT[i, :] = PulseT[i, :] / mean_val

            # K-means classification
            if len(peaks) > 1:
                kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(PulseT[i, peaks].reshape(-1, 1))
                L = kmeans.labels_
                C = kmeans.cluster_centers_

                # Find class with highest centroid
                idx = np.argmax(C)
                Distime[i] = peaks[L == idx]

                # Remove outliers
                if len(Distime[i]) > 0:
                    peak_vals = PulseT[i, Distime[i]]
                    outlier_mask = peak_vals <= (np.mean(peak_vals) + 3 * np.std(peak_vals))
                    Distime[i] = Distime[i][outlier_mask]
            else:
                Distime[i] = peaks
                print(f"Only {len(peaks)} peaks, skipping clustering")

        except Exception as e:
            print(f"Error refining MU #{i+1}: {e}")
            Distime[i] = Distimeold[i] if i < len(Distimeold) else np.array([], dtype=int)

    return PulseT, Distime
