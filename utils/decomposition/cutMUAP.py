import numpy as np


def gausswin(M, alpha=2.5):
    """
    Python equivalent of the in-built gausswin function in MATLAB.

    Args:
        M: Window length
        alpha: Reciprocal of the standard deviation

    Returns:
        w: Gaussian window
    """
    n = np.arange(-(M - 1) / 2, (M - 1) / 2 + 1, dtype=np.float64)
    w = np.exp((-1 / 2) * (alpha * n / ((M - 1) / 2)) ** 2)
    return w


def cutMUAP(MUPulses, length, Y):
    """
    Extracts consecutive MUAPs from signal Y and stores them row-wise.

    Args:
        MUPulses: Trigger positions (in samples) for rectangular window
        length: Radius of rectangular window (window length = 2*length+1)
        Y: Single signal channel

    Returns:
        MUAPs: Row-wise matrix of extracted MUAPs
    """
    # Remove pulses that would cause us to go out of bounds
    valid_pulses = []
    for pulse in MUPulses:
        if 0 <= pulse - length and pulse + length < len(Y):
            valid_pulses.append(pulse)

    if not valid_pulses:
        return np.array([])

    valid_pulses = np.array(valid_pulses)

    # Create the windowing function
    edge_len = round(length / 2)
    tmp = gausswin(2 * edge_len)
    win = np.ones(2 * length + 1)
    win[:edge_len] = tmp[:edge_len]
    win[-edge_len:] = tmp[edge_len:]

    # Extract MUAPs
    c = len(valid_pulses)
    MUAPs = np.zeros((c, 1 + 2 * length))

    for k in range(c):
        pulse = valid_pulses[k]

        # Handle edge cases
        start_idx = max(0, pulse - length)
        end_idx = min(len(Y), pulse + length + 1)

        # Calculate padding
        pad_start = max(0, length - pulse)
        pad_end = max(0, pulse + length + 1 - len(Y))

        # Extract and pad signal segment
        segment = Y[start_idx:end_idx]

        if pad_start > 0 or pad_end > 0:
            segment = np.pad(segment, (pad_start, pad_end))

        # Apply window and store
        MUAPs[k, :] = win * segment

    return MUAPs
