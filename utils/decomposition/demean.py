import numpy as np
from scipy import signal


def demean(signals):
    """
    Removes the mean from each channel of the input signal.

    Args:
        signals: Input EMG signal array (channels × samples)

    Returns:
        demsignals: Signal with mean removed
    """
    if signals.ndim > 1:
        demsignals = signal.detrend(signals, axis=1, type="constant", bp=0)
    else:
        demsignals = signal.detrend(signals, type="constant", bp=0)

    return demsignals
