import numpy as np
from utils.decomposition.getspikes import getspikes


def minimizeCOVISI(w_n, X, cov_n, fsamp):
    """
    Minimize the Coefficient of Variation (CoV) of interspike intervals (ISI).

    Args:
        w_n: Initial separation vector
        X: Whitened signal matrix
        cov_n: Initial CoV value
        fsamp: Sampling frequency

    Returns:
        w_n_1: Final separation vector
        spikes_n_1: Final spike indices
        cov_n_1: Final CoV value
    """
    # Ensure w_n has the right shape
    if w_n.ndim == 1:
        w_n = w_n.reshape(-1, 1)

    # Initialize variables
    cov_n_1 = cov_n + 0.1
    spikes_n = np.array([1])

    # Iteratively update until CoV increases
    while cov_n < cov_n_1:
        # Save previous values
        cov_n_1 = cov_n
        spikes_n_1 = spikes_n.copy()
        w_n_1 = w_n.copy()

        # Get new discharge times
        _, spikes_n = getspikes(w_n, X, fsamp)

        # Calculate new CoV if enough spikes
        if len(spikes_n) > 1:
            ISI = np.diff(spikes_n / fsamp)
            cov_n = np.std(ISI) / np.mean(ISI)

            # Update separation vector by summing all spikes
            w_n = np.sum(X[:, spikes_n], axis=1).reshape(-1, 1)

    # If no spikes were found, try one more time
    if len(spikes_n_1) < 2:
        _, spikes_n_1 = getspikes(w_n_1, X, fsamp)

    # Ensure the right output format
    if w_n_1.ndim > 1 and w_n_1.shape[1] == 1:
        w_n_1 = w_n_1.flatten()

    return w_n_1, spikes_n_1, cov_n_1
