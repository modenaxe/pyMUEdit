import numpy as np
import numpy.fft as fft


def notchsignals(signal, fsamp):
    frad = int(np.round(4 / (fsamp / signal.shape[1])))
    filtered_signal = np.zeros_like(signal)

    for i in range(signal.shape[0]):
        filtered_signal[i, :] = np.real(removelineinter(signal[i, :], frad, fsamp))

    return filtered_signal


def removelineinter(signal, frad, fsamp):
    fsignal = fft.fft(signal)
    fcorrec = np.zeros(len(fsignal), dtype=complex)

    window = int(fsamp)
    tstamp = []

    for i in range(0, len(fsignal) - window, window):
        mFreq = np.median(np.abs(fsignal[i + 1 : i + window + 1]))
        sFreq = np.std(np.abs(fsignal[i + 1 : i + window + 1]))

        # Find frequencies above threshold
        tstamp2 = np.where(np.abs(fsignal[i + 1 : i + window + 1]) > mFreq + 5 * sFreq)[0]
        tstamp2 = tstamp2 + i + 1

        # Add surrounding frequencies
        for j in range(-int(np.floor(frad / 2)), int(np.floor(frad / 2)) + 1):
            tstamp.extend(tstamp2 + j)

    if not tstamp:
        return signal

    # Filter valid timestamps
    tstamp = np.array(tstamp)
    tstamp = tstamp[(tstamp > 0) & (tstamp <= len(fsignal) // 2 + 1)]

    if len(tstamp) == 0:
        return signal

    tstamp = np.round(tstamp).astype(int)

    # Create correction signal
    for i in tstamp:
        fcorrec[i] = fsignal[i]

    # Mirror for conjugate symmetry
    half_length = len(fsignal) // 2
    correc = len(fsignal) - np.floor(len(fsignal) / 2) * 2
    mirror_indices = np.arange(len(fsignal) - 1, half_length, -1)
    source_indices = np.arange(1, half_length - int(correc) + 1)

    if len(mirror_indices) > 0 and len(source_indices) > 0:
        min_length = min(len(mirror_indices), len(source_indices))
        mirror_indices = mirror_indices[:min_length]
        source_indices = source_indices[:min_length]
        fcorrec[mirror_indices] = np.conj(fcorrec[source_indices])

    # Subtract the correction from original signal
    filtered_signal = signal - np.real(fft.ifft(fcorrec))

    return filtered_signal
