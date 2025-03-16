import numpy as np


def remoutliers(pulseT, distime, thresh, fsamp):
    for nMU in range(len(distime)):
        if len(distime[nMU]) > 1:
            DR = 1.0 / (np.diff(distime[nMU]) / fsamp)

            # Iteration on CoV of discharge rates
            k = 1
            while (np.std(DR) / np.mean(DR)) > thresh and k < 30:
                k += 1
                thres = np.mean(DR) + 3 * np.std(DR)
                idx = np.where(DR > thres)[0]

                if len(idx) > 0:
                    idxdel = []
                    for i in range(len(idx)):
                        if pulseT[nMU, distime[nMU][idx[i]]] < pulseT[nMU, distime[nMU][(idx[i] + 1)]]:
                            idxdel.append(idx[i])
                        else:
                            idxdel.append(idx[i] + 1)

                    distime[nMU] = np.delete(distime[nMU], idxdel)

                # Recalculate discharge rates
                if len(distime[nMU]) > 1:
                    DR = 1.0 / (np.diff(distime[nMU]) / fsamp)
                else:
                    break

    return distime
