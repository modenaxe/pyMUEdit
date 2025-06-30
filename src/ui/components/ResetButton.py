from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize, pyqtSignal


class ResetButton(QPushButton):
    """A reset button component that emits a signal when clicked"""
    
    reset_requested = pyqtSignal()  # Signal emitted when reset is requested

    def __init__(self, text="Reset", parent=None):
        """
        Initialize a reset button
        
        Args:
            text (str): Button text (default: "Reset")
            parent (QWidget): Parent widget
        """
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 10, QFont.Bold))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("resetButton")
        
        # Style the reset button with red color to indicate destructive action
        self.setStyleSheet(
            """
            QPushButton#resetButton {
                background-color: #f44336; /* Red color for reset */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton#resetButton:hover {
                background-color: #d32f2f; /* Darker red on hover */
            }
            QPushButton#resetButton:pressed {
                background-color: #b71c1c; /* Even darker red when pressed */
            }
            """
        )
        
        # Connect the button's clicked signal to emit our custom signal
        self.clicked.connect(self.reset_requested.emit) 