import numpy as np
from core.utils.decomposition.xcorr import xcorr


def remove_duplicates_between_arrays(pulse_trains, discharge_times, muscle, maxlag, jitter_val, tol, fsamp):
    """
    Identifies and removes duplicate motor units across different electrode arrays.

    Similar to remove_duplicates, but specifically handles detection of the same
    motor unit appearing in multiple electrode arrays.
    """

    jitter_thr = int(np.round(jitter_val * fsamp))
    spike_trains = np.zeros([np.shape(pulse_trains)[0], np.shape(pulse_trains)[1]])

    discharge_jits = []
    discharge_times_new = []
    pulse_trains_new = []
    muscle_new = []

    # generating binary spike trains for each MU extracted so far
    for i in range(np.shape(pulse_trains)[0]):
        spike_trains[i, discharge_times[i]] = 1
        discharge_jits.append([])

        # Convert NumPy arrays to lists before using extend()
        for j in range(jitter_thr):
            discharge_jits[i].extend((discharge_times[i] - j).tolist())
            discharge_jits[i].extend((discharge_times[i] + j).tolist())

        discharge_jits[i].extend(discharge_times[i].tolist())

    i = 1
    while discharge_jits:
        discharge_temp = []
        for mu_candidate in range(len(discharge_jits)):
            corr, lags = xcorr(spike_trains[0, :], spike_trains[mu_candidate, :], int(maxlag))
            ind_max = np.argmax(corr)
            corr_max = np.real(corr[ind_max])

            if corr_max > 0.2:
                discharge_temp.append([x + lags[ind_max] for x in discharge_jits[mu_candidate]])
            else:
                discharge_temp.append(discharge_jits[mu_candidate])

        # Now, we count the common discharge times
        comdis = np.zeros(np.shape(pulse_trains)[0])

        for j in range(1, np.shape(pulse_trains)[0]):
            com = np.intersect1d(discharge_jits[0], discharge_temp[j])

            if com.size > 1:
                # Find indices where diff != 1, but handle empty arrays
                diff_mask = np.diff(com) != 1
                keep_indices = np.insert(diff_mask, 0, False)
                com = com[keep_indices]
            elif com.size == 0:
                pass

            # Calculate common discharge ratio
            if len(discharge_times[0]) > 0 and len(discharge_times[j]) > 0:
                comdis[j] = len(com) / max(len(discharge_times[0]), len(discharge_times[j]))
            else:
                comdis[j] = 0

            # Clear com to free memory
            com = None

        duplicates = np.where(comdis >= tol)[0]
        duplicates = np.insert(duplicates, 0, 0)
        CoV = np.zeros(len(duplicates))

        for j in range(len(duplicates)):
            ISI = np.diff(discharge_times[duplicates[j]])
            if ISI.size > 0:
                CoV[j] = np.std(ISI) / np.mean(ISI)
            else:
                CoV[j] = float("inf")  # Set high CoV for empty arrays

        survivor = np.argmin(CoV)

        # delete all duplicates, but save the surviving MU
        discharge_times_new.append(discharge_times[duplicates[survivor]])
        pulse_trains_new.append(pulse_trains[duplicates[survivor]])
        muscle_new.append(muscle[duplicates[survivor]])

        # update firings and discharge times
        for j in range(len(duplicates)):
            discharge_times[duplicates[-(j + 1)]] = np.array([])
            discharge_jits[duplicates[-(j + 1)]] = []

        discharge_times = [mu for mu in discharge_times if mu.size > 0]
        discharge_jits = [mu for mu in discharge_jits if len(mu) > 0]

        # Clean the spike and pulse train arrays
        spike_trains = np.delete(spike_trains, duplicates, axis=0)
        pulse_trains = np.delete(pulse_trains, duplicates, axis=0)
        muscle = np.delete(muscle, duplicates, axis=0)

        i += 1

    muscle_new = np.array(muscle_new)
    pulse_trains_new = np.array(pulse_trains_new)
    return discharge_times_new, pulse_trains_new, muscle_new
