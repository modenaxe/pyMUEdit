from app.FileUploadFunc import FileUploadFunc
from ui.components.FileSidebar.FileButton import FileButton
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
)
from PyQt5.QtGui import QFont

# class containing the file section of the right sidebar
# when button is clicked it calls mu class method, passing instance of the center layout as it needs

class FileSection(QVBoxLayout):
      def __init__(self, sidebar, mu, center):
        super().__init__(sidebar)
      # self.setFont(QFont("Segoe UI", 9))
        title_label = QLabel("File")
        title_label.setStyleSheet(f"color: #e9ecee; border: none")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setObjectName("sidebarTitle")
        self.addWidget(title_label)
        browse_btn = FileButton('Load File')
        browse_btn.clicked.connect(lambda: mu.select_file_button_pushed(center))
        self.addWidget(browse_btn)
        self.addStretch(1)


