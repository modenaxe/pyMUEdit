from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QCheckBox, QToolButton, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import os

class WarningDialog(QDialog):
    def __init__(self, title_label="Warning", text="This is a warning Pop-up box. "
                         "Please change text.\n"
                         "Are you sure you want to continue?", enableCheckBox=True, checkBoxText="Don't ask again",
                         enableHelpButton=True, HelpButtonTip="Click for help"):
        super().__init__()
        self.setWindowTitle("Warning")
        #self.setFixedSize(350, 290)
        self.setMinimumWidth(350)
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.enableCheckBox = enableCheckBox
        self.checkbox_selected = False

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        #add help button
        if(enableHelpButton):
            help_row = QHBoxLayout()
            help_row.addStretch()
            help_button = QToolButton()
            help_button.setText("?")
            help_button.setFixedSize(24, 24)
            help_button.setStyleSheet("""
                QToolButton {
                    font-weight: bold;
                    font-size: 16px;
                    border: 1px solid #ccc;
                    border-radius: 12px;
                    background-color: #eee;
                }
                QToolButton:hover {
                    background-color: #ddd;
                }
            """)
            help_button.setToolTip(HelpButtonTip)
            help_row.addWidget(help_button)
            layout.addLayout(help_row)

        # ⚠️ icon
        icon_label = QLabel()
        current_dir = os.path.dirname(__file__)
        icon_path = os.path.join(current_dir, "../../public/warning_icon.png")
        pixmap = QPixmap(icon_path)
        if not os.path.exists(icon_path) or not pixmap or pixmap.isNull():
            icon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
            icon_label.setPixmap(icon.pixmap(48, 48))
            print("⚠️ Image not found")
        else:
            icon_label.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        icon_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(icon_label)

        # title
        title = QLabel(title_label)
        title.setStyleSheet("font-weight: bold; font-size: 18px;")
        title.setAlignment(Qt.AlignHCenter)
        layout.addWidget(title)

        # Description text
        message = QLabel(text)
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 13px; color: #333;")
        message.setAlignment(Qt.AlignHCenter)
        layout.addWidget(message)

        # Yes button
        yes_button = QPushButton("Yes")
        yes_button.setFixedHeight(30)
        yes_button.setStyleSheet("background-color: #007aff; color: white; border-radius: 6px; font-weight: bold;")
        yes_button.clicked.connect(self.handle_yes_clicked)
        layout.addWidget(yes_button)

        # “Don't ask again” checkbox
        if(enableCheckBox):
            self.checkbox = QCheckBox(checkBoxText)
            checkbox_layout = QHBoxLayout()
            checkbox_layout.addStretch()
            checkbox_layout.addWidget(self.checkbox)
            checkbox_layout.addStretch()
            layout.addLayout(checkbox_layout)

        self.setLayout(layout)

        self.exec_()
    
    def handle_yes_clicked(self):
        if self.enableCheckBox and self.checkbox.isChecked():
            self.checkbox_selected = True
        else:
            self.checkbox_selected = False
        self.accept()




