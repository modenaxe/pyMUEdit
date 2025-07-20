import copy
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
)

from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme as AnalysisTheme

class SortMUs(QWidget):
    def __init__(self, mu, analysis_plot, parent = None):
        super().__init__(parent)
        
        self.mu = mu
        self.analysis_plot = analysis_plot
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)
        
        btn = GeneralButton("Sort MUs", lambda: self.sort_MUs(), parent=self)
        layout.addWidget(btn, stretch=1)
        
        # returns boolean value based on whethere or not there's a valid file loaded
    def valid_file(self):
        if not self.mu.file:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return False 
        return True 

        
    def sort_MUs(self):
        if not self.valid_file():
            return
        
        print("sorting... ")
        emgfile = self.mu.file
        
        
        # code from openhdemg
        if emgfile["NUMBER_OF_MUS"] <= 1:
            return emgfile

        # Create the object to store the sorted emgfile.
        # Create a deepcopy to avoid changing the original emgfile
        sorted_emgfile = copy.deepcopy(self.mu.file)
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
        sorted_emgfile["BINARY_MUS_FIRING"] = sorted_emgfile["BINARY_MUS_FIRING"].reindex(
            columns=sorting_order
        )
        sorted_emgfile["BINARY_MUS_FIRING"].columns = np.arange(emgfile["NUMBER_OF_MUS"])

        # Sort MUPULSES.
        # Preferable to use the sorting_order as a double-check in alternative to:
        # sorted_emgfile["MUPULSES"] = sorted(
        #   sorted_emgfile["MUPULSES"], key=min, reverse=False)
        # )
        for origpos, newpos in enumerate(sorting_order):
            sorted_emgfile["MUPULSES"][origpos] = emgfile["MUPULSES"][newpos]

        self.mu.plot_idr(sorted_emgfile, self.analysis_plot)
        self.mu.updateEMGFile(sorted_emgfile)