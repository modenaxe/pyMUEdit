import numpy as np
from scipy import signal
from sklearn.cluster import KMeans


def calcSIL(X, w, fsamp):
    icasig = (np.dot(w.T, X)) * np.abs(np.dot(w.T, X))
    peaks, _ = signal.find_peaks(icasig, distance=round(fsamp * 0.02))

    if len(peaks) > 1:
        top_values = np.sort(icasig[peaks])[-10:]
        icasig = icasig / np.mean(top_values)

        kmeans = KMeans(n_clusters=2, random_state=0).fit(icasig[peaks].reshape(-1, 1))
        labels = kmeans.labels_
        centroids = kmeans.cluster_centers_

        idx2 = np.argmax(centroids)
        spikes2 = peaks[labels == idx2]

        # Calculate silhouette
        X_cluster = icasig[peaks].reshape(-1, 1)
        cluster_idx = labels == idx2
        other_idx = np.logical_not(cluster_idx)

        within = np.sum(np.square(X_cluster[cluster_idx] - centroids[idx2])) / np.sum(cluster_idx)
        if np.sum(other_idx) > 0:
            between = np.sum(np.square(X_cluster[cluster_idx] - centroids[1 - idx2])) / np.sum(cluster_idx)
            sil = (between - within) / max(within, between)
        else:
            sil = 0

        return icasig, spikes2, sil
    else:
        return icasig, peaks, 0
