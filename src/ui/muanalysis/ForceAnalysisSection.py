import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QVBoxLayout, QWidget)

from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.ForceAnalysisFunc import ForceAnalysisFunc
from core.muAnalysisCore.AnalysisResultsHist import store
from core.muAnalysisCore.SelectRange import SelectRange
from ui.components import ActionButton
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import \
    CleanTheme as AnalysisTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.SubsectionTitle import SubsectionTitle


class ForceAnalysisSection(QWidget):

    """ui for the force analysis of rfd and MVC"""

    def __init__(self, sidebar, analysis_plot):
        super().__init__(sidebar)

        layout = QVBoxLayout(self)
        subtitle_label = SubsectionTitle("FORCE ANALYSIS")
        layout.addWidget(subtitle_label)
        rfd_layout = QHBoxLayout()
        rfd_value = AnalysisInput("", "")
        rfd_value.set("50,100,150,200")
        func = ForceAnalysisFunc(analysis_plot, rfd_value)
        mvc_button = GeneralButton('MVC', func.get_mvc)
        button = GeneralButton(
            "RFD",
            lambda: func.get_rfd()
        )
        rfd_layout.addWidget(rfd_value)
        rfd_layout.addWidget(button)
        layout.addLayout(rfd_layout)
        layout.addWidget(mvc_button)
        layout.addStretch(1)
