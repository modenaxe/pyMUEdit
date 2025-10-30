import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
from ui.components.muAnalysisComponents.ConfirmationDialog import ConfirmationDialog
from ui.components.muAnalysisComponents.SaveablePlot import SaveablePlot
from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog

import openhdemg.library as emg

class FileUploadFunc:
    """Methods for handling the emgFile and its intital display to centre"""

    # global instance of file
    file = None

    def __init__(self):
        """Initialises class instance
        Params: None
        Returns: class instance
        """
        self.file_path = None
        self.coords = []
        self.cid = None
        self.mvc_value = None
        self.json = False
        self.unsortedFile = None  # store unsorted file version here

    def data_loaded(self):
        """Check if an EMG file is currently loaded.

        Returns:
            Boolean indicating whether self.file contains valid data
        """
        return self.file is not None

    def select_file_button_pushed(self, analysis_plot, json):
        """Method triggered on file uplaod button, allowing only valid files and importing the data from a file dialog
        Params: analysis_plot: centre plot instance, json: make true for testing with json files
        Returns: None
        """
        file_dialog = QFileDialog()
        if json:
            self.json = True
            file_path, _ = file_dialog.getOpenFileName(
                None, "Select file", "", "JSON Files (*.json);;All Files (*.*)"
            )
        else:
            file_path, _ = file_dialog.getOpenFileName(
                None, "Select file", "", "MAT Files (*.mat);;All Files (*.*)"
            )
        if file_path:
            self.load_file(analysis_plot, file_path, json)

    def load_file(self, analysis_plot, file_path, json):
        """Load EMG file from specified path and plot the data
        Params: filepath, analysis_plot: centre plot instance, json: if to be loaded from json
        Returns: None
        """
        error = 0

        emgfile = None
        if json:
            emgfile = emg.emg_from_json(file_path)
        else:
            try:
                emgfile = emg.emg_from_otb(file_path)
            except NotImplementedError as e:
                ErrorDialog(
                    f"{e}",
                    "NotImplementedError",
                ).exec_()
                error = 1
            except:
                self.import_data(None, None)
                error = 1

        self.file = self.sort_MUs(emgfile)
        self.file_path = file_path
        self.import_data(analysis_plot, self.file)

        return error

    def import_data(self, analysis_plot, emgfile):
        """Plots files in centre if the file is valid
        Params: filepath, analysis_plot: centre plot instance, emgfile
        Returns: None
        """
        if emgfile:
            self.plot_idr(self.file, analysis_plot)
        elif self.error:
            ErrorDialog("Loaded File has errors", "Error").exec_()

    def plot_idr(
        self,
        emgfile,
        analysis_plot,
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
        """from openHDEMG to plot idr on graph when first loaded
        Params (relevant to us): emgfile, analysis_plot(instance of centre plot)
        Returns: None
        """
        common = CommonOpenFunc()
        idr = common.compute_idr(emgfile=emgfile)
        if isinstance(munumber, str):
            if emgfile["NUMBER_OF_MUS"] == 1:
                munumber = 0
            else:
                munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]
        if isinstance(munumber, list) and len(munumber) == 1:
            munumber = munumber[0]
        figname = "aditi_unique_name"
        plt.close()  # This is to prevent plots from overlaying in centre on repeated uploads
        fig, ax1 = plt.subplots(
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=figname,
        )
        if isinstance(munumber, int):
            ax1.plot(
                idr[munumber]["timesec" if timeinseconds else "mupulses"],
                idr[munumber]["idr"],
                ".",
                markersize=12,
            )
            ax1.set_ylabel("MU {} (pps)".format(munumber))
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
        elif isinstance(munumber, list):
            idr_all = pd.DataFrame({key: df["idr"] for key, df in idr.items()})
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
                    ".",
                    markersize=8,
                )
            ax1.set_yticks(np.arange(0.5, len(munumber) + 0.5, 1))
            ax1.set_yticklabels([str(mu) for mu in munumber])
            ax1.set_ylabel("Motor units")
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
        else:
            raise TypeError(
                "While calling the plot_idr function, you should pass an "
                + "integer, a list or 'all' to munumber"
            )
        if addrefsig:
            if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
                raise TypeError(
                    "REF_SIGNAL is probably absent or it is not contained in a "
                    + "dataframe"
                )
            x_axis = (
                emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
                if timeinseconds
                else emgfile["REF_SIGNAL"].index
            )
            ax2 = ax1.twinx()
            ax2.plot(x_axis, emgfile["REF_SIGNAL"][0], color='#555555')
            ax2.set_ylabel("MVC")
            ax2.set_zorder(0)
            ax1.set_zorder(1)
            ax1.patch.set_alpha(0)
        canvas = SaveablePlot(fig)  # plotting in centre with the data now handled
        analysis_plot.display_fig(canvas)

    def handle_reset_workflow(self, analysis_plot):
        """
        Handles the full workflow for resetting analysis data, including confirmation.
        Params: analysis_plot: centre plot instance
        Returns: None
        """
        # Check if there's a file loaded to reset
        if self.file_path is None:
            print("No file loaded to reset.")
            return

        dialog = ConfirmationDialog(
            "This will reset the current analysis.", "Confirm Reset"
        )
        if dialog.exec_() == QDialog.Accepted:
            # User clicked 'Reset'
            self.reset_analysis_data(analysis_plot)

    def reset_analysis_data(self, analysis_plot):
        """
        Resets the analysis data by reloading the original file, clearing any transformations.
        Params: analysis_plot: centre plot instance
        Returns: None
        """
        if self.file_path is None:
            print("No original file path stored. Cannot reset.")
            return

        print("--- DEBUG: Resetting analysis data by reloading original file ---")

        # Clear any transformation data (MVC value, etc.)
        self.mvc_value = None
        # Add any other transformation data clearing logic here

        # Reload the original file to reset any transformations
        error = self.load_file(analysis_plot, self.file_path, self.json)
        if error == 0:
            print("File successfully reloaded, transformations cleared.")
        else:
            print("Error reloading file during reset.")
            # If reload fails, show error but keep the original file path
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("Reset Error")
            error_dialog.setInformativeText("Failed to reload the original file")
            error_dialog.setWindowTitle("Error")
            error_dialog.exec_()

    def plot_refsig(
        self,
        emgfile,
        analysis_plot,
        timeinseconds=True,
        figsize=[20, 15],
        tight_layout=True,
        line2d_kwargs_ax1=None,
        axes_kwargs=None,
        showimmediately=False,
    ):
        """From OPENHDEMG. Plots the reference signal
        Params:
            - emgfile: the file
            - analysis_plot: instance used to plot fig in the centre
            - timeinseconds: boolean if you want the axis to be plotted in seconds
            - figsize: (legacy code) defines the size of the plot, but now it's
            plotted in the centre
            - tight_layout: specifies different UI for the plot
            - line2d_kwargs_ax1: keyword arguments for line2d objects
            - axes_kwargs: keyword arguments for axes styling
            - showimmediately: (legacy code) plots it immediately, but this function now defaults to plotting it immediately
        """
        if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            refsig = emgfile["REF_SIGNAL"]
        else:
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a "
                + "dataframe"
            )

        if timeinseconds:
            x_axis = refsig.index / emgfile["FSAMP"]
        else:
            x_axis = refsig.index

        figname = "Reference Signal Graph"
        plt.close()
        fig, ax1 = plt.subplots(
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=figname,
        )

        ax1.plot(x_axis, refsig[0], color='#555555')

        ax1.set_ylabel("MVC")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        # Plotting
        canvas = SaveablePlot(fig)
        analysis_plot.display_fig(canvas)

    def sort_MUs(self, emgfile):
        """
        Sort motor units (MUs) in an EMG file based on the timing of their
        first detected pulse.

        Parameters
        ----------
        emgfile : dict
            A dictionary containing EMG data fields, including MU pulse timings,
            accuracy metrics, binary firing patterns, and other related signals.

        Returns
        -------
        dict
            A new EMG file dictionary with all MU-related fields sorted according
            to the order of their first pulses.
        """

        if emgfile["NUMBER_OF_MUS"] <= 1:
            return emgfile

        # Create the object to store the sorted emgfile.
        # Create a deepcopy to avoid changing the original emgfile
        sorted_emgfile = copy.deepcopy(emgfile)
        """
        Need to be changed: ==>
        emgfile =   {
                    "SOURCE" : SOURCE,
                    "RAW_SIGNAL" : RAW_SIGNAL,
                    "REF_SIGNAL" : REF_SIGNAL,
                    ==> "ACCURACY": ACCURACY,
                    ==> "IPTS" : IPTS,
                    ==> "MUPULSES" : MUPULSES,
                    "FSAMP" : FSAMP,
                    "IED" : IED,
                    "EMG_LENGTH" : EMG_LENGTH,
                    "NUMBER_OF_MUS" : NUMBER_OF_MUS,
                    ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                    }
        """

        # Identify the sorting_order by the first MUpulse of every MUs
        df = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            if len(emgfile["MUPULSES"][mu]) > 0:
                df.append(emgfile["MUPULSES"][mu][0])
            else:
                df.append(np.inf)

        df = pd.DataFrame(df, columns=["firstpulses"])
        df.sort_values(by="firstpulses", inplace=True)
        sorting_order = list(df.index)

        # Sort ACCURACY (single column)
        for origpos, newpos in enumerate(sorting_order):
            sorted_emgfile["ACCURACY"].loc[origpos] = emgfile["ACCURACY"].loc[newpos]

        # Sort IPTS (multiple columns, sort by columns, then reset columns' name)
        sorted_emgfile["IPTS"] = sorted_emgfile["IPTS"].reindex(columns=sorting_order)
        sorted_emgfile["IPTS"].columns = np.arange(emgfile["NUMBER_OF_MUS"])

        # Sort BINARY_MUS_FIRING (multiple columns, sort by columns,
        # then reset columns' name)
        sorted_emgfile["BINARY_MUS_FIRING"] = sorted_emgfile[
            "BINARY_MUS_FIRING"
        ].reindex(columns=sorting_order)
        sorted_emgfile["BINARY_MUS_FIRING"].columns = np.arange(
            emgfile["NUMBER_OF_MUS"]
        )

        for origpos, newpos in enumerate(sorting_order):
            sorted_emgfile["MUPULSES"][origpos] = emgfile["MUPULSES"][newpos]

        return sorted_emgfile
