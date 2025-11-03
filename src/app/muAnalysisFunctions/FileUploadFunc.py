import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
# from core.utils.manual_editing.h5_import import h5py_convert
from ui.components.muAnalysisComponents.ConfirmationDialog import ConfirmationDialog
from ui.components.muAnalysisComponents.SaveablePlot import SaveablePlot
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog

from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

# from h5py import File as h5py

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

    def set_file(self, emgfile):
        """Sets the current emg file
        Params: emgfile
        Returns: None
        """
        FileUploadFunc.file = emgfile

    def data_loaded(self):
        """Check if an EMG file is currently loaded.

        Returns:
            Boolean indicating whether FileUploadFunc.file contains valid data
        """
        return FileUploadFunc.file is not None

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
                """
                TODO: handle h5py files
                """
                ErrorDialog(
                    f"{e}",
                    "NotImplementedError",
                ).exec_()
                error = 1
                # f = h5py(file_path, "r")
                # print("h5py File load success")
                # files = h5py_convert().h5py_to_dict(f)
                # print(files)
            except:
                self.import_data(None, None)
                error = 1

        if emgfile:
            # FileUploadFunc.file = emg.sort_mus(emgfile)
            FileUploadFunc.file = emgfile
            self.file_path = file_path
            self.import_data(analysis_plot, FileUploadFunc.file)

        return error

    def import_data(self, analysis_plot, emgfile):
        """Plots files in centre if the file is valid
        Params: filepath, analysis_plot: centre plot instance, emgfile
        Returns: None
        """

        if emgfile:
            # fig = emg.plot_idr(emgfile, showimmediately=False)
            # canvas = SaveablePlot(fig)  # plotting in centre with the data now handled
            # analysis_plot.display_fig(canvas)
            self.plot_idr(emgfile, analysis_plot)
        else:
            ErrorDialog("Loaded File has errors", "Error").exec_()

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

    """
    needs to be retained due to bug in existing openHDEMG library which
    errors on plotting subsequent figures after initial import
    """
    def plot_idr(
        self,
        emgfile,
        analysis_plot,
        munumber="all",
        addrefsig=True,
        timeinseconds=True,
        figsize=[20, 15],
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