import numpy as np
import scipy
from sklearn.cluster import KMeans


def get_spikes(w_n, Z, fsamp):
    """
    Identifies spikes (motor unit action potentials) in the signal.

    Uses gradient convolutive kernel compensation to detect potential spikes
    and removes spurious discharges to improve the source separation
    vector estimate. This reduces ISI variability and minimizes
    the covariation in MU discharges.
    """

    source_pred = np.dot(np.transpose(w_n), Z).real  # element-wise square of the input to estimate the ith source
    source_pred = np.multiply(source_pred, abs(source_pred))  # keep the negatives
    peaks, _ = scipy.signal.find_peaks(np.squeeze(source_pred), distance=np.round(fsamp * 0.02) + 1)
    source_pred /= np.mean(maxk(source_pred[peaks], 10))

    if len(peaks) > 1:

        # two classes: 1) spikes 2) noise
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(source_pred[peaks].reshape(-1, 1))
        spikes_ind = np.argmax(kmeans.cluster_centers_)
        spikes = peaks[np.where(kmeans.labels_ == spikes_ind)]

        # remove outliers from the spikes cluster with a std-based threshold
        spikes = spikes[source_pred[spikes] <= np.mean(source_pred[spikes]) + 4 * np.std(source_pred[spikes])]
    else:
        spikes = peaks

    return source_pred, spikes


def maxk(signal, k):
    """
    Returns the k largest values in the signal.
    Helper function used by get_spikes.
    """
    return np.partition(signal, -k, axis=-1)[..., -k:]
