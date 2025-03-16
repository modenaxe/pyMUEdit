import numpy as np
from scipy.signal import convolve
from lib.cutMUAP import cutMUAP


def peeloff(X, spikes, fsamp, win):
    windowl = round(win * fsamp)
    waveform = np.zeros(windowl * 2 + 1)
    firings = np.zeros(X.shape[1])
    firings[spikes] = 1
    EMGtemp = np.zeros_like(X)

    for l in range(X.shape[0]):
        temp = cutMUAP(spikes, windowl, X[l, :])
        waveform = np.mean(temp, axis=0)
        EMGtemp[l, :] = convolve(firings, waveform, mode="same")

    X = X - EMGtemp

    return X
