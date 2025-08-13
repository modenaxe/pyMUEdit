from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from core.muAnalysisCore.ResetButton import ResetButton
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.GeneralRedButton import \
    GeneralRedButton


class FileSection(QFrame):

    """UI Section containing file handling Load and Reset"""

    def __init__(self, sidebar, mu, analysis_plot):
        super().__init__(sidebar)
        self.setObjectName("FileSection")
        layout = QVBoxLayout(self)
        title_label = AnalysisText.create_major_title("File")
        title_label.setObjectName("sidebarTitle")
        layout.addWidget(title_label)
        button_row = QHBoxLayout()
        layout.addLayout(button_row)
        browse_btn = GeneralButton(
            'Load File', lambda: mu.select_file_button_pushed(
                analysis_plot, False))
        button_row.addWidget(browse_btn, stretch=1)
        self.reset_btn = ResetButton('Reset')
        button_row.addWidget(self.reset_btn, stretch=1)
