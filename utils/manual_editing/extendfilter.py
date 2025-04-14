import numpy as np
from scipy import signal
from sklearn.cluster import KMeans
from utils.decomposition.bandpassingals import bandpassingals
from utils.decomposition.extend import extend
from utils.decomposition.whiteesig import whiteesig
from utils.manual_editing.pcaesig import pcaesig


def extendfilter(EMG, EMGmask, PulseT, distime, idx, fsamp, EMGtype):
    nbextchan = 1000
    mask = EMGmask == 0
    EMG = EMG[mask][:, idx]
    EMG = bandpassingals(EMG, fsamp, EMGtype)

    # Find spikes in the window (excluding edges)
    edge_samples = round(0.1 * fsamp)
    valid_window = np.arange(idx[0] + edge_samples, idx[-1] - edge_samples + 1)
    spikes1 = np.intersect1d(valid_window, distime)

    if len(spikes1) > 0:
        # Adjust spike indices to be relative to the window
        spikes2 = spikes1 - idx[0]

        # Extend the EMG signal
        exFactor1 = round(nbextchan / EMG.shape[0])
        eSIG = extend(EMG, exFactor1)

        # Create covariance matrix and its pseudoinverse
        ReSIG = np.dot(eSIG, eSIG.T) / eSIG.shape[1]
        iReSIGt = np.linalg.pinv(ReSIG)

        # Perform PCA and whitening
        E, D = pcaesig(eSIG)
        wSIG, _, dewhiteningMatrix = whiteesig(eSIG, E, D)  # type:ignore

        # Calculate the filter as the sum of whitened signal at spike times
        MUFilters = np.sum(wSIG[:, spikes2], axis=1).reshape(-1, 1)

        # Update the pulse train
        Pt = np.dot(np.dot(np.dot(dewhiteningMatrix, MUFilters).T, iReSIGt), eSIG)
        Pt = Pt[0, : EMG.shape[1]]

        # Set edges to zero
        Pt[:edge_samples] = 0
        Pt[-edge_samples:] = 0

        # Normalize the pulse train
        Pt = Pt * np.abs(Pt)
        peaks, _ = signal.find_peaks(Pt, distance=round(fsamp * 0.005))

        if len(peaks) > 2:
            # Normalize using the top 10 peak values or all if fewer
            if len(peaks) >= 10:
                top_values = np.sort(Pt[peaks])[-10:]
            else:
                top_values = Pt[peaks]
            Pt = Pt / np.mean(top_values)

            # K-means clustering to separate peaks
            kmeans = KMeans(n_clusters=2, random_state=0).fit(Pt[peaks].reshape(-1, 1))
            labels = kmeans.labels_
            centroids = kmeans.cluster_centers_

            # Find the class with the highest centroid
            idx2 = np.argmax(centroids)
            spikes2 = peaks[labels == idx2]

            # Remove outliers
            outlier_threshold = np.mean(Pt[spikes2]) + 3 * np.std(Pt[spikes2])
            spikes2 = spikes2[Pt[spikes2] <= outlier_threshold]

            # Update the pulse train in the time window
            start_idx = idx[0] + edge_samples - 1
            end_idx = idx[-1] - edge_samples
            PulseT[start_idx:end_idx] = Pt[edge_samples:-edge_samples]

            # Update the discharge times
            distime = np.setdiff1d(distime, spikes1)
            distime = np.append(distime, spikes2 + idx[0] - 1)
            distime = np.sort(distime)

    return PulseT, distime
