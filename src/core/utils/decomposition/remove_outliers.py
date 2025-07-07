import numpy as np

def remove_outliers(pulse_trains, discharge_times, fsamp, mu_names=None):
    """
    Remove outlier discharges: for each spike pair with high discharge rate,
    remove the spike with lower amplitude. Logic follows MATLAB implementation.
    Only a single pass is applied, no iteration.
    """
    removal_summary = {}
    for mu in range(len(discharge_times)):
        # Discharge rate between consecutive spikes
        drates = 1 / (np.diff(discharge_times[mu]) / fsamp)
        drates = np.array(drates).flatten()
        mean_dr = np.mean(drates)
        std_dr = np.std(drates, ddof=1)
        threshold = mean_dr + 3 * std_dr

        # Indices where DR exceeds threshold
        artifact_inds = np.where(drates > threshold)[0]

        del_indices = []

        for i in artifact_inds:
            t1 = discharge_times[mu][i]
            t2 = discharge_times[mu][i + 1]

            amp1 = pulse_trains[mu][t1]
            amp2 = pulse_trains[mu][t2]

            if amp1 < amp2:
                del_indices.append(i)
            else:
                del_indices.append(i + 1)

        # Remove duplicates & sort
        del_indices = sorted(set(del_indices))

        # Ensure not out of bounds
        del_indices = [idx for idx in del_indices if idx < len(discharge_times[mu])]

        # Perform deletion
        discharge_times[mu] = np.delete(discharge_times[mu], del_indices)
        # Identify MU name (fallback to MU_{index} if no name provided)
        mu_name = mu_names[mu] if mu_names and mu < len(mu_names) else f"MU_{mu}"
        removal_summary[mu_name] = len(del_indices)

    return discharge_times, removal_summary