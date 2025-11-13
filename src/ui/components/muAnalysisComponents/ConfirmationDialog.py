from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QLabel, QVBoxLayout)

from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components import ActionButton


class ConfirmationDialog(QDialog):

    """
    Dialog for confirming a reset
    """

    def __init__(self, message, title="Confirm Action", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 120)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        message_label = QLabel(message)
        message_label.setFont(QFont("Arial", 18))
        message_label.setStyleSheet(f"color: {CleanTheme.DIALOG_TEXT};")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        main_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(Qt.AlignCenter)

        cancel_button = ActionButton("Cancel", primary=False)
        cancel_button.clicked.connect(lambda: self.reject())
        cancel_button.setFixedHeight(30)

        reset_button = ActionButton("Confirm")
        reset_button.clicked.connect(self.accept)
        reset_button.setFixedHeight(30)

        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(reset_button)
        main_layout.addLayout(buttons_layout)
