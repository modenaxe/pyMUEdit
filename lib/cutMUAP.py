import numpy as np


def cutMUAP(MUPulses, len_window, Y):
    valid_pulses = MUPulses[(MUPulses >= (1 + 2 * len_window)) & (MUPulses <= len(Y) - 1 - 2 * len_window)]

    MUAPs = np.zeros((len(valid_pulses), 1 + 2 * len_window))

    if len(valid_pulses) > 0:
        for k in range(len(valid_pulses)):
            MUAPs[k, :] = Y[valid_pulses[k] - len_window : valid_pulses[k] + len_window + 1]

    return MUAPs
