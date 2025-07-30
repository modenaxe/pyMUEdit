import copy
from scipy import signal
from PyQt5.QtWidgets import (
    QWidget, 
    QFrame,
    QHBoxLayout,
    QDialog,
    QMessageBox,
)
import matplotlib.pyplot as plt
from app.muAnalysisFunctions.PlotEMGFunc import extract_delsys_muaps
from ui.components.SaveablePlot import SaveablePlot
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown, AnalysisLabeledDropdown
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from core.muAnalysisCore.SelectRange import SelectRange
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
# TODO: REMOVE uncessary imports

class PlotMUAP(QWidget):

    """
    The code for plotting MUAPs.
    Comes in the form of a button and some inputs 

    params:
        - analysis_plot instance 
        - matrix: dropdown instance, not the value 
        - orientation: dropdown instance, not the value
    """
    # TODO: check of the params are correct
    def __init__(self, analysis_plot, matrix, orientation, parent=None):
        super().__init__(parent)

        self.file = FileUploadFunc.file
        self.analysis_plot = analysis_plot
        self.matrix = matrix 
        self.orientation = orientation

        layout = QHBoxLayout(self)
        btn = GeneralButton("Plot MUAPs", self.plot, parent=self)
        layout.addWidget(btn, stretch=1)

        # configuration dropdown
        configuration_items = ["Monopolar", "Single differential", "Double differential"]
        configuration = AnalysisDropdown("Configuration", configuration_items, parent=self)
        layout.addWidget(configuration, stretch=1)

        # mu number dropdown
        mu_number_items = []
        if self.file["SOURCE"] in ["DEMUSE", "OTB", "CUSTOMCSV", "DELSYS"]:
            for i in range(self.file["NUMBER_OF_MUS"]):
                mu_number_items.append(str(i))
        mu_number = AnalysisDropdown("MU Number", mu_number_items, parent=self)
        layout.addWidget(mu_number, stretch=1)

        # configuration dropdown
        timewindow_items = ["25", "50", "100", "200"]
        timewindow = AnalysisDropdown("Timewindow (ms)", timewindow_items, parent=self)
        layout.addWidget(timewindow, stretch=1)


    # TODO:  go through this
    def plot(self):
        print("test")
        try:
            # DELSYS requires different MUAPS plot
            if self.file["SOURCE"] == "DELSYS":
                figsize = [int(i) for i in self.size_fig.get().split(",")]
                muaps_dict = extract_delsys_muaps(self.file)
                # TODO: change
                openhdemg.plot_muaps(
                    muaps_dict[int(self.muap_munum.get())],
                    figsize=figsize,
                )

            else:
                if self.matrix.get() == "None":
                    # Get rows and columns and turn into list
                    list_rcs = [int(i) for i in self.matrix_rc.get().split(",")]

                    try:
                        # Sort emg file
                        sorted_file = openhdemg.sort_rawemg(
                            emgfile=self.parent.resdict,
                            code=self.mat_code.get(),
                            orientation=int(self.orientation.get()),
                            n_rows=list_rcs[0],
                            n_cols=list_rcs[1],
                        )

                    except ValueError as e:
                        show_error_dialog(
                            parent=self,
                            error=e,
                            solution=str(
                                "Number of specified rows and columns must "
                                + "match the number of channels."
                            ),
                        )
                        return

                else:
                    # Sort emg file
                    sorted_file = openhdemg.sort_rawemg(
                        emgfile=self.parent.resdict,
                        code=self.mat_code.get(),
                        orientation=int(self.mat_orientation.get()),
                        custom_sorting_order=self.parent.settings.custom_sorting_order,
                    )

                # calcualte derivation
                if self.muap_config.get() == "Single differential":
                    diff_file = openhdemg.diff(sorted_rawemg=sorted_file)

                elif self.muap_config.get() == "Double differential":
                    diff_file = openhdemg.double_diff(
                        sorted_rawemg=sorted_file,
                    )

                elif self.muap_config.get() == "Monopolar":
                    diff_file = sorted_file

                # Calculate STA dictionary
                # Plot deviation
                sta_dict = openhdemg.sta(
                    emgfile=self.file,
                    sorted_rawemg=diff_file,
                    firings="all",
                    timewindow=int(self.muap_time.get()),
                )

                # Create list of figsize
                figsize = [int(i) for i in self.size_fig.get().split(",")]

                # Plot MUAPS
                openhdemg.plot_muaps(
                    sta_dict[int(self.muap_munum.get())],
                    figsize=figsize,
                )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Enter valid input parameters."
                    + "\nPotenital error sources:"
                    + "\n - Matrix Code"
                    + "\n - Matrix Orientation"
                    + "\n - Figure size arguments"
                    + "\n - Timewindow"
                    + "\n - MU Number"
                    + "\n - Rows,Columns arguments"
                    + "\n - custom_sorting_order in settings"
                ),
            )

        except UnboundLocalError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Enter valid Configuration."),
            )

        except KeyError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Enter valid Matrix Column."),
            )


