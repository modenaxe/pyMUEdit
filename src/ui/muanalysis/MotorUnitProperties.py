from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout,
    QHBoxLayout, 
    QPushButton, 
    QLineEdit,
    QDialog,
    QComboBox
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, pyqtSignal
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from app.muAnalysisFunctions.MUPropertiesFun import MUPropertiesFunc
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.PropertiesInnerDialogButton import PropertiesInnerDialogButton
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown

class MotorUnitPropertiesDialog(QDialog):

    """Dialog for entering Motor Unit Properties including MVC value"""

    mvc_updated = pyqtSignal(float)  # Signal emitted when MVC is updated

    def __init__(self, parent=None, analysis_plot=None, current_mvc=None):
        super().__init__(parent)
        self.current_mvc = current_mvc
        # passing instance of MUPropertiesFunc to be used in parts of dialog
        self.analysis_plot = analysis_plot
        self.init_ui(MUPropertiesFunc())

    def init_ui(self, func):
        self.setWindowTitle("Motor Unit Properties")
        self.setMinimumWidth(550)
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(f"background-color: {CleanTheme.ANALYSIS_BG_SIDEBAR};")
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)
        # Title
        title_label = QLabel("Motor Unit Properties")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {CleanTheme.ANALYSIS_BG_CARD};")
        layout.addWidget(title_label)

        # MVC Input Section
        box = QHBoxLayout()
        mvc_label = QLabel("Enter MVC [N]:")
        mvc_label.setFont(QFont("Arial", 12, QFont.Bold))
        mvc_label.setStyleSheet(f"color: {CleanTheme.ANALYSIS_BG_CARD};")
        self.mvc_input = PropertiesInnerDialogText("Enter Maximum Voluntary Contraction value...")
        if self.current_mvc is not None:
            self.mvc_input.setText(str(self.current_mvc))
            print(str(self.current_mvc))
        box.addWidget(mvc_label)
        box.addWidget(self.mvc_input)
    
        func.set_mvc(self.mvc_input)
    
        # compute threshold
        layout.addLayout(box)
        compute_threshold = ComputeThresholdSection(func)
        layout.addLayout(compute_threshold)
        
        #basic properties
        layout.addLayout(box)
        basic_prop = MotorUnitPropertiesBasic(self.analysis_plot, func, self)
        layout.addLayout(basic_prop)

    def save_mvc(self):
        pass

# basic properties section
# has firing at rec, firing at start/end input and basic properties button
# button leads to functions found in app.MUPropertiesFun
class MotorUnitPropertiesBasic(QHBoxLayout):

    """Basic Properties analysis layout"""

    def __init__(self, analysis_plot, func, over):
        super().__init__()
        button = GeneralButton("Basic Properties", lambda: func.basic_prop(analysis_plot, rec_input, steady_input, over))
        rec_input = PropertiesInnerDialogText('Firings at Rec')
        steady_input = PropertiesInnerDialogText('Firings at Start/End Steady')
        self.addWidget(button)
        self.addWidget(rec_input)
        self.addWidget(steady_input)

# general class for any inner inputs inside dialog
class PropertiesInnerDialogText(QLineEdit):

    """Inputs within Motor Unit Properties dialogs"""

    def __init__(self, text):
        super().__init__()
        self.setMinimumHeight(32)
        self.setPlaceholderText(text)
        self.setFont(QFont("Arial", 11))
        self.setStyleSheet(f"""
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
        
# class that holds the inputs to compute threshold
class ComputeThresholdSection(QHBoxLayout):
    def __init__(self, func):
        super().__init__()
        event_ = AnalysisDropdown("Event", items=['rt', 'dert', 'rt_dert'])
        type_ =  AnalysisDropdown("Type", items=['abs', 'rel', 'abs_rel'])
        button = GeneralButton("Compute Thresholds", lambda: func.compute_thresh(event_.get_value(), type_.get_value()))

        self.addWidget(button)
        self.addWidget(event_)
        self.addWidget(type_)
        

class MotorUnitPropertiesButton(QWidget):

    """Button widget for opening Motor Unit Properties dialog"""
    
    mvc_updated = pyqtSignal(float)  # Signal emitted when MVC is updated
    
    def __init__(self, analysis_plot, parent=None):
        super().__init__(parent)
        self.current_mvc = None
        self.analysis_plot = analysis_plot
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,0,10,0)
        # Subtitle
        subtitle_label = AnalysisText.create_subtitle("MOTOR UNIT ANALYSIS")
        subtitle_label.setObjectName("motorUnitAnalysisSubTitle")
        layout.addWidget(subtitle_label)

        mu_properties_btn = GeneralButton("Motor Unit Properties", lambda: self.open_mu_properties())
        layout.addWidget(mu_properties_btn)
        
    def open_mu_properties(self):
        # Open the Motor Unit Properties dialog
        dialog = MotorUnitPropertiesDialog(self, self.analysis_plot, self.current_mvc)
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
