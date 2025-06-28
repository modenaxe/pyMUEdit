from app.FileUploadFunc import FileUploadFunc
from ui.components.FileSidebar.FileButton import FileButton
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QFrame
)
from PyQt5.QtGui import QFont

# class containing the file section of the right sidebar
# when button is clicked it calls mu class method, passing instance of the center layout as it needs

class FileSection(QFrame):
      def __init__(self, sidebar, mu, center):
        super().__init__(sidebar)
      # self.setFont(QFont("Segoe UI", 9))
        self.setObjectName("FileSection")
        
        layout = QVBoxLayout(self)

        title_label = QLabel("File")
        title_label.setStyleSheet(f"color: #343a40; border: none")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setObjectName("sidebarTitle")
        
        browse_btn = FileButton('Load File')
        browse_btn.clicked.connect(lambda: mu.select_file_button_pushed(center))
        
        layout.addWidget(title_label)
        layout.addWidget(browse_btn)
        layout.addStretch(1)

