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
        self.load_btn = GeneralButton(
            'Load File', lambda: mu.select_file_button_pushed(
                analysis_plot, False))
        button_row.addWidget(self.load_btn, stretch=1)
        self.reset_btn = ResetButton('Reset')
        self.reset_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #475058;
                color: #fff;
                border-radius: 5px;
                font-size: 1em;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #495057;
            }
            """
        )
        button_row.addWidget(self.reset_btn, stretch=1)
