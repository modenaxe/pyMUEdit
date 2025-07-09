from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QStyle,
    QMainWindow,
    QComboBox,
)
from ui.components.AnalysisText import AnalysisText

"""
If there's no figure/file, a title appears prompting the user to load a file
"""
class AnalysisPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.canvas = None
        self.load_file_prompt()

    # loads the prompt into canvas
    def load_file_prompt(self):
        self.layout.removeWidget(self.canvas)
        self.canvas = AnalysisText.create_prompt("Press Load File to View Data")
        self.layout.addWidget(self.canvas)

    def display_fig(self, fig=None):
        self.layout.removeWidget(self.canvas)
        self.canvas = fig 
        self.layout.addWidget(self.canvas)

