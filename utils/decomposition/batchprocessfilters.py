import numpy as np
from scipy import signal
from sklearn.cluster import KMeans
import numba
from numba import jit


@jit(nopython=True, cache=True)
def maxk(arr, k):
    """Find the k largest values in the array using numba optimization"""
    if len(arr) <= k:
        return arr

    # Create a sorted copy of the last k elements
    result = np.sort(arr[:k])
    min_val = result[0]

    # Process the remaining elements
    for i in range(k, len(arr)):
        if arr[i] > min_val:
            # Find insertion position
            pos = 0
            while pos < k - 1 and result[pos + 1] < arr[i]:
                pos += 1

            # Shift elements to make room for the new value
            for j in range(0, pos):
                result[j] = result[j + 1]

            # Insert the new value
            result[pos] = arr[i]
            min_val = result[0]

    return result


def batchprocessfilters(MUFilters, wSIG, coordinates, exFactor, differentialmode, ltime, fsamp):
    """
    Optimized batch processing of filters.

    Args:
        MUFilters: Dictionary of motor unit filters for each window
        wSIG: Dictionary of whitened signals for each window
        coordinates: Plateau coordinates for each window
        exFactor: Extension factor
        differentialmode: Whether differential mode is enabled
        ltime: Length of the original signal
        fsamp: Sampling frequency

    Returns:
        PulseT: Generated pulse trains
        distime: Detected discharge times for each motor unit
    """
    # Count total number of motor units
    MUn = 0
    for nwin in range(len(wSIG)):
        if nwin < len(MUFilters) and MUFilters[nwin] is not None and hasattr(MUFilters[nwin], "shape"):
            if MUFilters[nwin].ndim > 1:
                MUn += MUFilters[nwin].shape[1]
            else:
                MUn += 1

    if MUn == 0:
        print("No motor units found")
        return np.zeros((0, ltime)), []

    # Initialize output arrays
    PulseT = np.zeros((MUn, ltime))
    distime = [np.array([], dtype=int) for _ in range(MUn)]
    MUnb = 0

    # Prepare parameters for peak detection - calculate once
    min_peak_distance = round(fsamp * 0.005)

    # Create a KMeans instance to reuse
    kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1, random_state=0)

    # Process each window
    for nwin in range(len(wSIG)):
        if nwin >= len(MUFilters) or MUFilters[nwin] is None or not hasattr(MUFilters[nwin], "shape"):
            continue

        # Get number of filters for this window
        if MUFilters[nwin].ndim > 1:
            num_filters = MUFilters[nwin].shape[1]
        else:
            num_filters = 1

        # Process each filter
        for j in range(num_filters):
            if MUnb >= MUn:
                continue

            # Process all windows with this filter
            for nwin2 in range(len(wSIG)):
                if nwin2 >= len(coordinates) // 2:
                    continue

                # Calculate indices
                if nwin2 * 2 + 1 >= len(coordinates):
                    continue

                idx_start = max(0, int(coordinates[nwin2 * 2] - 1))
                idx_end = min(ltime, int(coordinates[nwin2 * 2 + 1] + exFactor - 1 - differentialmode))

                # Skip if window is invalid
                if idx_start >= idx_end or nwin2 >= len(wSIG) or wSIG[nwin2] is None or len(wSIG[nwin2]) == 0:
                    continue

                # Get the filter vector
                if MUFilters[nwin].ndim > 1:
                    filter_vec = MUFilters[nwin][:, j]
                else:
                    filter_vec = MUFilters[nwin]

                # Calculate the dot product efficiently
                try:
                    result = np.dot(filter_vec, wSIG[nwin2])

                    # Handle shape mismatch
                    if len(result) == idx_end - idx_start:
                        PulseT[MUnb, idx_start:idx_end] = result
                    else:
                        # Adjust the target region
                        adjusted_end = min(idx_start + len(result), ltime)
                        PulseT[MUnb, idx_start:adjusted_end] = result[: adjusted_end - idx_start]
                except Exception as e:
                    print(f"Error in dot product: {e}")

            # Efficient squaring and rectifying
            PulseT[MUnb, :] = PulseT[MUnb, :] * np.abs(PulseT[MUnb, :])

            # Peak detection
            try:
                peaks, _ = signal.find_peaks(PulseT[MUnb, :], distance=min_peak_distance)

                if len(peaks) > 0:
                    # Normalize using top values
                    if len(peaks) >= 10:
                        top_values = np.partition(PulseT[MUnb, peaks], -10)[-10:]
                    else:
                        top_values = PulseT[MUnb, peaks]

                    mean_val = np.mean(top_values)
                    if mean_val > 0:
                        PulseT[MUnb, :] /= mean_val

                    # K-means clustering for spike selection
                    if len(peaks) >= 2:
                        # Reshape data for KMeans
                        X = PulseT[MUnb, peaks].reshape(-1, 1)

                        # Fit KMeans
                        kmeans.fit(X)
                        labels = kmeans.labels_
                        centroids = kmeans.cluster_centers_

                        # Find the higher centroid class
                        idx = np.argmax(centroids)
                        selected_peaks = peaks[labels == idx]

                        # Remove outliers efficiently
                        if len(selected_peaks) > 0:
                            peak_vals = PulseT[MUnb, selected_peaks]
                            threshold = np.mean(peak_vals) + 3 * np.std(peak_vals)
                            outlier_mask = peak_vals <= threshold
                            selected_peaks = selected_peaks[outlier_mask]

                        distime[MUnb] = selected_peaks
                    else:
                        distime[MUnb] = peaks

            except Exception as e:
                print(f"Error in peak detection: {e}")

            # Increment motor unit counter
            MUnb += 1

    # Return only the valid motor units
    if MUnb == 0:
        return np.zeros((0, ltime)), []

    return PulseT[:MUnb], distime[:MUnb]
