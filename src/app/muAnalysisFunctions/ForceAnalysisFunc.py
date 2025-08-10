import pandas as pd
from PyQt5.QtCore import Qt
from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from core.muAnalysisCore.SelectRange import SelectRange

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
        SelectRange(self.analysis_plot, self.two_point, False)
    
    def two_point(self, x, y):
        """Function for select range once start and end are selected to find MVC and display on results table
        Param: x,y: coords from select range
        Return: MVC
        """
        emgfile = FileUploadFunc.file
        mvc = emgfile["REF_SIGNAL"].loc[x:y].max()
        mvc = float(mvc[0])
        exportable_df = []
        exportable_df.append({"MVC": mvc})
        exportable_df = pd.DataFrame(exportable_df)
        store.append_analysis_hist(
            "MVC", exportable_df.to_dict("records")
        )
        return mvc

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
            SelectRange(self.analysis_plot, lambda start,end:self.one_point(start,end,ms), True)

    def one_point(self, start_, y, ms):
        """Function for select range once start is slected to find RFD and display on results table
        Param: start_,y: coords from select range (only start_ is used), ms: user input for miliseconds range
        Return: None
        """
        emgfile = FileUploadFunc.file
        rfd_dict = dict.fromkeys(ms, None)
        for thisms in ms:
            ms_insamples = round((int(thisms) * emgfile["FSAMP"]) / 1000)
            n_0 = emgfile["REF_SIGNAL"].loc[start_]
            n_next = emgfile["REF_SIGNAL"].loc[start_ + ms_insamples]

            rfdval = (n_next - n_0) / (thisms / 1000)
            rfd_dict[thisms] = rfdval
        rfd = pd.DataFrame(rfd_dict)
        store.append_analysis_hist(
        "RFD", rfd.to_dict("records")
        )
