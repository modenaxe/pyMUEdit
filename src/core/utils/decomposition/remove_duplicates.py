import numpy as np
from core.utils.decomposition.xcorr import xcorr


def remove_duplicates(pulse_trains, discharge_times, discharge_times2, mu_filters, maxlag, jitter_val, tol, fsamp):
    """
    Identifies and removes duplicate motor units.

    Uses cross-correlation to detect motor units that likely represent the same physical unit,
    keeping only the one with the most regular firing pattern (lowest CoV).
    """

    jitter_thr = int(np.round(jitter_val * fsamp))
    spike_trains = np.zeros([np.shape(pulse_trains)[0], np.shape(pulse_trains)[1]])

    discharge_jits = []
    discharge_times_new = []
    pulse_trains_new = []

    # generating binary spike trains for each MU extracted so far
    for i in range(np.shape(pulse_trains)[0]):
        spike_trains[i, discharge_times[i]] = 1
        discharge_jits.append([])  # append an empty list to be extended with jitters

        # adding jitter
        for j in range(jitter_thr):
            discharge_jits[i].extend((discharge_times2[i] - j).tolist())
            discharge_jits[i].extend((discharge_times2[i] + j).tolist())

        discharge_jits[i].extend(discharge_times2[i].tolist())

    # With the binary trains generated above, you can readily identify duplicate MUs
    i = 1
    while discharge_jits:
        discharge_temp = []
        for mu_candidate in range(len(discharge_jits)):

            # calculating the cross correlation between the firings of two candidate MUs
            corr, lags = xcorr(spike_trains[0, :], spike_trains[mu_candidate, :], int(maxlag))
            ind_max = np.argmax(corr)
            corr_max = np.real(corr[ind_max])

            if corr_max > 0.2:
                discharge_temp.append([x + lags[ind_max] for x in discharge_jits[mu_candidate]])
            else:
                discharge_temp.append(discharge_jits[mu_candidate])

        # Now, we count the common discharge times
        comdis = np.zeros(np.shape(pulse_trains)[0])

        for j in range(1, np.shape(pulse_trains)[0]):  # skip the first since it is used for the baseline comparison
            com = np.intersect1d(discharge_jits[0], discharge_temp[j])
            com = com[np.insert(np.diff(com) != 1, 0, False)]
            comdis[j] = len(com) / max(len(discharge_times[0]), len(discharge_times[j]))
            com = None

        # use this establish the duplicate MUs, and keep only the MU that has the most stable, regular firing behaviour
        duplicates = np.where(comdis >= tol)[0]
        duplicates = np.insert(duplicates, 0, 0)
        CoV = np.zeros(len(duplicates))

        for j in range(len(duplicates)):
            ISI = np.diff(discharge_times[duplicates[j]])
            CoV[j] = np.std(ISI) / np.mean(ISI)

        survivor = np.argmin(CoV)  # the surviving MU has the lowest CoV

        # delete all duplicates, but save the surviving MU
        discharge_times_new.append(discharge_times[duplicates[survivor]])
        pulse_trains_new.append(pulse_trains[duplicates[survivor]])

        # update firings and discharge times
        for j in range(len(duplicates)):
            # THE FIX IS HERE: Use np.array([]) to maintain NumPy array consistency
            discharge_times[duplicates[-(j + 1)]] = np.array([])
            discharge_times2[duplicates[-(j + 1)]] = np.array([])
            discharge_jits[duplicates[-(j + 1)]] = []

        # if it is not empty, assign it back to the list, otherwise remove the empty element
        discharge_times = [mu for mu in discharge_times if mu.size > 0]
        discharge_times2 = [mu for mu in discharge_times2 if mu.size > 0]
        discharge_jits = [mu for mu in discharge_jits if len(mu) > 0]

        # Clean the spike and pulse train arrays based on identified duplicates
        spike_trains = np.delete(spike_trains, duplicates, axis=0)
        pulse_trains = np.delete(pulse_trains, duplicates, axis=0)
        mu_filters = np.delete(mu_filters, duplicates, axis=0)

        i += 1

    return discharge_times_new, pulse_trains_new, mu_filters
