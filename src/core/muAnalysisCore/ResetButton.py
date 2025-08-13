from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.GeneralRedButton import GeneralRedButton

class ResetButton(GeneralRedButton):

    """A reset button component that emits a signal when clicked"""
    
    reset_requested = pyqtSignal()  # Signal emitted when reset is requested

    def __init__(self, text="Reset", parent=None):
        super().__init__(text, parent)
        self.clicked.connect(self.reset_requested.emit) 