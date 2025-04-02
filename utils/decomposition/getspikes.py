import numpy as np
from scipy.signal import find_peaks
from sklearn.cluster import KMeans


def maxk(signal, k):
    """Find the k largest values in the signal"""
    return np.partition(signal, -k, axis=-1)[..., -k:]


def getspikes(w, X, fsamp):
    """
    Estimate the signal source and detect peaks based on gradient convolutive kernel compensation.
    Aims to remove spurious discharges to improve source separation vector estimate.

    Args:
        w: Separation vector
        X: Whitened signal matrix
        fsamp: Sampling frequency

    Returns:
        source_pred: Estimated source signal
        spikes: Detected spike indices
    """
    # Handle matrices of different dimensions
    if w.ndim == 1:
        w = w.reshape(-1, 1)

    # Compute icasig as (w.T @ X) * abs(w.T @ X)
    source_pred = np.dot(w.T, X)
    source_pred = source_pred * np.abs(source_pred)

    # Make sure source_pred is 1D for find_peaks
    if source_pred.ndim > 1:
        source_pred = source_pred.flatten()

    # Peak detection
    peaks, _ = find_peaks(np.squeeze(source_pred), distance=round(fsamp * 0.02))

    # Normalize using top values
    if len(peaks) > 0:
        if len(peaks) >= 10:
            top_values = maxk(source_pred[peaks], 10)
        else:
            top_values = source_pred[peaks]

        mean_max = np.mean(top_values)
        if mean_max > 0:
            source_pred = source_pred / mean_max

    # If enough spikes, use K-means clustering
    if len(peaks) > 1:
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(source_pred[peaks].reshape(-1, 1))
        spikes_ind = np.argmax(kmeans.cluster_centers_)
        spikes = peaks[kmeans.labels_ == spikes_ind]

        # Remove outliers from the spike train
        spikes = spikes[source_pred[spikes] <= np.mean(source_pred[spikes]) + 3 * np.std(source_pred[spikes])]
    else:
        spikes = peaks

    return source_pred, spikes
