from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.GeneralRedButton import GeneralRedButton
from  core.muAnalysisCore.ResetButton import ResetButton
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame
)
from PyQt5.QtGui import QFont
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from ui.components.muAnalysisComponents.MajorHeading import MajorHeading

# class containing the file section of the right sidebar
# when button is clicked it calls mu class method, passing instance of the center layout as it needs

class FileSection(QFrame):

    """Section contianing file handling Load and Reset"""

    def __init__(self, sidebar, mu, analysis_plot):
        super().__init__(sidebar)
        self.setObjectName("FileSection")

        layout = QVBoxLayout(self)

        title_label = MajorHeading("File")
        title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY}; border: none")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setObjectName("sidebarTitle")

        # Create horizontal layout for the buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        browse_btn = GeneralButton('Load File', lambda: mu.select_file_button_pushed(analysis_plot, False))
        # browse_btn.setFixedWidth(120)
        #REMOVE THIS FOR FINAL JUST FOR TESTING
        browse_btn.setFixedWidth(90)
        browse_btn.setFixedHeight(40)

        json_btn = GeneralButton('Json File', lambda: mu.select_file_button_pushed(analysis_plot, True))
        # json_btn.setFixedWidth(120)
        #REMOVE THIS FOR FINAL JUST FOR TESTING
        json_btn.setFixedWidth(90)
        json_btn.setFixedHeight(40)

        self.reset_btn = ResetButton('Reset')
        # self.reset_btn.setFixedWidth(120)
        #REMOVE THIS FOR FINAL JUST FOR TESTING
        self.reset_btn.setFixedWidth(90)
        self.reset_btn.setFixedHeight(40)

        button_row.addWidget(browse_btn)
        button_row.addWidget(json_btn)
        button_row.addWidget(self.reset_btn)

        layout.addWidget(title_label)
        layout.addLayout(button_row)
        layout.addStretch(1)

