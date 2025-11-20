from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from app.muAnalysisFunctions.ForceAnalysisFunc import ForceAnalysisFunc
from ui.components import ActionButton
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput


class ForceAnalysisSection(QWidget):

    """ui for the force analysis of rfd and MVC"""

    def __init__(self, sidebar, analysis_plot):
        super().__init__(sidebar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        rfd_layout = QHBoxLayout()
        rfd_value = AnalysisInput("", "")
        rfd_value.set("50,100,150,200")
        func = ForceAnalysisFunc(analysis_plot, rfd_value)
        button = ActionButton("RFD")
        button.clicked.connect(lambda: func.get_rfd())
        button.setMinimumHeight(40)
        rfd_layout.addWidget(rfd_value)
        rfd_layout.addWidget(button)
        layout.addLayout(rfd_layout)
        layout.addStretch(1)
