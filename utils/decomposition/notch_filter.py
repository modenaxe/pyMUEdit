import numpy as np
import scipy


def notch_filter(signal, fsamp, to_han=False):
    """
    Implements a notch filter to remove frequency interference.

    Identifies frequency components with magnitudes greater than 5 standard deviations
    away from the median frequency component magnitude and removes them from the signal.
    """

    bandwidth_as_index = int(round(4 * (np.shape(signal)[1] / fsamp)))
    filtered_signal = np.zeros([np.shape(signal)[0], np.shape(signal)[1]])

    for chan in range(np.shape(signal)[0]):

        if to_han:
            hwindow = scipy.signal.hann(np.shape(signal[chan, :])[0])
            final_signal = signal[chan, :] * hwindow
        else:
            final_signal = signal[chan, :]

        fourier_signal = np.fft.fft(final_signal)
        fourier_interf = np.zeros(len(fourier_signal), dtype="complex_")
        interf2remove = np.zeros(len(fourier_signal), dtype=np.int32)
        window = fsamp
        tracker = 0

        for interval in range(0, len(fourier_signal) - window + 1, window):
            median_freq = np.median(abs(fourier_signal[interval + 1 : interval + window + 1]))
            std_freq = np.std(abs(fourier_signal[interval + 1 : interval + window + 1]))
            # interference is defined as when the magnitude of a given frequency component in the fourier spectrum
            # is greater than 5 times the std, relative to the median magnitude
            label_interf = list(
                np.where(abs(fourier_signal[interval + 1 : interval + window + 1]) > median_freq + 5 * std_freq)[0]
            )
            # np.where gives tuple, element access to the array
            # need to shift these labels to make sure they are not relative to the window only, but to the whole signal
            label_interf = [x + interval + 1 for x in label_interf]

            if label_interf:
                for i in range(int(-np.floor(bandwidth_as_index / 2)), int(np.floor(bandwidth_as_index / 2) + 1)):

                    temp_shifted_list = [x + i for x in label_interf]
                    interf2remove[tracker : tracker + len(label_interf)] = temp_shifted_list
                    tracker = tracker + len(label_interf)

        indexf2remove = np.where(np.logical_and(interf2remove >= 0, interf2remove <= len(fourier_signal) / 2))[0]
        fourier_interf[interf2remove[indexf2remove]] = fourier_signal[interf2remove[indexf2remove]]
        corrector = int(len(fourier_signal) - np.floor(len(fourier_signal) / 2) * 2)

        fourier_interf[int(np.ceil(len(fourier_signal) / 2)) :] = np.flip(
            np.conj(fourier_interf[1 : int(np.ceil(len(fourier_signal) / 2) + 1 - corrector)])
        )
        filtered_signal[chan, :] = signal[chan, :] - np.fft.ifft(fourier_interf).real

    return filtered_signal
