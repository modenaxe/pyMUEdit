import numpy as np


def extend_emg(extended_template, signal, ext_factor):
    """
    Extends EMG signals for improved numerical stability.

    For extension, R-1 versions of the original data are stacked with R-1 timeshifts.
    Structure: [channel1(k), channel2(k),..., channelm(k);
               channel1(k-1), channel2(k-1),...,channelm(k-1);...;
               channel1(k-(R-1)),channel2(k-(R-1)), channelm(k-(R-1))]
    """
    nchans = np.shape(signal)[0]
    nobvs = np.shape(signal)[1]
    for i in range(ext_factor):

        extended_template[nchans * i : nchans * (i + 1), i : nobvs + i] = signal

    return extended_template
