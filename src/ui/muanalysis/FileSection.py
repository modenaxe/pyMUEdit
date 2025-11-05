from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from core.muAnalysisCore.ResetButton import ResetButton
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components import ActionButton


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
        self.load_btn = ActionButton('Load File')
        self.load_btn.clicked.connect(
            lambda: mu.select_file_button_pushed(
                analysis_plot, False)
        )
        self.load_btn.setMinimumHeight(40)
        button_row.addWidget(self.load_btn, stretch=1)
        self.reset_btn = ResetButton('Reset')
        self.reset_btn.setMinimumHeight(40)
        button_row.addWidget(self.reset_btn, stretch=1)
