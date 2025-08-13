import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from ui.components.muAnalysisComponents.SaveablePlot import SaveablePlot


"""Functions from OPENHDEMG used to plot MUAPS"""

def extract_delsys_muaps(emgfile):
    """openhdemg: extract MUAPS obtained from Delsys decomposition
    Params:
        - emgfile: the file
    Returns:
        - dictionary of MUAPS for every MU
    """
    all_muaps = emgfile["EXTRAS"]
    muaps_dict = {mu: None for mu in range(emgfile["NUMBER_OF_MUS"])}
    for mu in range(emgfile["NUMBER_OF_MUS"]):
        df = pd.DataFrame(all_muaps.filter(regex=f"MU_{mu}_CH_"))
        df.columns = range(len(df.columns))
        muaps_dict[mu] = {"col0": df}

    return muaps_dict

def sta(
    emgfile, sorted_rawemg, firings=[0, 50], timewindow=50
):
    """openhdemg: Computes the spike-triggered average (STA) of every MU 
    Params:
        - emgfile: the file
        - sorted_rawemg: dict of sorted electrodes 
        - firings: list or str {"all"}. The range of firings for STA
        - timewindow: timewindow to compute STA in ms
    Returns:
        - dictionary of STAs
    """
    timewindow_samples = round((timewindow / 1000) * emgfile["FSAMP"])
    halftime = round(timewindow_samples / 2)
    tottime = halftime * 2

    sta_dict = {mu: {} for mu in range(emgfile["NUMBER_OF_MUS"])}

    for mu in sta_dict.keys():
        tot_firings = len(emgfile["MUPULSES"][mu])
        if tot_firings == 0:
            warnings.warn(f"Empty MU {mu} in sta(). It will be set to 0.")

        if firings == "all":
            firings_ = [0, tot_firings]
        else:
            firings_ = firings

        thismups = emgfile["MUPULSES"][mu][firings_[0]: firings_[1]]

        # Calculate STA for each column in sorted_rawemg
        sorted_rawemg_sta = {}
        for col in sorted_rawemg.keys():
            row_dict = {}
            for row in sorted_rawemg[col].columns:
                emg_array = sorted_rawemg[col][row].to_numpy()
                # Calculate STA using NumPy vectorized operations
                sta_values = []
                if len(thismups) > 0: 
                    for pulse in thismups:
                        ls = emg_array[pulse - halftime: pulse + halftime]
                        if len(ls) == tottime:
                            sta_values.append(ls)
                else:
                    if np.all(np.isnan(emg_array)):
                        sta_values.append(np.full((tottime, ), np.nan))
                    else:
                        sta_values.append(np.full((tottime, ), 0))
                row_dict[row] = np.mean(sta_values, axis=0)
            sorted_rawemg_sta[col] = pd.DataFrame(row_dict)
        sta_dict[mu] = sorted_rawemg_sta

    return sta_dict

def muaps_from_sta(
    analysis_plot,
    sta_dict,
    title="MUAPs from STA",
    figsize=[20, 15],
    tight_layout=False,
    line2d_kwargs_ax1=None,
):
    """openhdemg: plots MUAPs obtained from STA. Originally called plot_muaps 
    Params:
        - analysis_plot: instance of AnalysisPlot
        - sta_dict: dictionary generated from extract_delsys_muaps() or sta()
        - title: title of the plot 
        - figsize: size of the figure (legacy, plot goes in centre now)
        - tight_layout: adjusts the UI of the plot 
        - line2d_kwargs_ax1: arguments for a set of line2d objects
    Returns: None
    """
    if isinstance(sta_dict, dict):
        sta_dict = [sta_dict]

    if not isinstance(sta_dict, list):
        raise TypeError("sta_dict must be dict or list")

    # Find the largest and smallest value to define common y axis limits.
    ymax = 0
    ymin = 0
    for thisdict in sta_dict:
        for c in thisdict:
            max_ = thisdict[c].max().max()
            min_ = thisdict[c].min().min()
            if max_ > ymax:
                ymax = max_
            if min_ < ymin:
                ymin = min_
    if ymax == 0 and ymin == 0:
        ymax = 1
        ymin = -1

    cols = len(sta_dict[0])
    rows = len(sta_dict[0][next(iter(sta_dict[0]))].columns)

    figname = "MUAPs"
    fig, axs = plt.subplots(
        rows,
        cols,
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Manage exception of arrays instead of matrices and check that they
    # are correctly oriented.
    if cols > 1 and rows > 1:
        for thisdict in sta_dict:
            # Plot all the MUAPs
            for r in range(rows):
                for pos, c in enumerate(thisdict.keys()):
                    axs[r, pos].plot(thisdict[c].iloc[:, r])

                    axs[r, pos].set_ylim(ymin, ymax)
                    axs[r, pos].axis('off')

    elif cols == 1 and rows > 1:
        for thisdict in sta_dict:
            # Plot all the MUAPs
            for r in range(rows):
                for pos, c in enumerate(thisdict.keys()):
                    axs[r].plot(thisdict[c].iloc[:, r])

                    axs[r].set_ylim(ymin, ymax)
                    axs[r, pos].axis('off')

    elif cols > 1 and rows == 1:
        raise ValueError(
            "Arrays should be organised as 1 column, multiple rows. " +
            "Not as 1 row, multiple columns."
        )

    else:
        raise ValueError(
            "Unacceptable number of rows and columns to plot"
        )
        
    # Set tight layout if requested
    if tight_layout:
        plt.tight_layout()

    canvas = SaveablePlot(fig)
    analysis_plot.display_fig(canvas)
    plt.close()

