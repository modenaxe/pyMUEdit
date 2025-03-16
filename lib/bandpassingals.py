from scipy import signal


def bandpassingals(input_signal, fsamp, emgtype):
    if emgtype == 1:
        b, a = signal.butter(2, [20, 500], btype="bandpass", fs=fsamp)  # type: ignore
        filtered_signal = signal.filtfilt(b, a, input_signal.T).T
    else:
        b, a = signal.butter(3, [100, 4400], btype="bandpass", fs=fsamp)  # type: ignore
        filtered_signal = signal.filtfilt(b, a, input_signal.T).T

    return filtered_signal
