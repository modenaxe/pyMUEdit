import numpy as np
from scipy.signal import correlate


def remduplicates(PulseT, distime, distime2, maxlag, jitter, tol, fsamp):
    print("Removing duplicates")

    jit = round(jitter * fsamp)

    # Generate binary spike trains
    firings = np.zeros_like(PulseT)
    distimmp = []

    for i in range(PulseT.shape[0]):
        firings[i, distime2[i]] = 1
        tmp_times = []

        for j in range(1, jit + 1):
            tmp_times.extend(distime2[i] - j)
            tmp_times.extend(distime2[i] + j)

        tmp_times.extend(distime2[i])
        distimmp.append(np.array(tmp_times))

    MUn = len(distime2)

    i = 0
    Pulsenew = np.zeros((0, PulseT.shape[1]))
    distimenew = []

    # Remove duplicates
    while len(distimmp) > 0:
        # Remove lag that may exist between MUs
        distimetemp = [None] * len(distimmp)

        for j in range(len(distimmp)):
            c = correlate(firings[0, :], firings[j, :], mode="same", method="direct")
            c = c / np.sqrt(np.sum(firings[0, :] ** 2) * np.sum(firings[j, :] ** 2))  # Normalization

            lags = np.arange(-maxlag * 2, maxlag * 2 + 1)
            correl = np.max(c)
            idx = np.argmax(c)

            if correl > 0.2:
                distimetemp[j] = distimmp[j] + lags[idx]
            else:
                distimetemp[j] = distimmp[j]

        # Find common discharge times
        comdis = np.zeros(len(distimmp))

        for j in range(1, len(distimmp)):
            com = np.intersect1d(distimmp[0], distimetemp[j])  # type: ignore
            # Remove consecutive entries
            com = com[np.concatenate(([False], np.diff(com) != 1))]
            comdis[j] = len(com) / max(len(distime[0]), len(distime[j]))

        # Flag duplicates and keep the MU with the lowest CoV of ISI
        duplicates = np.where(comdis >= tol)[0]
        duplicates = np.concatenate(([0], duplicates))
        CoV = np.zeros(len(duplicates))

        for j in range(len(duplicates)):
            ISI = np.diff(distime[duplicates[j]])
            CoV[j] = np.std(ISI) / np.mean(ISI)

        survivor = np.argmin(CoV)

        # Delete duplicates and save the surviving MU
        distimenew.append(distime[duplicates[survivor]])
        Pulsenew = np.vstack((Pulsenew, PulseT[duplicates[survivor], :].reshape(1, -1)))

        # Update firings and discharge times
        duplicates = sorted(duplicates, reverse=True)
        for j in range(len(duplicates)):
            del distimmp[duplicates[j]]
            del distime[duplicates[j]]
            del distime2[duplicates[j]]

        firings = np.delete(firings, duplicates, axis=0)
        PulseT = np.delete(PulseT, duplicates, axis=0)

        print(f"{len(distime)} remaining MUs to check")
        i += 1

    return Pulsenew, distimenew
