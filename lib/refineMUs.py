import numpy as np
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
from lib.extend import extend


def refineMUs(EMG, EMGmask, PulseTold, Distimeold, fsamp):
    print("Refining MU pulse trains - Signal extension")

    # Remove masked channels
    EMG = EMG[EMGmask == 0, :]

    # Signal extension
    nbextchan = 1500
    exFactor = round(nbextchan / EMG.shape[0])
    eSIG = extend(EMG, exFactor)
    ReSIG = eSIG @ eSIG.T / eSIG.shape[1]
    iReSIGt = np.linalg.pinv(ReSIG)

    PulseT = np.zeros_like(PulseTold)
    Distime = [None] * PulseTold.shape[0]

    # Recalculate MUfilters
    for i in range(PulseTold.shape[0]):
        print(f"Refining MU#{i+1} out of {PulseTold.shape[0]} MUs")

        # Remove outliers
        valid_indices = PulseTold[i, Distimeold[i]] <= np.mean(PulseTold[i, Distimeold[i]]) + 3 * np.std(
            PulseTold[i, Distimeold[i]]
        )
        filtered_distime = Distimeold[i][valid_indices]

        # Calculate motor unit filter
        MUFilters = np.sum(eSIG[:, filtered_distime], axis=1, keepdims=True)

        # Apply filter to signal
        IPTtmp = (MUFilters.T @ iReSIGt) @ eSIG
        PulseT[i, :] = IPTtmp[0, : EMG.shape[1]]

        # Nonlinear transformation (square and rectify)
        PulseT[i, :] = np.abs(PulseT[i, :]) * PulseT[i, :]

        # Peak detection
        peaks, spikes = find_peaks(PulseT[i, :], distance=round(fsamp * 0.02))

        # Normalize
        if len(spikes) >= 10:
            max_vals = np.sort(PulseT[i, spikes])[-10:]
            PulseT[i, :] = PulseT[i, :] / np.mean(max_vals)

        # K-means classification
        if len(spikes) > 1:
            kmeans = KMeans(n_clusters=2, random_state=0).fit(PulseT[i, spikes].reshape(-1, 1))
            L = kmeans.labels_
            C = kmeans.cluster_centers_

            # Find class with highest centroid
            idx = np.argmax(C)
            Distime[i] = spikes[L == idx]
        else:
            Distime[i] = spikes

    return PulseT, Distime
