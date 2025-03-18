import numpy as np
from scipy import signal
from sklearn.cluster import KMeans


def batchprocessfilters(MUFilters, wSIG, coordinates, exFactor, differentialmode, ltime, fsamp):
    MUn = 0
    for nwin in range(len(wSIG)):
        MUn += MUFilters[nwin].shape[1]

    PulseT = np.zeros((MUn, ltime))
    distime = [None] * MUn
    MUnb = 0

    for nwin in range(len(wSIG)):
        for j in range(MUFilters[nwin].shape[1]):
            for nwin2 in range(len(wSIG)):
                idx_start = coordinates[nwin2 * 2] - 1
                idx_end = coordinates[nwin2 * 2 + 1] + exFactor - 1 - differentialmode
                PulseT[MUnb, idx_start:idx_end] = np.dot(MUFilters[nwin][:, j].T, wSIG[nwin2])

            PulseT[MUnb, :] = PulseT[MUnb, :] * np.abs(PulseT[MUnb, :])
            peaks, _ = signal.find_peaks(PulseT[MUnb, :], distance=round(fsamp * 0.005))

            if len(peaks) > 0:
                top_values = np.sort(PulseT[MUnb, peaks])[-10:]
                PulseT[MUnb, :] = PulseT[MUnb, :] / np.mean(top_values)

                kmeans = KMeans(n_clusters=2, random_state=0).fit(PulseT[MUnb, peaks].reshape(-1, 1))
                labels = kmeans.labels_
                centroids = kmeans.cluster_centers_

                idx = np.argmax(centroids)
                distime[MUnb] = peaks[labels == idx]

            MUnb += 1

    PulseT = PulseT[:, :ltime]
    return PulseT, distime
