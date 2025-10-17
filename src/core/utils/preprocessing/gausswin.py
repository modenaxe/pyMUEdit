import numpy as np


def gausswin(M, alpha=2.5):
    """
    Creates a Gaussian window of length M.

    Python equivalent of MATLAB's gausswin function, used for windowing
    signals in motor unit extraction.
    """

    n = np.arange(-(M - 1) / 2, (M - 1) / 2 + 1, dtype="complex128")
    w = np.exp((-1 / 2) * (alpha * n / ((M - 1) / 2)) ** 2)
    return w
