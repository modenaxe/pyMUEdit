import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
# from core.utils.manual_editing.h5_import import h5py_convert
from ui.components.muAnalysisComponents.ConfirmationDialog import ConfirmationDialog
from ui.components.muAnalysisComponents.SaveablePlot import SaveablePlot
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog

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
            self.file = emg.sort_mus(emgfile)
            self.file_path = file_path
            self.import_data(analysis_plot, self.file)

        return error

    def import_data(self, analysis_plot, emgfile):
        """Plots files in centre if the file is valid
        Params: filepath, analysis_plot: centre plot instance, emgfile
        Returns: None
        """
        if emgfile:
            fig = emg.plot_idr(self.file, showimmediately=False)
            canvas = SaveablePlot(fig)  # plotting in centre with the data now handled
            analysis_plot.display_fig(canvas)
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