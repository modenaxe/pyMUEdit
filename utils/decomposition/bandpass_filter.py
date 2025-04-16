import numpy as np
import scipy


def bandpass_filter(signal, fsamp, emg_type="surface"):
    """
    Applies a bandpass filter to EMG signals.

    Filters the signal based on the EMG type (surface or intramuscular)
    with different cutoff frequencies for each type.
    """

    if emg_type == "surface":
        lowfreq = 20
        highfreq = 500
        order = 2
    elif emg_type == "intra":
        lowfreq = 100
        highfreq = 4400
        order = 3

    nyq = fsamp / 2
    lowcut = lowfreq / nyq
    highcut = highfreq / nyq
    [b, a] = scipy.signal.butter(order, [lowcut, highcut], "bandpass")
    # the cut off frequencies should be inputted as normalised angular frequencies

    filtered_signal = np.zeros([np.shape(signal)[0], np.shape(signal)[1]])

    for chan in range(np.shape(signal)[0]):
        filtered_signal[chan, :] = scipy.signal.filtfilt(
            b, a, signal[chan, :], padtype="odd", padlen=3 * (max(len(b), len(a)) - 1)
        )

    return filtered_signal
