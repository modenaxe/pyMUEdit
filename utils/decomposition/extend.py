import numpy as np


def extend(signal, ext_factor):
    """
    Extension of EMG signals to improve numerical stability.

    Args:
        signal: Input EMG signal array (channels × samples)
        ext_factor: Extension factor (number of copies)

    Returns:
        extended_template: Extended signal
    """
    if signal.ndim == 1:
        signal = signal.reshape(1, -1)

    nchans = signal.shape[0]
    nobvs = signal.shape[1]

    # Create output array
    extended_template = np.zeros((nchans * ext_factor, nobvs + ext_factor - 1))

    # Fill with shifted copies of the original signal
    for i in range(ext_factor):
        extended_template[nchans * i : nchans * (i + 1), i : nobvs + i] = signal

    return extended_template
