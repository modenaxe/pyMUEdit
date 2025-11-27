from core.logger import logger

def parse_mu_input(raw_text):
    """Parses the MU input text and returns a sorted list of MU numbers.

    Args:
        raw_text (str): The input text containing MU numbers or ranges.

    Returns:
        list: A sorted list of unique MU numbers.

    Raises:
        ValueError: If the input format is invalid.
    """
    # Accepts comma-separated and dash ranges, e.g. '1,3,5-7'
    mus = []
    raw_text = raw_text.strip()
    if not raw_text:
        raise ValueError("Empty input")
    parts = raw_text.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start_end = part.split('-')
            if len(start_end) != 2:
                raise ValueError("Invalid range format")
            start, end = start_end
            start = int(start)
            end = int(end)
            if start > end:
                raise ValueError("Range start must be <= end")
            mus.extend(range(start, end + 1))
        else:
            mus.append(int(part))
    return sorted(set(mus))

def parse_channel_input(raw_text, max_channels=None):
    """Parse a string of channel numbers and ranges into a list of integers."""
    channels = []
    raw_text = raw_text.strip()
    if not raw_text:
        raise ValueError("Empty input")

    parts = raw_text.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start_end = part.split('-')
            if len(start_end) != 2:
                raise ValueError("Invalid range format")
            start, end = start_end
            start = int(start)
            end = int(end)
            if start > end:
                raise ValueError("Range start must be <= end")
            channels.extend(range(start, end + 1))
        else:
            channels.append(int(part))

    channels = sorted(set(channels))

    # Validate channel range if max_channels is provided
    if max_channels is not None:
        invalid_channels = [ch for ch in channels if ch < 0 or ch >= max_channels]
        if invalid_channels:
            raise ValueError(f"Invalid channels: {invalid_channels}. Available channels are 0-{max_channels-1}")

    return channels
