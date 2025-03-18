import numpy as np
from scipy.signal import find_peaks
from sklearn.cluster import KMeans


def getspikes(w, X, fsamp):
    # Estimate the i source
    icasig = (w.T @ X) * np.abs(w.T @ X)

    # Peak detection
    peaks, spikes = find_peaks(icasig, distance=round(fsamp * 0.02))

    # Normalize
    if len(spikes) > 0:
        icasig = icasig / np.mean(np.sort(icasig[spikes])[-10:])

    if len(spikes) > 1:
        # Kmean classification
        kmeans = KMeans(n_clusters=2).fit(icasig[spikes].reshape(-1, 1))
        L = kmeans.labels_
        C = kmeans.cluster_centers_

        # Spikes should be in the class with the highest centroid
        idx2 = np.argmax(C)
        spikes2 = spikes[L == idx2]

        # Remove the outliers of the pulse train
        mask = icasig[spikes2] <= np.mean(icasig[spikes2]) + 3 * np.std(icasig[spikes2])
        spikes2 = spikes2[mask]
    else:
        spikes2 = spikes

    return icasig, spikes2
