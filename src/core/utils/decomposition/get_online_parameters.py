# type:ignore
import numpy as np
from sklearn.cluster import KMeans
from utils.decomposition.extend_emg import extend_emg
from utils.decomposition.get_spikes import maxk


def get_online_parameters(data, rejected_channels, mu_filters, chans_per_electrode, fsamp, g):
    """
    Calculates parameters needed for online EMG decomposition.

    Returns extension factor, inverted extended data, normalization values,
    and cluster centroids for real-time processing.
    """

    data_slice = data[chans_per_electrode[g] * (g) : (g + 1) * chans_per_electrode[g], :]  # will need to be generalised
    rejected_channels_slice = rejected_channels[g] == 1
    cleaned_data = np.delete(data_slice, rejected_channels_slice, 0)

    # get the first estimate of pulse trains using the previously derived mu filters, applied to the emg data
    ext_factor = int(np.round(1500 / np.shape(cleaned_data)[0]))
    extended_data = np.zeros([1, np.shape(cleaned_data)[0] * (ext_factor), np.shape(cleaned_data)[1] + ext_factor - 1])
    extended_data = extend_emg(extended_data, cleaned_data, ext_factor)

    # get inverted version
    inv_extended_data = np.linalg.pinv(extended_data)

    # initialisations for extracting pulse trains and centroids in clustering
    mu_count = np.shape(mu_filters)[1]
    pulse_trains = np.zeros([mu_count, np.shape(data)[1]])
    norm = np.zeros[mu_count]
    centroids = np.zeros[mu_count, 2]

    for mu in range(mu_count):

        pulse_temp = (mu_filters[:, mu].T @ inv_extended_data) @ extended_data

        pulse_trains = pulse_temp[: np.shape(data)[1]]
        pulse_trains = np.multiply(pulse_trains, abs(pulse_trains))  # keep the negatives

        # peaks variable holds the indices of all peaks
        peaks, _ = scipy.signal.find_peaks(np.squeeze(pulse_trains), distance=np.round(fsamp * 0.02) + 1)

        if len(peaks) > 1:
            # two classes: 1) spikes 2) noise
            kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(pulse_trains[mu, peaks].reshape(-1, 1))

            spikes_ind = np.argmax(kmeans.cluster_centers_)
            spikes = peaks[np.where(kmeans.labels_ == spikes_ind)]
            spikes = spikes[pulse_trains[spikes] <= np.mean(pulse_trains[spikes]) + 3 * np.std(pulse_trains[spikes])]

            noise_ind = np.argmin(kmeans.cluster_centers)
            noise = peaks[np.where(kmeans.labels_ == noise_ind)]
            norm[mu] = maxk(pulse_trains[spikes], 10)
            pulse_trains = pulse_trains / norm[mu]
            centroids[mu, 0] = (
                KMeans(n_clusters=1, init="k-means++", n_init=1)
                .fit(pulse_trains[spikes].reshape(-1, 1))
                .cluster_centers
            )
            centroids[mu, 1] = (
                KMeans(n_clusters=1, init="k-means++", n_init=1).fit(pulse_trains[noise].reshape(-1, 1)).cluster_centers
            )

    return ext_factor, inv_extended_data, norm, centroids
