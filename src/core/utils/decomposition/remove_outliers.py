import numpy as np


def remove_outliers(pulse_trains, discharge_times, fsamp, threshold=0.4, max_its=30):
    """
    Removes outlier discharge times that would create unrealistic firing rates.

    Identifies and eliminates motor unit discharges that would lead to
    physiologically implausible discharge rates, improving the reliability
    of the identified motor unit.
    """

    for mu in range(len(discharge_times)):
        discharge_rates = 1 / (np.diff(discharge_times[mu]) / fsamp)
        it = 1
        while (np.std(discharge_rates) / np.mean(discharge_rates)) > threshold and it < max_its:
            artifact_limit = np.mean(discharge_rates) + 3 * np.std(discharge_rates)

            # identify the indices for which this limit is exceeded
            artifact_inds = np.argwhere(discharge_rates > artifact_limit).flatten()

            if artifact_inds.size > 0:
                # vectorising the comparisons between the numerator terms used to calculate the rate, for indices at rate artifacts
                diff_artifact_comp = (
                    pulse_trains[mu][discharge_times[mu][artifact_inds]]
                    < pulse_trains[mu][discharge_times[mu][artifact_inds + 1]]
                )

                # 0 means discharge_times[mu][artifact_inds]] was less, 1 means discharge_times[mu][artifact_inds + 1]] was more
                less_or_more = np.argmax([diff_artifact_comp, ~diff_artifact_comp], axis=0)
                discharge_times[mu] = np.delete(discharge_times[mu], artifact_inds + less_or_more)

            discharge_rates = 1 / (np.diff(discharge_times[mu]) / fsamp)
            it += 1

    return discharge_times
