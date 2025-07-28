from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QFrame,
)
import pandas as pd
from ui.components import ActionButton
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme as AnalysisTheme
from PyQt5.QtCore import Qt
from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from core.muAnalysisCore.SelectRange import SelectRange
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput

class ForceAnalysisSection(QWidget):

    def __init__(self, sidebar, mu, analysis_plot):
        super().__init__(sidebar)

        self.analysis_plot = analysis_plot
        layout = QVBoxLayout(self)
        subtitle_label = AnalysisText.create_subtitle("FORCE ANALYSIS")
        mvc_button = GeneralButton('MVC', self.get_mvc)

        layout.addWidget(subtitle_label)

        rfd_layout = QHBoxLayout()
        rfd_value = AnalysisInput("", "")
        rfd_value.set("50,100,150,200")
        button = GeneralButton(
            "RFD",
            lambda: self.get_rfd()
        )
        rfd_layout.addWidget(rfd_value)
        rfd_layout.addWidget(button)

        layout.addLayout(rfd_layout)
        layout.addWidget(mvc_button)
        layout.addStretch(1)

    def get_mvc(self):
        file = FileUploadFunc.file
        if file == None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        SelectRange(self.analysis_plot, self.two_point, False)
    
    def two_point(self, x, y):
        emgfile = FileUploadFunc.file
        mvc = emgfile["REF_SIGNAL"].loc[x:y].max()
        mvc = float(mvc[0])
        exportable_df = []
        exportable_df.append({"MVC": mvc})
        exportable_df = pd.DataFrame(exportable_df)
        store.append_analysis_hist(
            "MUs Thresholds", exportable_df.to_dict("records")
        )
        return mvc

    def get_rfd(self):
        SelectRange(self.analysis_plot, self.two_point, True)