import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import warnings
import copy
import itertools

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
    showimmediately=False,
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

#OPENHDEMG
def plot_differentials(
    emgfile,
    differential,
    column="col0",
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
    common = CommonOpenFunc()
    
    #print("column: ", column)
    #print("keys: ", differential.keys())

    if column not in differential:
        print(f"ERROR: '{column}' not in differential keys: {list(differential.keys())}")
        raise KeyError(f"differential does not contain the column '{column}'")

    emgsig = differential[column]

    if not isinstance(emgsig, pd.DataFrame):
        print(f"ERROR: differential['{column}'] is of type {type(emgsig)}")
        raise TypeError(
            "The signal differential[column] is present but not in a DataFrame"
        )

    # Here we produce an x axis in seconds or samples
    if timeinseconds:
        x_axis = emgsig.index / emgfile["FSAMP"]
    else:
        x_axis = emgsig.index

    # Create figure and axis
    figname = "Differentials"
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Plot all the channels
    if manual_offset == 0:
        # Normalise the df
        norm_raw_all = common.min_max_scaling(emgsig, col_by_col=False)

        for count, thisChannel in enumerate(emgsig.columns):
            norm_raw = norm_raw_all[thisChannel]

            # Add value to the previous channel to avoid overlapping
            norm_raw = norm_raw + (0.5 - norm_raw.mean()) + count
            ax1.plot(x_axis, norm_raw)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(np.arange(0.5, len(emgsig.columns) + 0.5, 1))
        ax1.set_yticklabels([str(x) for x in emgsig.columns])

        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif manual_offset > 0:
        half_offset = manual_offset / 2
        for count, thisChannel in enumerate(emgsig.columns):
            data = emgsig[thisChannel]

            # Add offset to the previous channel to avoid overlapping
            if count == 0:
                data = data + half_offset
                ax1.plot(x_axis, data)
            else:
                data = data + half_offset + manual_offset * count
                ax1.plot(x_axis, data)

        # Ensure correct and complete ticks on the left y axis
        """ ax1.set_yticks(
            np.arange(
                half_offset,
                len(emgsig.columns) * manual_offset + half_offset,
                manual_offset,
            )
        ) """
        ax1.set_yticks(
            np.linspace(
                start=half_offset,
                stop=len(emgsig.columns) * manual_offset + half_offset - manual_offset,
                num=len(emgsig.columns),
            )
        )
        ax1.set_yticklabels([str(x) for x in emgsig.columns])

        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise ValueError(
            "When calling the plot_differentials function, manual_offset " +
            "must be >= 0"
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

#OPENHDEMG
def diff(sorted_rawemg):

    # Create a dict of pd.DataFrames for the single differential
    # {"col0": {}, "col1": {}, "col2": {}, "col3": {}, "col4": {}}
    sd = {col: {} for col in sorted_rawemg.keys()}

    # Loop matrix columns
    for col in sorted_rawemg.keys():
        # Loop matrix rows
        for pos, row in enumerate(sorted_rawemg[col].columns):
            if pos > 0:
                res = (
                    sorted_rawemg[col].loc[:, row - 1] - sorted_rawemg[col].loc[:, row]
                )
                sd[col][row] = res

        sd[col] = pd.DataFrame(sd[col])

    return sd

#OPENHDEMG
def double_diff(sorted_rawemg):

    # Create a dict of pd.DataFrames for the double differential
    # {"col0": {}, "col1": {}, "col2": {}, "col3": {}, "col4": {}}
    dd = {col: {} for col in sorted_rawemg.keys()}

    # Loop matrix columns
    for col in sorted_rawemg.keys():
        # Loop matrix rows
        for pos, row in enumerate(sorted_rawemg[col].columns):
            if pos > 1:
                res = (
                    -sorted_rawemg[col].loc[:, row - 2]
                    + 2 * sorted_rawemg[col].loc[:, row - 1]
                    - sorted_rawemg[col].loc[:, row]
                )
                dd[col][row] = res

        dd[col] = pd.DataFrame(dd[col])

    return dd

#OPENHDEMG
def sort_rawemg(
    emgfile,
    code="GR08MM1305",
    orientation=180,
    dividebycolumn=True,
    n_rows=None,
    n_cols=None,
    custom_sorting_order=None,
):

    valid_codes = [
        "GR08MM1305",
        "GR04MM1305",
        "GR10MM0808",
        "Trigno Galileo Sensor",
        "None",
        "Custom",
    ]
    if code not in valid_codes:
        return ValueError("Unsupported code in sort_rawemg()")

    # Work on a copy of the RAW_SIGNAL
    rawemg = copy.deepcopy(emgfile["RAW_SIGNAL"])

    # Get sorting order by matrix code
    if code == "Custom":
        # Theck that custom_sorting_order has been specified
        if not isinstance(custom_sorting_order, list):
            raise ValueError(
                "In sort_rawemg(), custom_sorting_order must be a list of " +
                "lists when code=='Custom'"
            )

        # Get custom sorting order
        base0_sorting_order = custom_sorting_order

    elif code in ["GR08MM1305", "GR04MM1305"]:
        # Get sorting order by matrix orientation
        if orientation == 0:
            """
            MUST REMEMBER: python loops from 0 and the emg channels start
            from 0 but the channel order reflects the real channels and
            starts from 1! This order is for the user, while the script
            uses the base0_sorting_order.

            base0_sorting_order provides the sorting order while
            base0_nanpos indicates the position of the empty (np.nan)
            channel.

            Channel Order GR08MM1305
                   0   1   2   3   4
            0     64  39  38  13  12
            1     63  40  37  14  11
            2     62  41  36  15  10
            3     61  42  35  16   9
            4     60  43  34  17   8
            5     59  44  33  18   7
            6     58  45  32  19   6
            7     57  46  31  20   5
            8     56  47  30  21   4
            9     55  48  29  22   3
            10    54  49  28  23   2
            11    53  50  27  24   1
            12    52  51  26  25 NaN
            """
            base0_sorting_order = [
                [63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52,     51],
                [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,     50],
                [37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26,     25],
                [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,     24],
                [11, 10,  9,  8,  7,  6,  5,  4,  3,  2,  1,  0, np.nan],
            ]

        elif orientation == 180:
            """
            Channel Order GR08MM1305
                   0   1   2   3   4
            0    NaN  25  26  51  52
            1      1  24  27  50  53
            2      2  23  28  49  54
            3      3  22  29  48  55
            4      4  21  30  47  56
            5      5  20  31  46  57
            6      6  19  32  45  58
            7      7  18  33  44  59
            8      8  17  34  43  60
            9      9  16  35  42  61
            10    10  15  36  41  62
            11    11  14  37  40  63
            12    12  13  38  39  64
            """
            base0_sorting_order = [
                [np.nan,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11],
                [24,     23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12],
                [25,     26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37],
                [50,     49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38],
                [51,     52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63],
            ]

    elif code == "GR10MM0808":
        if orientation == 0:
            """
            Channel Order GR10MM0808
                0   1   2   3   4   5   6   7
            0  57  49  41  33  25  17   9   1
            1  58  50  42  34  26  18  10   2
            2  59  51  43  35  27  19  11   3
            3  60  52  44  36  28  20  12   4
            4  61  53  45  37  29  21  13   5
            5  62  54  46  38  30  22  14   6
            6  63  55  47  39  31  23  15   7
            7  64  56  48  40  32  24  16   8
            """
            base0_sorting_order = [
                [56, 57, 58, 59, 60, 61, 62, 63],
                [48, 49, 50, 51, 52, 53, 54, 55],
                [40, 41, 42, 43, 44, 45, 46, 47],
                [33, 33, 34, 35, 36, 37, 38, 39],
                [24, 25, 26, 27, 28, 29, 30, 31],
                [16, 17, 18, 19, 20, 21, 22, 23],
                [8,  9, 10, 11, 12, 13, 14, 15],
                [0,  1,  2,  3,  4,  5,  6,  7],
            ]

        elif orientation == 180:
            """
            Channel Order GR10MM0808
                0   1   2   3   4   5   6   7
            0   8  16  24  32  40  48  56  64
            1   7  16  23  31  39  47  55  63
            2   6  14  22  30  38  46  54  62
            3   5  13  21  29  37  45  53  61
            4   4  12  20  28  36  44  52  60
            5   3  11  19  27  35  43  51  59
            6   2  10  18  26  34  42  50  58
            7   1   9  17  25  33  41  49  57
            """
            base0_sorting_order = [
                [7,   6,  5,  4,  3,  2,  1,  0],
                [15, 14, 13, 12, 11, 10,  9,  8],
                [23, 22, 21, 20, 19, 18, 17, 16],
                [31, 30, 29, 28, 27, 26, 25, 24],
                [39, 38, 37, 36, 35, 34, 33, 32],
                [47, 46, 45, 44, 43, 42, 41, 40],
                [55, 54, 53, 52, 51, 50, 49, 48],
                [63, 62, 61, 60, 59, 58, 57, 56],
            ]

    elif code == "Trigno Galileo Sensor":
        """
        Channel Order Trigno Galileo Sensor

            1
        4       2
            3

        Will be represented as:
            0
        0   1
        1   2
        2   3
        3   4
        """
        base0_sorting_order = [[0, 1, 2, 3]]

    else:  # elif code == "None":
        pass

    # Once the order to sort channels has been retrieved,
    # Sort the channels based on pre-specified order and reset columns
    if code not in [None, "None"]:
        flattened_base0_sorting_order = list(
            itertools.chain(*base0_sorting_order),
        )
        sorted_rawemg = rawemg.reindex(columns=flattened_base0_sorting_order)
        sorted_rawemg.columns = range(sorted_rawemg.columns.size)
    else:
        # Always allow a way to avoid electrodes sorting.
        # Return a copy of the RAW_SIGNAL
        sorted_rawemg = rawemg

    # Check if we need the sorted RAW_SIGNAL divided by column
    if dividebycolumn:
        if code not in [None, "None"]:
            n_cols = len(base0_sorting_order)
            n_rows = len(base0_sorting_order[0])

        else:
            # Check if n_rows and n_cols have been passed
            if not isinstance(n_rows, int):
                raise ValueError(
                    "In sort_rawemg(), n_rows and n_cols must be integers " +
                    "when code == 'None'"
                )
            if not isinstance(n_cols, int):
                raise ValueError(
                    "In sort_rawemg(), n_rows and n_cols must be integers " +
                    "when code == 'None'"
                )

        # Create the empty dict to fill with the sorted_rawemg divided by
        # columns. But first check for missing empty channel.
        if n_rows * n_cols != sorted_rawemg.shape[1]:
            raise ValueError(
                "Number of rows * columns must match the number of channels."
            )

        empty_dict = {f"col{n}": None for n in range(n_cols)}

        for pos, col in enumerate(empty_dict.keys()):
            empty_dict[col] = sorted_rawemg.iloc[:, n_rows*pos:n_rows*(pos+1)]

        sorted_rawemg = empty_dict

    return sorted_rawemg
