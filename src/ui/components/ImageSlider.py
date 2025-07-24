import os
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from ui.components.CircleButton import CircleButton

class ImageSlider(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(480, 480)

        # image path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.images = {
            "step1": os.path.abspath(os.path.join(current_dir, "../../public/error_icon.png")),
            "step2": os.path.abspath(os.path.join(current_dir, "../../public/success_icon.png")),
            "step3": os.path.abspath(os.path.join(current_dir, "../../public/question_icon.png")),
        }

        self.image_label = QLabel("Let's start\nClick button show image")
        self.image_label.setAlignment(Qt.AlignCenter)

        # The list of all buttons
        self.buttons = []

        # button group
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(100, 10, 100, 10)
        for label, path in self.images.items():
            button = CircleButton(diameter=15)
            self.buttons.append(button)
            button.setToolTip(label)
            button.clicked.connect(lambda _, p=path, btn=button: self.on_button_clicked(p, btn)) 
            button_layout.addWidget(button)
            
        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        layout.addLayout(button_layout)

    def on_button_clicked(self, image_path, clicked_button):
        for btn in self.buttons:
            if btn != clicked_button:
                btn.setChecked(False)

            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.image_label.setText("fail to load image")
            else:
                self.image_label.setPixmap(pixmap.scaled(455, 455, Qt.KeepAspectRatio, Qt.SmoothTransformation))

