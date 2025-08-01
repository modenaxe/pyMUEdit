import numpy as np
from scipy import fft


def process_channel(channel_data, fsamp):
    """
    Process a single channel for notch filtering.

    Args:
        channel_data: Signal data for one channel
        fsamp: Sampling frequency

    Returns:
        filtered_channel: Notch filtered channel data
    """
    signal_length = len(channel_data)
    bandwidth_as_index = int(round(4 / (fsamp / signal_length)))
    half_bandwidth = bandwidth_as_index // 2
    window_size = int(fsamp)

    # Compute FFT
    fourier_signal = fft.fft(channel_data)
    fourier_interf = np.zeros(signal_length, dtype=complex)

    # Process in windows with vectorized operations
    for interval in range(0, signal_length - window_size, window_size):
        window_start = interval + 1
        window_end = min(interval + window_size + 1, signal_length)

        # Skip empty windows
        if window_end <= window_start:
            continue

        # Get window segment
        window_segment = np.abs(fourier_signal[window_start:window_end])  # type:ignore

        # Calculate statistics
        median_freq = np.median(window_segment)
        # ddof=1 makes `np.std` behave like matlab's `std`
        std_freq = np.std(window_segment, ddof=1)
        threshold = median_freq + 5 * std_freq

        # Find interference indices (vectorized)
        interference_indices = np.nonzero(window_segment > threshold)[0] + window_start

        # Apply bandwidth around each interference
        for idx in interference_indices:
            start_idx = max(0, idx - half_bandwidth)
            end_idx = min(signal_length, idx + half_bandwidth + 1)
            fourier_interf[start_idx:end_idx] = fourier_signal[start_idx:end_idx]

    # Apply symmetry for real IFFT output
    if np.any(fourier_interf != 0):
        midpoint = signal_length // 2
        # Skip DC component (index 0)
        fourier_interf[signal_length - midpoint + 1 :] = np.conj(
            fourier_interf[1:midpoint][::-1]
        )

    # Apply IFFT and subtract from original
    inverse_fft = fft.ifft(fourier_interf).real  # type:ignore
    filtered_channel = channel_data - inverse_fft

    return filtered_channel


def notch_filter(signal, fsamp):
    """
    Notch filter implementation.

    Args:
        signal: Input EMG signal array (channels × samples)
        fsamp: Sampling frequency in Hz

    Returns:
        filtered_signal: Notch filtered signal
    """

    # Ensure we have a 2D array
    if signal.ndim == 1:
        signal = signal.reshape(1, -1)

    return np.array([process_channel(channel, fsamp) for channel in signal])
