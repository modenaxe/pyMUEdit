from PyQt5.QtCore import pyqtSignal

from ui.components import ActionButton

class ResetButton(ActionButton):

    """A reset button component that emits a signal when clicked"""

    reset_requested = pyqtSignal()  # Signal emitted when reset is requested

    def __init__(self, text="Reset", parent=None):
        super().__init__(text, parent)
        self.clicked.connect(self.reset_requested.emit)