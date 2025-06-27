from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from ui.components.CleanTheme import CleanTheme
from ui.components.AnalysisDropdown import AnalysisDropdown
from ui.components.AnalysisButton import AnalysisButton
from ui.components.AnalysisText import AnalysisText


class AdvancedTools(QWidget):
    def __init__(self, items=None, parent=None):
        super().__init__(parent)

        adv_layout = QVBoxLayout(self)

        # the title 
        advanced_label = AnalysisText.create_subtitle("ADVANCED TOOLS")
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
            "Custom Order",
            "GR08MM1305",
            "GR04MM1305",
            "GR10MM0808"
        ]

        # analysis tools dropdown
        analysis_tools_dropdown = AnalysisDropdown(
            self.analysis_tool,
            items=self.analysis_tools_options, 
            parent=self
        )
        adv_layout.addWidget(analysis_tools_dropdown)
        self.analysis_tools_dropdown = analysis_tools_dropdown

        # matrix orientation dropdown
        matrix_orientation_dropdown = AnalysisDropdown(
            self.matrix_orientation,
            items=self.matrix_orientation_options, 
            parent=self
        )
        adv_layout.addWidget(matrix_orientation_dropdown)
        self.matrix_orientation_dropdown = matrix_orientation_dropdown

        # matrix selection dropdown
        matrix_code_dropdown = AnalysisDropdown(
            self.matrix_code,
            items=self.matrix_code_options, 
            parent=self
        )
        adv_layout.addWidget(matrix_code_dropdown)
        self.matrix_code_dropdown = matrix_code_dropdown

        # advanced analysis button
        advanced_analysis_btn = AnalysisButton(
            "Advanced Analysis", 
            lambda: self.show_popup(), 
            parent=self
        )
        adv_layout.addWidget(advanced_analysis_btn, stretch=1)

    def show_popup(self):
        if (self.analysis_tools_dropdown.currentText() == ""):
            self.show_error("Please choose an analysis tool.")
        elif (self.matrix_orientation_dropdown.currentText() == ""):
            self.show_error("Please choose a matrix orientation.")
        elif (self.matrix_code_dropdown.currentText() == ""):
            self.show_error("Please choose a matrix code.")
        else:
            self.show_analysis()

    def show_error(self, message=""):
        QMessageBox.warning(
            self,
            "Invalid advanced analysis selection",
            message,
        )

    def show_analysis(self):
        QMessageBox.information( # doesn't have to be QMessage
            self,
            "Motor Unit Tracking",
            "TODO, task 32 (Seb)",
        )

