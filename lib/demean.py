import numpy as np


def demean(signals):
    values = np.mean(signals, axis=1, keepdims=True)
    demsignals = signals - values
    return demsignals
