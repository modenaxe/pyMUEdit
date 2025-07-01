import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import warnings
import copy

from matplotlib.figure import Figure


def parse_channel_input(raw_text, max_channels=None):
    """
    Parse the channel input string into a list of integers.
    Accepts comma-separated and dash ranges, e.g. '1,3,5-7'.
    Raises ValueError if input is invalid or channels exceed available range.
    
    Parameters:
    -----------
    raw_text : str
        The channel input string to parse
    max_channels : int, optional
        Maximum number of available channels (0-indexed). If provided, validates
        that all requested channels are within range [0, max_channels-1].
    """
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

#OPENHDEMG
def min_max_scaling(data=None, series_or_df=None, col_by_col=False):
    # Create a deepcopy of the original data
    if data is not None:
        data = copy.deepcopy(data)

    elif series_or_df is not None:
        data = copy.deepcopy(series_or_df)

        # Warn for the use of deprecated parameters
        msg = (
            "The 'series_or_df' parameter is deprecated since v0.1.1 and " +
            "will be removed after v0.2.0. Please use 'data' instead."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)

    # Automatically act depending on the data received
    if isinstance(data, pd.Series):
        data = (data - data.min()) / (data.max() - data.min())

        return data

    elif isinstance(data, pd.DataFrame):
        if col_by_col:
            for col in data.columns:
                data[col] = (
                    (data[col] - data[col].min()) /
                    (data[col].max() - data[col].min())
                )

            return data

        else:
            data = (
                (data - data.min().min()) /
                (data.max().max() - data.min().min())
            )

            return data

    elif isinstance(data, np.ndarray):
        if col_by_col:
            # Check if data is 1D 2D or nD and act accordingly
            if len(data.shape) == 1:
                data = (data - data.min()) / (data.max() - data.min())

                return data

            elif len(data.shape) == 2:
                dims = any(d == 0 or d == 1 for d in data.shape)
                if dims:  # Only 1 column
                    data = (data - data.min()) / (data.max() - data.min())
                else:  # Multiple columns
                    for col in range(data.shape[1]):
                        data[:, col] = (
                            (data[:, col] - data[:, col].min()) /
                            (data[:, col].max() - data[:, col].min())
                        )

                return data

            elif len(data.shape) > 2:
                raise ValueError(
                    "col_by_col is supported only for 1 and 2D arrays. Set " +
                    "col_by_col=False to normalise the whole data instead."
                )

        else:
            data = (data - data.min()) / (data.max() - data.min())

            return data

    else:
        raise TypeError(
            "data must be one of pd.series, pd.dataframe or np.ndarray. " +
            f"{type(data)} was passed instead."
        )

#OPENHDEMG
def plot_emgsig(
    emgfile,
    channels,
    manual_offset=0,
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):

    # Load signal
    if isinstance(emgfile["RAW_SIGNAL"], pd.DataFrame):
        emgsig = emgfile["RAW_SIGNAL"]
    else:
        raise TypeError("RAW_SIGNAL is missing or not a DataFrame")

    # Get the number of available channels for validation
    max_channels = len(emgsig.columns)
    
    # If channels is a string, parse it and validate
    if isinstance(channels, str):
        channels = parse_channel_input(channels, max_channels)
    elif isinstance(channels, (list, int)):
        # For direct channel input, validate the range
        if isinstance(channels, list):
            invalid_channels = [ch for ch in channels if ch < 0 or ch >= max_channels]
            if invalid_channels:
                raise ValueError(f"Invalid channels: {invalid_channels}. Available channels are 0-{max_channels-1}")
        else:  # int
            if channels < 0 or channels >= max_channels:
                raise ValueError(f"Invalid channel: {channels}. Available channels are 0-{max_channels-1}")

    if timeinseconds:
        x_axis = emgsig.index / emgfile["FSAMP"]
    else:
        x_axis = emgsig.index

    # Create figure and axes
    fig, ax1 = plt.subplots(figsize=(figsize[0] / 2.54, figsize[1] / 2.54))
    fig.suptitle(f"EMG Channels: {channels}")

    # Default style args
    line2d_kwargs_ax1 = line2d_kwargs_ax1 or {}
    line2d_kwargs_ax2 = line2d_kwargs_ax2 or {}
    axes_kwargs = axes_kwargs or {}

    # Case 1: Single channel
    if isinstance(channels, int):
        ax1.plot(x_axis, emgsig[channels], **line2d_kwargs_ax1)
        ax1.set_ylabel(f"Ch {channels}")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    # Case 2: Multiple channels, no offset
    elif isinstance(channels, list) and manual_offset == 0:
        norm_raw_all = min_max_scaling(emgsig[channels], col_by_col=False)
        for count, ch in enumerate(channels):
            norm_raw = norm_raw_all[ch] + (0.5 - norm_raw_all[ch].mean()) + count
            ax1.plot(x_axis, norm_raw, **line2d_kwargs_ax1)

        ax1.set_yticks(np.arange(0.5, len(channels) + 0.5, 1))
        ax1.set_yticklabels([str(x) for x in channels])
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    # Case 3: Multiple channels with manual offset
    elif isinstance(channels, list) and manual_offset > 0:
        half_offset = manual_offset / 2
        for count, ch in enumerate(channels):
            data = emgsig[ch] + half_offset + manual_offset * count
            ax1.plot(x_axis, data, **line2d_kwargs_ax1)

        ax1.set_yticks(
            np.linspace(
                start=half_offset,
                stop=half_offset + manual_offset * (len(channels) - 1),
                num=len(channels),
            )
        )
        ax1.set_yticklabels([str(x) for x in channels])
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(channels, list) and manual_offset < 0:
        raise ValueError("manual_offset must be >= 0")

    else:
        raise TypeError("channels must be an int or list of ints")

    # Case 4: Add reference signal if requested
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError("REF_SIGNAL is missing or not a DataFrame")
        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0], **line2d_kwargs_ax2)
        ax2.set_ylabel("MVC")
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Apply any axis-level customizations
    for key, val in axes_kwargs.items():
        getattr(ax1, f"set_{key}")(val)

    if tight_layout:
        plt.tight_layout()

    if showimmediately:
        plt.show()
        
    return fig