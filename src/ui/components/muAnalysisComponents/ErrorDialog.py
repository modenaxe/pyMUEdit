from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStyle
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from ui.components.muAnalysisComponents.GeneralRedButton import GeneralRedButton

class ErrorDialog(QDialog):

    """Error dialog with custom message to be used for any user input errors"""

    def __init__(self, message, title="Confirm Action", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 120)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        message_label = QLabel(message)
        message_label.setFont(QFont("Arial", 18))
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        main_layout.addStretch(1)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(Qt.AlignCenter)
        cancel_button = GeneralRedButton("Ok")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        main_layout.addLayout(buttons_layout)