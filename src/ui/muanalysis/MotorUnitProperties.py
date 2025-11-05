from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QHBoxLayout,
                             QLineEdit, QVBoxLayout, QWidget)

from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.MUPropertiesFun import MUPropertiesFunc
from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.AnalysisDropdownDialog import \
    AnalysisDropdownDialog
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.PropertiesInnerDialogText import \
    PropertiesInnerDialogText
from ui.muanalysis.ComputeThresholdSection import ComputeThresholdSection

from ui.components import ActionButton
from openhdemg.library import compute_dr


class MotorUnitPropertiesDialog(QWidget):

    """Dialog for entering Motor Unit Properties including MVC value"""

    mvc_updated = pyqtSignal(float)  # Signal emitted when MVC is updated

    def __init__(
            self,
            parent=None,
            analysis_plot=None,
            current_mvc=None,
            emgfile=None):
        super().__init__(parent)
        self.current_mvc = current_mvc
        self.analysis_plot = analysis_plot
        self.emgfile = emgfile
        self.init_ui(MUPropertiesFunc())

    def init_ui(self, func):
        self.setWindowTitle("Motor Unit Properties")
        self.setFixedHeight(300)
        self.setFixedWidth(650)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint
        )
        self.setStyleSheet(
            f"background-color: {CleanTheme.BG_CARD};")
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)
        title = AnalysisText.create_title_dark("Motor Unit Properties")
        layout.addWidget(title)

        # MVC Input Section
        box = QHBoxLayout()
        mvc_label = AnalysisText.create_heading_dark("Enter MVC [N]:")
        layout.addWidget(mvc_label)
        self.mvc_input = PropertiesInnerDialogText(
            "Enter Maximum Voluntary Contraction value..."
        )
        if self.current_mvc is not None:
            self.mvc_input.setText(str(self.current_mvc))
        box.addWidget(mvc_label)
        box.addWidget(self.mvc_input)
        layout.addLayout(box)

        dr_section = QHBoxLayout()

        dr_button = ActionButton(
            "Discharge Rate"
        )
        dr_button.clicked.connect(lambda: self.handle_discharge_rate())
        dr_button.setMinimumHeight(40)
        dr_section.addWidget(dr_button)

        self.dr_event_dropdown = AnalysisDropdownDialog(
            "Event",
            items=["rec", "derec", "rec_derec", "steady", "rec_derec_steady"],
            parent=self,
        )
        self.dr_event_dropdown.setCurrentIndex(0)
        self.dr_event_dropdown.setMinimumHeight(32)
        dr_section.addWidget(self.dr_event_dropdown)

        # Firings at Rec textbox
        self.dr_firings_rec = PropertiesInnerDialogText("Firings at Rec")
        dr_section.addWidget(self.dr_firings_rec)

        # Firings at Start/End Steady textbox
        self.dr_firings_steady = PropertiesInnerDialogText(
            "Firings at Start/End Steady"
        )
        dr_section.addWidget(self.dr_firings_steady)

        # append Compute Threshold section to UI
        compute_threshold = ComputeThresholdSection(func)
        layout.addLayout(compute_threshold)
        layout.addLayout(dr_section)
        func.set_mvc(self.mvc_input)

        basic_prop = MotorUnitPropertiesBasic(func)
        layout.addLayout(basic_prop)
        layout.addStretch(1)

    def handle_discharge_rate(self):
        event = self.dr_event_dropdown.currentText()
        firings_rec = self.dr_firings_rec.text()
        firings_steady = self.dr_firings_steady.text()

        if not event or event == "Event" or not firings_rec or not firings_steady:
            ErrorDialog("Complete all inputs", "Error").exec_()
            return
        try:
            n_firings_RecDerec = int(firings_rec)
            n_firings_steady = int(firings_steady)
        except ValueError:
            ErrorDialog("Firings values must be integers", "Error").exec_()
            return
        # Get EMG file/data context
        if self.emgfile is None:
            ErrorDialog("EMG data not loaded.", "Error").exec_()
            return

        try:
            dr_df = compute_dr(
                emgfile=self.emgfile,
                n_firings_RecDerec=n_firings_RecDerec,
                n_firings_steady=n_firings_steady,
                event_=event,
            )
        except Exception as e:
            ErrorDialog(
                f"Error computing discharge rate: {str(e)}",
                "Error").exec_()
            return
        # Append result to results panel (top of history)
        store.append_analysis_hist(
            f"Discharge Rate (event: {event})", dr_df.to_dict("records")
        )


class MotorUnitPropertiesBasic(QHBoxLayout):

    """Basic Properties analysis layout"""

    def __init__(self, func):
        super().__init__()
        button = ActionButton("Basic Properties")
        button.clicked.connect(
            lambda: func.basic_prop(
                rec_input,
                steady_input
            )
        )
        button.setMinimumHeight(40)
        rec_input = PropertiesInnerDialogText("Firings at Rec")
        steady_input = PropertiesInnerDialogText("Firings at Start/End Steady")
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
        self.setStyleSheet(
            f"""
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
        """
        )


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
        layout.setContentsMargins(0, 0, 0, 0)

        mu_properties_btn = ActionButton("Motor Unit Properties")
        mu_properties_btn.clicked.connect(
            lambda: self.open_mu_properties())
        mu_properties_btn.setMinimumHeight(40)
        layout.addWidget(mu_properties_btn)

    def open_mu_properties(self):
        # Open the Motor Unit Properties dialog
        emgfile = FileUploadFunc.file
        if not emgfile:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        dialog = MotorUnitPropertiesDialog(
            self, self.analysis_plot, self.current_mvc, emgfile=emgfile
        )
        dialog.mvc_updated.connect(self.update_mvc)
        dialog.show()

    def update_mvc(self, mvc_value):
        # Update the MVC value
        self.current_mvc = mvc_value
        print(f"MVC updated to: {mvc_value} N")
        self.mvc_updated.emit(mvc_value)

    def get_mvc(self):
        # Get the current MVC value
        return self.current_mvc
