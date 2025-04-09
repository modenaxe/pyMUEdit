import numpy as np
from scipy import fft
import multiprocessing
from functools import partial


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
    bandwidth_as_index = int(round(4 * (signal_length / fsamp)))
    half_bandwidth = bandwidth_as_index // 2
    window_size = int(fsamp)

    # Compute FFT
    fourier_signal = fft.fft(channel_data)
    fourier_interf = np.zeros(signal_length, dtype=complex)

    # Process in windows with vectorized operations
    for interval in range(0, signal_length - window_size + 1, window_size):
        window_start = interval + 1
        window_end = min(interval + window_size + 1, signal_length)

        # Skip empty windows
        if window_end <= window_start:
            continue

        # Get window segment
        window_segment = np.abs(fourier_signal[window_start:window_end])  # type:ignore

        # Calculate statistics
        median_freq = np.median(window_segment)
        std_freq = np.std(window_segment)
        threshold = median_freq + 5 * std_freq

        # Find interference indices (vectorized)
        interference_indices = np.where(window_segment > threshold)[0] + window_start

        # Apply bandwidth around each interference
        for idx in interference_indices:
            start_idx = max(0, idx - half_bandwidth)
            end_idx = min(signal_length, idx + half_bandwidth + 1)
            fourier_interf[start_idx:end_idx] = fourier_signal[start_idx:end_idx]

    # Apply symmetry for real IFFT output
    if np.any(fourier_interf != 0):
        midpoint = signal_length // 2
        # Skip DC component (index 0)
        fourier_interf[signal_length - midpoint + 1 :] = np.conj(fourier_interf[1:midpoint][::-1])

    # Apply IFFT and subtract from original
    inverse_fft = fft.ifft(fourier_interf).real  # type:ignore
    filtered_channel = channel_data - inverse_fft

    return filtered_channel


def notchsignals(signal, fsamp):
    """
    Multiprocessing-based notch filter implementation.

    Args:
        signal: Input EMG signal array (channels × samples)
        fsamp: Sampling frequency in Hz

    Returns:
        filtered_signal: Notch filtered signal
    """

    # Ensure we have a 2D array
    if signal.ndim == 1:
        signal = signal.reshape(1, -1)

    n_channels, signal_length = signal.shape

    # Pre-allocate output array
    filtered_signal = np.zeros_like(signal)

    # Set up multiprocessing
    n_processes = min(multiprocessing.cpu_count(), 8)

    # Create a partial function with fixed fsamp
    process_func = partial(process_channel, fsamp=fsamp)

    # Use multiprocessing Pool
    with multiprocessing.Pool(processes=n_processes) as pool:
        batch_size = max(1, n_channels // 10)

        for batch_start in range(0, n_channels, batch_size):
            batch_end = min(batch_start + batch_size, n_channels)
            batch_indices = range(batch_start, batch_end)

            # Process batch
            results = pool.map(process_func, [signal[i] for i in batch_indices])

            # Store results
            for idx, result in zip(batch_indices, results):
                filtered_signal[idx] = result

    return filtered_signal
