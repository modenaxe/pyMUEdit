import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QStyle, QVBoxLayout
from core.logger import logger

class SuccessDialog(QDialog):
    def __init__(self, title_label="Success!", text="Please change text."):
        super().__init__()
        self.setWindowTitle("Success")
        # self.setFixedSize(350, 280)
        self.setMinimumWidth(350)
        self.setMaximumHeight(350)
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ✅ icon
        icon_label = QLabel()
        current_dir = os.path.dirname(__file__)
        icon_path = os.path.join(current_dir, "../../public/success_icon.png")
        pixmap = QPixmap(icon_path)
        if not os.path.exists(icon_path) or not pixmap or pixmap.isNull():
            icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
            icon_label.setPixmap(icon.pixmap(48, 48))
            logger.warning("✅ icon not found")
        else:
            icon_label.setPixmap(
                pixmap.scaled(
                    64,
                    64,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # title
        title = QLabel(title_label)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #222;")
        layout.addWidget(title)

        # Description text
        message = QLabel(text)
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("font-size: 13px; color: #555;")
        message.adjustSize()
        layout.addWidget(message)

        # yes button
        yes_button = QPushButton("Yes")
        yes_button.setFixedHeight(36)
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0061d0;
            }
        """)
        yes_button.clicked.connect(self.accept)
        layout.addWidget(yes_button)

        self.setLayout(layout)
        self.adjustSize()

        self.exec_()
