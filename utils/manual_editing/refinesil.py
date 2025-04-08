import numpy as np
from scipy.signal import find_peaks
from sklearn.cluster import KMeans


def refinesil(PulseT, distime, fsamp):
    # Peak detection
    spikes, _ = find_peaks(PulseT, distance=round(fsamp * 0.005))

    # Normalization
    if len(spikes) >= 10:
        max_vals = np.sort(PulseT[spikes])[-10:]
        PulseT = PulseT / np.mean(max_vals)

    # Initialize silhouette values array
    sil_vals = np.zeros((int(np.floor(len(PulseT) / fsamp)), 2))

    # Calculate silhouette values for each time window
    for i in range(int(np.floor(len(PulseT) / fsamp))):
        # Find spikes in current window
        idx = np.where((spikes > 1 + (i - 1) * fsamp) & (spikes < i * fsamp))[0]
        idx1 = np.where((distime > 1 + (i - 1) * fsamp) & (distime < i * fsamp))[0]

        if len(idx) > 2 and len(idx1) > 2:
            # Run K-means
            kmeans = KMeans(n_clusters=2, random_state=0).fit(PulseT[spikes[idx]].reshape(-1, 1))
            L = kmeans.labels_
            C = kmeans.cluster_centers_

            # Calculate intra-cluster distances
            idx2 = np.argmax(C)
            within = kmeans.inertia_

            # Calculate inter-cluster distances
            other_cluster = 1 if idx2 == 0 else 0
            points_in_cluster = PulseT[spikes[idx]][L == idx2].reshape(-1, 1)
            between = np.sum((points_in_cluster - C[other_cluster]) ** 2)

            # Store time point and silhouette value
            sil_vals[i, 0] = np.floor(i * fsamp - (fsamp / 2))
            sil_vals[i, 1] = (between - within) / max(within, between)
        else:
            sil_vals[i, 0] = np.floor(i * fsamp - (fsamp / 2))
            sil_vals[i, 1] = np.nan

    return sil_vals
