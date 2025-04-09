import numpy as np
from scipy.signal import convolve
from utils.decomposition.cutMUAP import cutMUAP


def peeloff(Z, spikes, fsamp, win=0.025):
    """
    Peels off detected motor unit action potentials from the signal.

    Args:
        Z: Whitened signal matrix
        spikes: Indices of detected spikes
        fsamp: Sampling frequency
        win: Window duration in seconds for detecting action potentials

    Returns:
        Z: Signal with motor unit contribution removed
    """
    windowl = round(win * fsamp)
    waveform = np.zeros(windowl * 2 + 1)
    firings = np.zeros(Z.shape[1])
    firings[spikes] = 1  # Create binary spike train
    EMGtemp = np.zeros_like(Z)

    # For each channel, cut out MUAPs, calculate average waveform, and convolve
    for l in range(Z.shape[0]):
        temp = cutMUAP(spikes, windowl, Z[l, :])
        if len(temp) > 0:  # Only if we have some MUAPs
            waveform = np.mean(temp, axis=0)
            EMGtemp[l, :] = convolve(firings, waveform, mode="same", method="fft")

    # Remove motor unit contribution
    Z = Z - EMGtemp

    return Z
