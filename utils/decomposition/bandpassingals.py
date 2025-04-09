import numpy as np
import scipy


def bandpassingals(signal, fsamp, emgtype):
    """
    Generic band-pass filter implementation and application to EMG signal.

    Args:
        signal: Input EMG signal array (channels × samples)
        fsamp: Sampling frequency in Hz
        emgtype: Type of EMG signal (1 for surface, 2 for intramuscular)

    Returns:
        filtered_signal: Bandpass filtered signal
    """
    # Set filter parameters based on EMG type
    if emgtype == 1:  # surface EMG
        lowfreq = 20
        highfreq = 500
        order = 2
    else:  # intramuscular EMG
        lowfreq = 100
        highfreq = 4400
        order = 3

    # Get filter coefficients
    nyq = fsamp / 2
    lowcut = lowfreq / nyq
    highcut = highfreq / nyq
    [b, a] = scipy.signal.butter(order, [lowcut, highcut], "bandpass")

    # Initialize output array
    filtered_signal = np.zeros([signal.shape[0], signal.shape[1]])

    # Apply filter to each channel
    for chan in range(signal.shape[0]):
        # Use padlen matching MATLAB's approach for compatibility
        filtered_signal[chan, :] = scipy.signal.filtfilt(
            b, a, signal[chan, :], padtype="odd", padlen=3 * (max(len(b), len(a)) - 1)
        )

    return filtered_signal
