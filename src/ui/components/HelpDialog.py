from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QCheckBox, QToolButton, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from ui.components.ImageSlider import ImageSlider

class HelpDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("How to use")
        self.setFixedSize(500, 500)
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        window = ImageSlider()
        window.show()
        layout.addWidget(window)

        self.setLayout(layout)

        self.exec_()






