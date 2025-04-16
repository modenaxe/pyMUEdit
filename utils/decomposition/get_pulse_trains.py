import numpy as np
import scipy
from sklearn.cluster import KMeans
from utils.decomposition.extend_emg import extend_emg
from utils.decomposition.get_spikes import maxk


def get_pulse_trains(data, rejected_channels, mu_filters, chans_per_electrode, fsamp, g):
    """
    Extracts pulse trains and discharge times from EMG data using precomputed MU filters.

    Used for post-processing when combining with biofeedback.
    """

    data_slice = data[chans_per_electrode[g] * (g) : (g + 1) * chans_per_electrode[g], :]
    rejected_channels_slice = rejected_channels[g] == 1
    cleaned_data = np.delete(data_slice, rejected_channels_slice, 0)

    # get the first estimate of pulse trains using the previously derived mu filters, applied to the emg data
    ext_factor = int(np.round(1500 / np.shape(cleaned_data)[0]))
    extended_data = np.zeros([1, np.shape(cleaned_data)[0] * (ext_factor), np.shape(cleaned_data)[1] + ext_factor - 1])
    extended_data = extend_emg(extended_data, cleaned_data, ext_factor)

    # get the real and inverted versions
    inv_extended_data = np.linalg.pinv(extended_data)

    # initialisations for extracting pulse trains in clustering
    mu_count = np.shape(mu_filters)[1]
    pulse_trains = np.zeros([mu_count, np.shape(data)[1]])
    discharge_times = [None] * mu_count  # do not know size yet, so can only predefine as a list

    for mu in range(mu_count):

        pulse_temp = (mu_filters[:, mu].T @ inv_extended_data) @ extended_data
        pulse_trains[mu, :] = pulse_temp[: np.shape(data)[1]]
        pulse_trains[mu, :] = np.multiply(pulse_trains[mu, :], abs(pulse_trains[mu, :]))  # keep the negatives

        # peaks variable holds the indices of all peaks
        peaks, _ = scipy.signal.find_peaks(np.squeeze(pulse_trains[mu, :]), distance=np.round(fsamp * 0.02) + 1)
        pulse_trains[mu, :] /= np.mean(maxk(pulse_trains[mu, peaks], 10))

        if len(peaks) > 1:

            # two classes: 1) spikes 2) noise
            kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(pulse_trains[mu, peaks].reshape(-1, 1))
            spikes_ind = np.argmax(kmeans.cluster_centers_)
            spikes = peaks[np.where(kmeans.labels_ == spikes_ind)]

            # remove outliers from the spikes cluster with a std-based threshold
            discharge_times[mu] = spikes[
                pulse_trains[mu, spikes] <= np.mean(pulse_trains[mu, spikes]) + 3 * np.std(pulse_trains[mu, spikes])
            ]
        else:
            discharge_times[mu] = peaks

    return pulse_trains, discharge_times, ext_factor
