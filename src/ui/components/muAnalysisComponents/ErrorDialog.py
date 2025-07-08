from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStyle
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class ErrorDialog(QDialog):
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

        cancel_button = QPushButton("Ok")
        cancel_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color:  #d32f2f;
            }}
            """
        )
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(cancel_button)
        main_layout.addLayout(buttons_layout)