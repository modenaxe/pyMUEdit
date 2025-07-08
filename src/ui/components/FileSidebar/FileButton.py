from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize
from ui.components.CleanTheme import CleanTheme



class FileButton(QPushButton):

# all file actions button styling
    def __init__(self, text):
      super().__init__(text )
      self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
      self.setCursor(Qt.CursorShape.PointingHandCursor)
      self.setStyleSheet(
          f"""
          QPushButton {{
            background-color: {CleanTheme.ANALYSIS_BG_BUTTON};
            color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
            border: none;
            height: 40%;
            max-width: 100%;
            border-radius: 4px;
          }}
          QPushButton:hover {{
            background-color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
            color: {CleanTheme.ANALYSIS_BG_BUTTON};
          }}
      """
      )
