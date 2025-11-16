import pandas as pd
from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc

from openhdemg.library import get_mvc, compute_rfd

class ForceAnalysisFunc():

    """Functions for the force analysis of RFD and MVC"""

    def __init__(self, analysis_plot, ms):
        """Initialises class instance
        Params: analysis_plot: centre plot instance, ms: user input for RFD values
        Returns: class isntance
        """
        self.analysis_plot = analysis_plot
        self.rfd_value = ms

    def get_mvc(self):
        """Set up for MVC select range functionality
        Param: None
        Return: None
        """
        file = FileUploadFunc.file
        if file == None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        mvc = get_mvc(file)
        exportable_df = []
        exportable_df.append({"MVC": mvc})
        exportable_df = pd.DataFrame(exportable_df)
        store.append_analysis_hist(
            "MVC", exportable_df.to_dict("records")
        )

    def get_rfd(self):
        """Set up for RFD select range functionality
        Param: None
        Return: None
        """
        file = FileUploadFunc.file
        if file == None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        try:
            ms = self.rfd_value.get()
            ms = ms.split(',')
            ms = [int(val.strip()) for val in ms]
        except:
            ErrorDialog("Invalid RFD values", "Error").exec_()
        else:
            try:
                rfd = compute_rfd(file, ms)
                store.append_analysis_hist(
                    "RFD", rfd.to_dict("records")
                )
            except Exception as e:
                ErrorDialog(str(e), "Error").exec_()
