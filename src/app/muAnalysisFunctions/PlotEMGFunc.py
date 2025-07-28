import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import warnings
import copy

from matplotlib.figure import Figure
from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
from ui.components.SaveablePlot import SaveablePlot


def parse_channel_input(raw_text, max_channels=None):
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
def plot_emgsig(
    emgfile,
    analysis_plot,
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
        common = CommonOpenFunc()
        norm_raw_all = common.min_max_scaling(emgsig[channels], col_by_col=False)
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
    
    # TL : function now plots it and doesn't return a figure, similar to plot_idr and plog_refsig in MUAnalysisFunc
    canvas = SaveablePlot(fig)
    analysis_plot.display_plot(canvas)

#OPENHDEMG
def plot_idr(
    emgfile,
    munumber="all",
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=False,
):
    common = CommonOpenFunc()
    idr = common.compute_idr(emgfile=emgfile)
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]
    if isinstance(munumber, list) and len(munumber) == 1:
        munumber = munumber[0]
    figname = "IDR"
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num=figname,
    )
    if isinstance(munumber, int):
        ax1.plot(
            idr[munumber]["timesec" if timeinseconds else "mupulses"],
            idr[munumber]["idr"],
            ".", markersize=12,
        )
        ax1.set_ylabel(f"MU {munumber} (pps)")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
    elif isinstance(munumber, list):
        idr_all = pd.DataFrame({key: df['idr'] for key, df in idr.items()})
        idr_all = idr_all[munumber]
        common = CommonOpenFunc()
        norm_idr_all = common.min_max_scaling(data=idr_all, col_by_col=False)
        for count, thisMU in enumerate(munumber):
            norm_idr = norm_idr_all[thisMU]
            if norm_idr.mean() <= 0.5:
                norm_idr = norm_idr + (0.5 - norm_idr.mean()) + count
            else:
                norm_idr = norm_idr - (norm_idr.mean() - 0.5) + count
            ax1.plot(
                idr[thisMU]["timesec" if timeinseconds else "mupulses"][1:],
                norm_idr.dropna(),
                ".", markersize=8,
            )
        ax1.set_yticks(np.arange(0.5, len(munumber) + 0.5, 1))
        ax1.set_yticklabels([str(mu) for mu in munumber])
        ax1.set_ylabel("Motor units")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
    else:
        raise TypeError(
            "While calling the plot_idr function, you should pass an " +
            "integer, a list or 'all' to munumber"
        )
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )
        x_axis = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )
        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)
    if tight_layout:
        plt.tight_layout()
    if showimmediately:
        plt.show()
    return fig


