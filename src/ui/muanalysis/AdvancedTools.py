from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QMessageBox, QPushButton,
                             QVBoxLayout, QWidget)

from app.muAnalysisFunctions.ConductionVelocityDialog import \
    ConductionVelocityDialog
from app.muAnalysisFunctions.MotorUnitTrackingDialog import \
    MotorUnitTrackingDialog
from ui.components.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.AnalysisDropdown import \
    AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.SubsectionTitle import SubsectionTitle
from ui.muanalysis.PIC import PICDialog


class AdvancedTools(QWidget):
    """Dialog and drops down for advanced tool analysis"""

    def __init__(self, items=None, parent=None):
        super().__init__(parent)

        adv_layout = QVBoxLayout(self)
        adv_layout.setContentsMargins(10, 0, 10, 0)
        # the title
        advanced_label = SubsectionTitle("ADVANCED TOOLS")
        adv_layout.addWidget(advanced_label)

        # declaring the dropdown options
        self.analysis_tool = "Analysis Tool"
        self.analysis_tools_options = [
            "Motor Unit Tracking",
            "Conduction Velocity Estimation",
            "Persistent Inward Currents",
        ]
        self.matrix_orientation = "Matrix Orientation"
        self.matrix_orientation_options = [
            "0",
            "180",
        ]
        self.matrix_code = "Matrix Code"
        self.matrix_code_options = [
            "None",
            "GR08MM1305",
            "GR04MM1305",
            "GR10MM0808",
        ]

        # analysis tools dropdown
        analysis_tools_dropdown = AnalysisDropdown(
            self.analysis_tool, items=self.analysis_tools_options, parent=self
        )
        adv_layout.addWidget(analysis_tools_dropdown)
        self.analysis_tools_dropdown = analysis_tools_dropdown

        # matrix orientation dropdown
        matrix_orientation_dropdown = AnalysisDropdown(
            self.matrix_orientation, items=self.matrix_orientation_options, parent=self)
        adv_layout.addWidget(matrix_orientation_dropdown)
        self.matrix_orientation_dropdown = matrix_orientation_dropdown

        # matrix selection dropdown
        matrix_code_dropdown = AnalysisDropdown(
            self.matrix_code, items=self.matrix_code_options, parent=self
        )
        adv_layout.addWidget(matrix_code_dropdown)
        self.matrix_code_dropdown = matrix_code_dropdown

        # advanced analysis button
        advanced_analysis_btn = GeneralButton(
            "Advanced Analysis", lambda: self.show_popup(), parent=self
        )
        adv_layout.addWidget(advanced_analysis_btn, stretch=1)

        self.analysis_tools_dropdown.currentTextChanged.connect(
            self.on_PIC_selection)

    def on_PIC_selection(self):
        """
        Enable or disable matrix configuration dropdowns based on the current
        selection in the analysis tools dropdown.
        """
        disable = (self.analysis_tools_dropdown.currentText()
                   == "Persistent Inward Currents")
        self.matrix_orientation_dropdown.setDisabled(disable)
        self.matrix_code_dropdown.setDisabled(disable)

    def show_popup(self):
        if self.analysis_tools_dropdown.currentText() == "Persistent Inward Currents":
            self.show_analysis()
        elif self.analysis_tools_dropdown.currentText() == "":
            self.show_error("Please choose an analysis tool.")
        elif self.matrix_orientation_dropdown.currentText() == "":
            self.show_error("Please choose a matrix orientation.")
        elif self.matrix_code_dropdown.currentText() == "":
            self.show_error("Please choose a matrix code.")
        else:
            self.show_analysis()

    def show_error(self, message=""):
        ErrorDialog(message, "Error").exec_()

    def show_analysis(self):
        selected_tool = self.analysis_tools_dropdown.currentText()
        if selected_tool == "Motor Unit Tracking":
            dialog = MotorUnitTrackingDialog(
                parent=self,
                matrix_orientation=self.matrix_orientation_dropdown.currentText(),
                matrix_code=self.matrix_code_dropdown.currentText(),
            )
            dialog.exec_()
        elif selected_tool == "Conduction Velocity Estimation":
            dialog = ConductionVelocityDialog(self)
            dialog.exec_()
        elif selected_tool == "Persistent Inward Currents":
            dialog = PICDialog(self)
            dialog.exec()
        else:
            ErrorDialog("Unknown analysis tool.", "Error").exec_()
