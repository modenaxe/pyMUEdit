import numpy as np
import scipy
from sklearn.cluster import KMeans
from core.utils.decomposition.extend_emg import extend_emg
from core.utils.decomposition.get_spikes import maxk


def refine_mus(signal, signal_mask, pulse_trains_n_1, discharge_times_n_1, fsamp):
    """
    Refines motor unit pulse trains using a second pass.

    Recalculates and improves the accuracy of motor unit templates and discharge times
    by using the discharge times from the first pass to create better filters.
    """

    signal = [x for i, x in enumerate(signal) if signal_mask[i] != 1]
    nbextchan = 1500
    extension_factor = round(nbextchan / np.shape(signal)[0])
    extend_obvs = np.zeros([np.shape(signal)[0] * (extension_factor), np.shape(signal)[1] + extension_factor - 1])
    extend_obvs = extend_emg(extend_obvs, signal, extension_factor)
    re_obvs = np.matmul(extend_obvs, extend_obvs.T) / np.shape(extend_obvs)[1]
    invre_obvs = np.linalg.pinv(re_obvs)
    pulse_trains_n = np.zeros(np.shape(pulse_trains_n_1))
    discharge_times_n = [None] * len(pulse_trains_n_1)

    # recalculating the mu filters
    for mu in range(len(pulse_trains_n_1)):

        mu_filters = np.sum(extend_obvs[:, discharge_times_n_1[mu]], axis=1)
        IPTtmp = np.dot(np.dot(mu_filters.T, invre_obvs), extend_obvs)
        pulse_trains_n[mu, :] = IPTtmp[: np.shape(signal)[1]]

        pulse_trains_n[mu, :] = np.multiply(pulse_trains_n[mu, :], abs(pulse_trains_n[mu, :]))
        peaks, _ = scipy.signal.find_peaks(np.squeeze(pulse_trains_n[mu, :]), distance=np.round(fsamp * 0.02) + 1)
        pulse_trains_n[mu, :] /= np.mean(maxk(pulse_trains_n[mu, peaks], 10))
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(pulse_trains_n[mu, peaks].reshape(-1, 1))
        spikes_ind = np.argmax(kmeans.cluster_centers_)
        discharge_times_n[mu] = peaks[np.where(kmeans.labels_ == spikes_ind)]

    print(f"Refined {len(pulse_trains_n_1)} MUs")

    return pulse_trains_n, discharge_times_n