#OPENHDEMG
def plot_mupulses(
    emgfile,
    munumber="all",
    linewidths=0,
    linelengths=0.9,
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    common = CommonOpenFunc()
    # Warn for the use of a deprecated parameter
    if linewidths > 0:
        msg = (
            "The linewidths parameter is deprecated since v0.1.1 and will " +
            "be removed after v0.2.0. Please use line2d_kwargs_ax1 instead. " +
            "See examples in the plot_mupulses documentation."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)

    # Check to have the correct input
    if isinstance(emgfile["MUPULSES"], list):
        mupulses = emgfile["MUPULSES"]
    else:
        raise TypeError(
            "MUPULSES is probably absent or it is not contained in a np.array"
        )

    # Check linelengths value
    if linelengths < 0 or linelengths > 1:
        raise ValueError(
            "linelengths must be a number between 0 and 1."
        )

    # Check if all the MUs have to be plotted and create the y labels
    if isinstance(munumber, str):
        # Manage exception of single MU
        if emgfile["NUMBER_OF_MUS"] > 1:
            y_tick_lab = [*range(0, emgfile["NUMBER_OF_MUS"])]
            ylab = "Motor units"
            munumber = [*range(emgfile["NUMBER_OF_MUS"])]
        else:
            munumber = 0

    if isinstance(munumber, int):
        mupulses = [mupulses[munumber]]
        y_tick_lab = []
        ylab = f"MU n. {munumber}"
    elif isinstance(munumber, list):
        if len(munumber) > 1:
            mupulses = [mupulses[mu] for mu in munumber]
            y_tick_lab = munumber
            ylab = "Motor units"
        else:
            mupulses = [mupulses[munumber[0]]]
            y_tick_lab = []
            ylab = f"MU n. {munumber[0]}"
    else:
        raise TypeError(
            "While calling the plot_mupulses function, you should pass an " +
            "integer, a list or 'all' to munumber"
        )

    # Convert x axes in seconds if timeinseconds==True.
    # This has to be done both for the REF_SIGNAL and the mupulses, for the
    # MUPULSES we need to convert the point of firing from samples to seconds.
    if timeinseconds:
        mupulses = [n / emgfile["FSAMP"] for n in mupulses]
        x_axis = emgfile["RAW_SIGNAL"].index / emgfile["FSAMP"]
    else:
        x_axis = emgfile["RAW_SIGNAL"].index

    # Create colors list for the firings and plot them
    colors1 = ["C{}".format(i) for i in range(len(mupulses))]

    # Use the subplot to allow the use of twinx
    figname = ("MUs pulses")
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num=figname,
    )

    # Plot the MUPULSES.
    # Iterate over each row and plot events manually to allow the use of
    # the Figure_Layout_Manager.
    for i, (events, color) in enumerate(zip(mupulses, colors1)):
        # The `y` position for this row (increasing by 1 for each new row)
        delta = (1-linelengths) / 2
        y_pos = i
        # Draw each event as a vertical line
        for event in events:
            ax1.plot(
                [event, event],
                [y_pos + delta, y_pos + delta + linelengths],
                color=color, linewidth=linewidths,
                **(line2d_kwargs_ax1 or {})
            )

    # Ensure correct and complete ticks on the left y axis
    ax1.set_yticks(np.arange(0.5, len(mupulses) + 0.5, 1))
    ax1.set_yticklabels([str(mu) for mu in y_tick_lab])
    # Set axes labels
    ax1.set_ylabel(ylab)
    ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )
        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Set tight layout if requested
    if tight_layout:
        plt.tight_layout()

    if showimmediately:
        plt.show()

    return fig

# OPENHDEMG
# plots the source? not entirely sure yet
def plot_ipts(
    emgfile,
    munumber="all",
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    common = CommonOpenFunc()
    # Check if all the MUs have to be plotted
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Check if we have a single mu or a list of mus to plot
    if isinstance(munumber, list) and len(munumber) == 1:
        munumber = munumber[0]

    # Check to have the IPTS in a pandas dataframe
    if isinstance(emgfile["IPTS"], pd.DataFrame):
        ipts = emgfile["IPTS"]
    else:
        raise TypeError(
            "IPTS is probably absent or it is not contained in a dataframe"
        )

    # Here we produce an x axis in seconds or samples
    if timeinseconds:
        x_axis = ipts.index / emgfile["FSAMP"]
    else:
        x_axis = ipts.index

    # Use the subplot function to allow for the use of twinx()
    figname = "IPTS"
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num=figname,
    )

    # Check if we have a single MU or a list of MUs to plot
    if isinstance(munumber, int):
        ax1.plot(x_axis, ipts[munumber])

        ax1.set_ylabel("MU {}".format(munumber))
        # Use set_ylabel because if the MU is empty,
        # the channel number won't show.
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list):
        # Plot all the MUs.
        for count, thisMU in enumerate(munumber):
            norm_ipts = common.min_max_scaling(
                ipts[thisMU], col_by_col=False,
            )

            # Add value to the previous channel to avoid overlapping
            norm_ipts = norm_ipts + (0.5 - norm_ipts.mean()) + count
            ax1.plot(x_axis, norm_ipts)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(np.arange(0.5, len(munumber) + 0.5, 1))
        ax1.set_yticklabels([str(x) for x in munumber])

        # Set axes labels
        ax1.set_ylabel("Motor units")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise TypeError(
            "While calling the plot_ipts function, you should pass an " +
            "integer, a list or 'all' to munumber"
        )

    # Plot the ref signal
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )

        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Set tight layout if requested
    if tight_layout:
        plt.tight_layout()

    if showimmediately:
        plt.show()

    return fig