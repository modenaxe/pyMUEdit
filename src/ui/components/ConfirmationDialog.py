from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class ConfirmationDialog(QDialog):
    def __init__(self, message, title="Confirm Action", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 120)
        self.colors = {
            "bg_card": "#ffffff",
            "border": "#e0e0e0",
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "button_confirm_bg": "#dc3545",
            "button_confirm_hover": "#c82333",
            "button_cancel_bg": "#6c757d",
            "button_cancel_hover": "#5a6268",
        }

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        message_label = QLabel(message)
        message_label.setFont(QFont("Arial", 18))
        message_label.setStyleSheet(f"color: {self.colors['text_primary']};")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)

        main_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(Qt.AlignCenter)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['button_cancel_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_cancel_hover']};
            }}
            """
        )
        cancel_button.clicked.connect(self.reject)

        reset_button = QPushButton("Reset")
        reset_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['button_confirm_bg']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_confirm_hover']};
            }}
            """
        )
        reset_button.clicked.connect(self.accept)

        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(reset_button)

        main_layout.addLayout(buttons_layout)
