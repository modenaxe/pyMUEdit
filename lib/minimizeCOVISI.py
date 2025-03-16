import numpy as np
from lib.getspikes import getspikes


def minimizeCOVISI(w, X, CoV, fsamp):
    k = 1
    CoVlast = CoV + 0.1
    spikes = np.array([1])

    while CoV < CoVlast:
        CoVlast = CoV  # save the last CoV
        spikeslast = spikes  # save the last discharge times
        wlast = w  # save the last MU filter

        # Get discharge times
        _, spikes = getspikes(w, X, fsamp)

        # Calculate interspike interval
        if len(spikes) > 1:
            ISI = np.diff(spikes / fsamp)
            CoV = np.std(ISI) / np.mean(ISI)

            # Update the separation vector
            k = k + 1
            w = np.sum(X[:, spikes], axis=1).reshape(-1, 1)

    if len(spikeslast) < 2:
        _, spikeslast = getspikes(w, X, fsamp)  # save the last discharge times

    return wlast, spikeslast, CoVlast
