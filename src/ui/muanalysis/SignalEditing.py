from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QMessageBox,
    QDialog,
)
from ui.components.CleanTheme import CleanTheme
from ui.components.AnalysisButton import AnalysisButton
from ui.components.AnalysisText import AnalysisText


class SignalEditing(QWidget):
    def __init__(self, items=None, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        btn = AnalysisButton("Signal Editing", lambda: self.show_window(), parent=self)
        layout.addWidget(btn, stretch=1)

    def show_window(self):
        window = QDialog()

        window.setWindowTitle("Signal Editing Window")
        window_layout = QVBoxLayout()
        window.setLayout(window_layout)

        # title
        title = AnalysisText.create_title("Signal Editing") 
        window_layout.addWidget(title)

        # subtitle 
        emg_subtitle = AnalysisText.create_subtitle("EMG Signal")
        window_layout.addWidget(emg_subtitle)


        # another subtitle 
        reference_subtitle = AnalysisText.create_subtitle("Reference Signal")
        window_layout.addWidget(reference_subtitle)

        window.exec()


