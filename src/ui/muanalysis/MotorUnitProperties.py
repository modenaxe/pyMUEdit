from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout, 
    QPushButton, 
    QLineEdit,
    QDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
from ui.components.CleanTheme import CleanTheme


class MotorUnitPropertiesDialog(QDialog):
    # Dialog for entering Motor Unit Properties including MVC value

    mvc_updated = pyqtSignal(float)  # Signal emitted when MVC is updated

    def __init__(self, parent=None, current_mvc=None):
        super().__init__(parent)
        self.current_mvc = current_mvc
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Motor Unit Properties")
        self.setMinimumWidth(550)
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(f"background-color: {CleanTheme.ANALYSIS_BG_CARD};")
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)
        # Title
        title_label = QLabel("Motor Unit Properties")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        layout.addWidget(title_label)
        # MVC Input Section
        mvc_label = QLabel("Enter MVC [N]:")
        mvc_label.setFont(QFont("Arial", 12, QFont.Bold))
        mvc_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        layout.addWidget(mvc_label)
        self.mvc_input = QLineEdit()
        self.mvc_input.setMinimumHeight(32)
        self.mvc_input.setPlaceholderText("Enter Maximum Voluntary Contraction value...")
        self.mvc_input.setFont(QFont("Arial", 11))
        self.mvc_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                border: 2px solid {CleanTheme.BORDER};
                border-radius: 6px;
                background-color: {CleanTheme.ANALYSIS_BG_CARD};
                color: {CleanTheme.TEXT_PRIMARY};
                font-size: 11pt;
            }}
            QLineEdit:focus {{
                border-color: {CleanTheme.ANALYSIS_BG_BUTTON};
            }}
        """)
        if self.current_mvc is not None:
            self.mvc_input.setText(str(self.current_mvc))
        layout.addWidget(self.mvc_input)

    def save_mvc(self):
        pass


class MotorUnitPropertiesButton(QWidget):
    """Button widget for opening Motor Unit Properties dialog"""
    
    mvc_updated = pyqtSignal(float)  # Signal emitted when MVC is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mvc = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Subtitle
        subtitle_label = QLabel("MOTOR UNIT ANALYSIS")
        subtitle_label.setObjectName("motorUnitAnalysisSubTitle")
        subtitle_label.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
            margin: 0px;
            """
        )
        subtitle_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(subtitle_label)
        
        # Motor Unit Properties button
        mu_properties_btn = QPushButton("Motor Unit Properties")
        mu_properties_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mu_properties_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {CleanTheme.ANALYSIS_BG_BUTTON};
                color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                height: 40px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                color: {CleanTheme.ANALYSIS_BG_BUTTON};
            }}
        """
        )
        mu_properties_btn.clicked.connect(self.open_mu_properties)
        layout.addWidget(mu_properties_btn)
        layout.setAlignment(mu_properties_btn, Qt.AlignTop)
        
    def open_mu_properties(self):
        # Open the Motor Unit Properties dialog
        dialog = MotorUnitPropertiesDialog(self, self.current_mvc)
        dialog.mvc_updated.connect(self.update_mvc)
        dialog.exec_()
        
    def update_mvc(self, mvc_value):
        # Update the MVC value
        self.current_mvc = mvc_value
        print(f"MVC updated to: {mvc_value} N")
        self.mvc_updated.emit(mvc_value)
        
    def get_mvc(self):
        # Get the current MVC value
        return self.current_mvc 