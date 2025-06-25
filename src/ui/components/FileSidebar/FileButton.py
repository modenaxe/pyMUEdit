from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize



class FileButton(QPushButton):

# all file actions button styling
    def __init__(self, text):
      super().__init__(text )
      # self.setFont(QFont("Segoe UI", 9))
      self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
      self.setCursor(Qt.CursorShape.PointingHandCursor)
      self.setStyleSheet(
          f"""
          QPushButton {{
              background-color: #495057;
              color: #e9ecee;
              border: none;
              height: 40%;
              max-width: 100%;
              border-radius: 4px;
          }}
          QPushButton:hover {{
              background-color: #e9ecee;
              color: #495057;
          }}
      """
      )
