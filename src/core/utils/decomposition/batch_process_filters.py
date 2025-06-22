import numpy as np
import scipy
from sklearn.cluster import KMeans
from core.utils.decomposition.get_spikes import maxk


def batch_process_filters(whit_sig, mu_filters, plateau, extender, diff, orig_sig_size, fsamp):
    """
    Processes motor unit filters across all signal batches.

    Combines filter outputs across all batched windows to create consistent
    pulse trains and discharge times for the entire signal duration.
    """
    mu_count = 0
    for batch in range(np.shape(whit_sig)[0]):
        mu_count += np.shape(mu_filters[batch])[1]

    pulse_trains = np.zeros([mu_count, orig_sig_size])
    discharge_times = [None] * mu_count
    mu_batch_count = 0

    for win_1 in range(np.shape(whit_sig)[0]):
        for mu_candidate in range(np.shape(mu_filters[win_1])[1]):
            for win_2 in range(np.shape(whit_sig)[0]):

                pulse_trains[
                    mu_batch_count, int(plateau[win_2 * 2]) : int(plateau[(win_2 + 1) * 2 - 1]) + extender - diff
                ] = (np.transpose(mu_filters[win_1][:, mu_candidate]) @ whit_sig[win_1])

            pulse_trains[mu_batch_count, :] = np.multiply(
                pulse_trains[mu_batch_count, :], abs(pulse_trains[mu_batch_count, :])
            )

            # peaks variable holds the indices of all peaks
            peaks, _ = scipy.signal.find_peaks(
                np.squeeze(pulse_trains[mu_batch_count, :]), distance=np.round(fsamp * 0.005) + 1
            )
            pulse_trains[mu_batch_count, :] /= np.mean(maxk(pulse_trains[mu_batch_count, :], 10))

            # two classes: 1) spikes 2) noise
            kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(
                pulse_trains[mu_batch_count, peaks].reshape(-1, 1)
            )
            spikes_ind = np.argmax(kmeans.cluster_centers_)
            discharge_times[mu_batch_count] = peaks[np.where(kmeans.labels_ == spikes_ind)]
            print(f"Batch processing MU#{mu_batch_count+1} out of {mu_count} MUs")
            mu_batch_count += 1

    return pulse_trains, discharge_times
