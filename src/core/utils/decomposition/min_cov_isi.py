import numpy as np
from core.utils.decomposition.get_spikes import get_spikes


def min_cov_isi(w_n, B, Z, fsamp, cov_n, spikes_n):
    """
    Minimizes coefficient of variation (CoV) of inter-spike intervals.

    Iteratively refines the separation vector to achieve more regular
    motor unit firing patterns by minimizing the CoV of the interspike
    intervals.
    """

    cov_n_1 = cov_n + 0.1

    while cov_n < cov_n_1:

        cov_n_1 = cov_n.copy()
        spikes_n_1 = spikes_n.copy()

        w_n_1 = w_n.copy()
        _, spikes_n = get_spikes(w_n, Z, fsamp)

        # determine the interspike interval
        ISI = np.diff(spikes_n / fsamp)
        # determine the coefficient of variation
        cov_n = np.std(ISI) / np.mean(ISI)

        # update the sepearation vector by summing all the spikes
        w_n = np.sum(Z[:, spikes_n], axis=1)  # summing the spiking across time, leaving an array that is channels x 1

    if len(spikes_n_1) < 2:
        _, spikes_n_1 = get_spikes(w_n, Z, fsamp)

    return w_n_1, spikes_n_1, cov_n_1
