from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget)
from app.muAnalysisFunctions.ConductionVelocityDialog import \
    ConductionVelocityDialog
from app.muAnalysisFunctions.MotorUnitTrackingDialog import \
    MotorUnitTrackingDialog
from ui.components.muAnalysisComponents.AnalysisDropdown import \
    AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components import ActionButton
from ui.muanalysis.PIC import PICDialog


class AdvancedTools(QWidget):
    """Dialog and drops down for advanced tool analysis"""

    def __init__(self, parent=None):
        super().__init__(parent)

        adv_layout = QVBoxLayout(self)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        adv_layout.setSpacing(8)

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
        analysis_tools_dropdown.setCurrentIndex(0)
        adv_layout.addWidget(analysis_tools_dropdown)
        self.analysis_tools_dropdown = analysis_tools_dropdown

        # matrix orientation dropdown
        matrix_orientation_dropdown = AnalysisDropdown(
            self.matrix_orientation, items=self.matrix_orientation_options, parent=self)
        adv_layout.addWidget(matrix_orientation_dropdown)
        self.matrix_orientation_dropdown = matrix_orientation_dropdown
        self.matrix_orientation_dropdown.setCurrentIndex(1)

        # matrix selection dropdown
        matrix_code_dropdown = AnalysisDropdown(
            self.matrix_code, items=self.matrix_code_options, parent=self
        )
        matrix_code_dropdown.setCurrentIndex(1)
        adv_layout.addWidget(matrix_code_dropdown)
        self.matrix_code_dropdown = matrix_code_dropdown
        self.matrix_code_dropdown.currentTextChanged.connect(
            self.on_matrix_code_selection)

        # Column and Rows input for None type matrix code
        channels_section = QWidget()
        channels_layout = QHBoxLayout(channels_section)
        self.rows_input = AnalysisInput(placeholder="Rows")
        self.columns_input = AnalysisInput(placeholder="Columns")
        channels_layout.addWidget(self.rows_input)
        channels_layout.addWidget(self.columns_input)
        adv_layout.addWidget(channels_section)

        self.rows_input.hide()
        self.columns_input.hide()

        # advanced analysis button
        advanced_analysis_btn = ActionButton("Advanced Analysis", parent=self)
        advanced_analysis_btn.clicked.connect(lambda: self.show_popup())
        advanced_analysis_btn.setMinimumHeight(40)
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

    def on_matrix_code_selection(self):
        """
        Show or hide rows and columns input fields based on the selected
        matrix code.
        """
        if self.matrix_code_dropdown.currentText() == "None":
            self.rows_input.show()
            self.columns_input.show()
        else:
            self.rows_input.hide()
            self.columns_input.hide()

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
            if self.matrix_code_dropdown.currentText() == "None":
                self.rows = self.rows_input.get()
                self.columns = self.columns_input.get()
                if not self.rows_input.get() or not self.columns_input.get():
                    self.show_error("Please enter both rows and columns for the matrix.")
                else:
                    try:
                        self.rows = int(self.rows)
                        self.columns = int(self.columns)
                        self.show_analysis()
                    except:
                        self.show_error("Rows and Columns must be integers.")
            else:
                self.show_analysis()

    def show_error(self, message=""):
        ErrorDialog(message, "Error").exec_()

    def show_analysis(self):
        selected_tool = self.analysis_tools_dropdown.currentText()

        matrix_orientation_string = self.matrix_orientation_dropdown.currentText()
        matrix_code_string = self.matrix_code_dropdown.currentText()

        matrix_orientation = int(matrix_orientation_string) if matrix_orientation_string else 180
        matrix_code = None if matrix_code_string in (None, "", "None") else matrix_code_string

        rows = self.rows if matrix_code is None else None
        columns = self.columns if matrix_code is None else None

        if selected_tool == "Motor Unit Tracking":
            dialog = MotorUnitTrackingDialog(
                parent=self,
                matrix_orientation=matrix_orientation,
                matrix_code=matrix_code,
                n_rows=rows,
                n_cols=columns
            )
            dialog.exec_()
        elif selected_tool == "Conduction Velocity Estimation":
            dialog = ConductionVelocityDialog(
                parent=self,
                matrix_orientation=matrix_orientation,
                matrix_code=matrix_code,
                n_rows=rows,
                n_cols=columns
            )
            dialog.exec_()
        elif selected_tool == "Persistent Inward Currents":
            dialog = PICDialog(self)
            dialog.exec()
        else:
            ErrorDialog("Unknown analysis tool.", "Error").exec_()
