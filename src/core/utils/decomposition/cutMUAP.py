import numpy as np
from core.utils.decomposition.gausswin import gausswin


def cutMUAP(MUPulses, length, Y):
    """
    Extracts motor unit action potential waveforms from a signal.

    Cuts out signal segments centered around identified spike locations
    to create a collection of aligned motor unit action potentials.

    Args:
        MUPulses: Trigger positions (in samples) for rectangular window
        length: Radius of rectangular window (window length = 2*len +1)
        Y: Single signal channel containing recorded signals

    Returns:
        MUAPs: Matrix of extracted MUAPs (aligned signal intervals)
    """

    while len(MUPulses) > 0 and MUPulses[-1] + 2 * length > len(Y):
        MUPulses = MUPulses[:-1]

    c = len(MUPulses)
    edge_len = round(length / 2)
    tmp = gausswin(2 * edge_len)  # gives the same output as the in-built gausswin function in MATLAB

    # create the filtering window
    win = np.ones(2 * length + 1)
    win[:edge_len] = tmp[:edge_len]
    win[-edge_len:] = tmp[edge_len:]
    MUAPs = np.empty((c, 1 + 2 * length))
    for k in range(c):
        start = max(MUPulses[k] - length, 1) - (MUPulses[k] - length)
        end = MUPulses[k] + length - min(MUPulses[k] + length, len(Y))
        MUAPs[k, :] = win * np.concatenate(
            (np.zeros(start), Y[max(MUPulses[k] - length, 1) : min(MUPulses[k] + length, len(Y)) + 1], np.zeros(end))
        )

    return MUAPs
