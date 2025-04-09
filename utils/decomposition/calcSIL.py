import numpy as np
from scipy import signal
from sklearn.cluster import KMeans


def maxk(signal, k):
    """Find the k largest values in the signal"""
    return np.partition(signal, -k, axis=-1)[..., -k:]


def calcSIL(X, w, fsamp):
    """
    Calculate the silhouette value for a source separation vector.

    Args:
        X: Whitened signal matrix
        w: Separation vector
        fsamp: Sampling frequency

    Returns:
        icasig: Estimated source signal
        spikes2: Detected spike indices
        sil: Silhouette value
    """
    # Ensure w is a column vector
    if w.ndim == 1:
        w = w.reshape(-1, 1)

    # Calculate the MU pulse train
    icasig = (np.dot(w.T, X)) * np.abs(np.dot(w.T, X))

    # Flatten for peak detection
    if icasig.ndim > 1:
        icasig = icasig.flatten()

    # Find peaks
    peaks, _ = signal.find_peaks(icasig, distance=round(fsamp * 0.02))

    # Initialize return values
    sil = 0
    spikes2 = peaks

    if len(peaks) > 1:
        # Normalize using top 10 values
        if len(peaks) >= 10:
            top_values = np.sort(icasig[peaks])[-10:]
        else:
            top_values = icasig[peaks]

        icasig = icasig / np.mean(top_values)

        # K-means clustering to separate the peaks
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(icasig[peaks].reshape(-1, 1))
        labels = kmeans.labels_
        centroids = kmeans.cluster_centers_

        # Find class with highest centroid
        idx2 = np.argmax(centroids)
        spikes2 = peaks[labels == idx2]

        # Calculate silhouette using the approach from processing_tools
        X_cluster = icasig[peaks].reshape(-1, 1)
        cluster_idx = labels == idx2
        other_idx = ~cluster_idx

        # Calculate within-cluster sum
        intra_sums = ((X_cluster[cluster_idx] - centroids[idx2]) ** 2).sum()

        # Calculate between-cluster sum
        if np.any(other_idx):
            inter_sums = ((X_cluster[cluster_idx] - centroids[1 - idx2]) ** 2).sum()
            # Calculate final silhouette value
            sil = (inter_sums - intra_sums) / max(intra_sums, inter_sums)

    return icasig, spikes2, sil
