import numpy as np
import scipy
from core.utils.decomposition.cutMUAP import cutMUAP


def peel_off(Z, spikes, fsamp):
    """
    Removes the contribution of identified motor units from the signal.

    This prevents the algorithm from extracting the same motor unit multiple times,
    by subtracting the estimated waveform of identified motor units from the signal.
    """

    windowl = round(0.05 * fsamp)
    waveform = np.zeros([windowl * 2 + 1])
    firings = np.zeros([np.shape(Z)[1]])
    firings[spikes] = 1  # make the firings binary
    EMGtemp = np.empty(Z.shape)  # intialise a temporary EMG signal

    for i in range(np.shape(Z)[0]):  # iterating through the (extended) channels
        temp = cutMUAP(spikes, windowl, Z[i, :])
        waveform = np.mean(temp, axis=0)
        EMGtemp[i, :] = scipy.signal.convolve(firings, waveform, mode="same", method="auto")

    Z -= EMGtemp
    return Z
