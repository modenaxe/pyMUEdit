from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.GeneralRedButton import GeneralRedButton
from  core.muAnalysisCore.ResetButton import ResetButton
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText

# class containing the file section of the right sidebar
# when button is clicked it calls mu class method, passing instance of the center layout as it needs

class FileSection(QFrame):

    """Section contianing file handling Load and Reset"""

    def __init__(self, sidebar, mu, analysis_plot):
        super().__init__(sidebar)
        self.setObjectName("FileSection")

        layout = QVBoxLayout(self)

        title_label = AnalysisText.create_major_title("File") 
        title_label.setObjectName("sidebarTitle")
        layout.addWidget(title_label)

        # Create horizontal layout for the buttons
        button_row = QHBoxLayout()
        layout.addLayout(button_row)

        # load file button
        browse_btn = GeneralButton('Load File', lambda: mu.select_file_button_pushed(analysis_plot, False))
        button_row.addWidget(browse_btn, stretch=1)

        # json button 
        # json_btn = GeneralButton('Json File', lambda: mu.select_file_button_pushed(analysis_plot, True))
        # button_row.addWidget(json_btn, stretch=1)


        # reset row 
        reset_row = QHBoxLayout()
        layout.addLayout(reset_row)

        # adding a filler to align the reset button better
        filler = QWidget()
        reset_row.addWidget(filler, stretch=1)

        # reset button 
        self.reset_btn = ResetButton('Reset')
        reset_row.addWidget(self.reset_btn, stretch=1)
