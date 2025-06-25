from app.MUAnalysisFunc import MUAnalysisFunc
from ui.components.FileSidebar.FileButton import FileButton
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
)
from PyQt5.QtGui import QFont

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


