import numpy as np


def xcorr(x, y, max_lag=None):
    """
    Computes the cross-correlation between two signals.

    Used to identify similarities between two signals with potential time lag,
    which is useful for detecting duplicate motor units.
    """

    # asssume no lag limitation unless specificied
    fft_size = 2 ** (len(x) + len(y) - 1).bit_length()
    xcorrvalues = np.fft.ifft(np.fft.fft(x, fft_size) * np.conj(np.fft.fft(y, fft_size)))
    xcorrvalues = np.fft.fftshift(xcorrvalues)

    if max_lag is not None:
        max_lag = min(max_lag, len(xcorrvalues) // 2)
        lags = np.arange(-max_lag, max_lag + 1)
        xcorrvalues = xcorrvalues[len(xcorrvalues) // 2 - max_lag : len(xcorrvalues) // 2 + max_lag + 1]
    else:
        lags = np.arange(-(len(xcorrvalues) // 2), len(xcorrvalues) // 2 + 1)

    xcorrvalues /= np.max(xcorrvalues)

    return xcorrvalues, lags
