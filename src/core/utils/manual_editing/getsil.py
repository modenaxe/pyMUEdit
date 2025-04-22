import numpy as np
from scipy import signal
from sklearn.cluster import KMeans


def getsil(PulseT, fsamp):
    peaks, _ = signal.find_peaks(PulseT, distance=round(fsamp * 0.005))
    if len(peaks) == 0:
        return 0

    # Normalize the pulse train using the top 10 peak values
    top_values = np.sort(PulseT[peaks])[-10:]
    PulseT = PulseT / np.mean(top_values)

    # K-means clustering to separate the peaks
    X = PulseT[peaks].reshape(-1, 1)
    kmeans = KMeans(n_clusters=2, random_state=0).fit(X)
    labels = kmeans.labels_
    centroids = kmeans.cluster_centers_

    # Find the class with the highest centroid
    idx2 = np.argmax(centroids)

    # Calculate silhouette
    cluster_idx = labels == idx2
    other_idx = np.logical_not(cluster_idx)

    # Calculate within-cluster distance
    within = np.sum(np.square(X[cluster_idx] - centroids[idx2])) / np.sum(cluster_idx)

    # Calculate between-cluster distance
    if np.sum(other_idx) > 0:
        between = np.sum(np.square(X[cluster_idx] - centroids[1 - idx2])) / np.sum(cluster_idx)
        sil = (between - within) / max(within, between)
    else:
        sil = 0

    return sil
