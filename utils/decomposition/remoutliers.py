import numpy as np


def remoutliers(pulseT, distime, thresh, fsamp):
    """
    Remove outliers from motor unit discharge patterns.

    Args:
        pulseT: Motor unit pulse trains
        distime: List of discharge times for each motor unit
        thresh: Threshold for CoV of discharge rates
        fsamp: Sampling frequency

    Returns:
        Filtered discharge times
    """
    distime_copy = []
    for dt in distime:
        if dt is not None and len(dt) > 0:
            distime_copy.append(dt.copy())
        else:
            distime_copy.append(np.array([], dtype=int))

    for nMU in range(len(distime_copy)):

        if distime_copy[nMU] is None or len(distime_copy[nMU]) <= 1:
            continue

        try:
            # Calculate discharge rates
            DR = 1.0 / (np.diff(distime_copy[nMU]) / fsamp)

            # Handle invalid values
            DR = DR[np.isfinite(DR)]
            if len(DR) == 0:
                print(f"  Warning: No valid discharge rates for MU {nMU+1}")
                continue

            # Iteratively remove outliers
            k = 1
            cov = np.nanstd(DR) / np.nanmean(DR) if np.nanmean(DR) > 0 else float("inf")

            while cov > thresh and k < 30 and len(DR) > 1:
                k += 1

                # Find threshold for outliers
                thres = np.nanmean(DR) + 3 * np.nanstd(DR)
                idx = np.where(DR > thres)[0]
                print(f"  Found {len(idx)} outliers above threshold {thres:.2f}")

                if len(idx) > 0:
                    # Decide which spike to remove based on pulse amplitude
                    idxdel = []
                    for i in range(len(idx)):
                        # Compare pulse amplitude at consecutive spikes
                        if idx[i] + 1 < len(distime_copy[nMU]) and idx[i] < len(DR):
                            try:
                                # Access pulseT safely
                                if isinstance(pulseT, np.ndarray) and nMU < pulseT.shape[0]:
                                    if distime_copy[nMU][idx[i]] < len(pulseT[nMU]) and distime_copy[nMU][
                                        idx[i] + 1
                                    ] < len(pulseT[nMU]):
                                        if (
                                            pulseT[nMU, distime_copy[nMU][idx[i]]]
                                            < pulseT[nMU, distime_copy[nMU][idx[i] + 1]]
                                        ):
                                            idxdel.append(idx[i])
                                        else:
                                            if idx[i] + 1 < len(distime_copy[nMU]):
                                                idxdel.append(idx[i] + 1)
                                else:
                                    idxdel.append(idx[i])
                            except Exception as e:
                                print(f"  Error comparing pulses: {e}")
                                idxdel.append(idx[i])

                    # Remove the identified outliers
                    if idxdel:
                        print(f"  Removing {len(idxdel)} spikes")
                        distime_copy[nMU] = np.delete(distime_copy[nMU], idxdel)
                    else:
                        print(f"  No spikes to remove")
                        break

                # Recalculate discharge rates if more than one spike remains
                if len(distime_copy[nMU]) > 1:
                    DR = 1.0 / (np.diff(distime_copy[nMU]) / fsamp)
                    DR = DR[np.isfinite(DR)]
                    if len(DR) > 0:
                        cov = np.nanstd(DR) / np.nanmean(DR) if np.nanmean(DR) > 0 else float("inf")
                    else:
                        break
                else:
                    break

        except Exception as e:
            print(f"  Error processing MU {nMU+1}: {e}")

    return distime_copy
