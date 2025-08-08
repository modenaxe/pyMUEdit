from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QCheckBox, QDialog, QLabel, QVBoxLayout

from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.PICFunc import compute_deltaf
from ui.components.muAnalysisComponents.AnalysisCheckboxDark import \
    AnalysisCheckboxDark
from ui.components.muAnalysisComponents.AnalysisDropdown import \
    AnalysisLabeledDropdown
from ui.components.muAnalysisComponents.AnalysisDropdownDialog import (
    AnalysisDropdownDialog, AnalysisLabeledDropdownDialog)
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton


class PICDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file = FileUploadFunc.file

        # initialise UI
        self.setWindowTitle("Persistent Inward Currents")
        self.setMinimumWidth(550)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        self.setStyleSheet(
            f"background-color: {CleanTheme.ANALYSIS_DIALOG_BACKGROUND};")
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)

        # Title
        title_label = AnalysisText.create_title_dark(
            "Persistent Inward Currents")
        layout.addWidget(title_label)

        # average method drop down
        self.avg_method_dropdown = AnalysisLabeledDropdownDialog(
            "Average Method",
            items=["Test Unit Average", "All"],
            parent=self,
        )
        self.avg_method_dropdown.setMinimumHeight(32)
        layout.addWidget(self.avg_method_dropdown)

        # normalisation drop down
        self.normalisation_dropdown = AnalysisLabeledDropdownDialog(
            "Normalisation",
            items=["False", "Ctrl Max Desc"],
            parent=self
        )
        self.normalisation_dropdown.setMinimumHeight(32)
        layout.addWidget(self.normalisation_dropdown)

        # Clean selection
        self.clean_checkbox = AnalysisCheckboxDark("Clean")
        self.clean_checkbox.setChecked(True)

        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(15)
        checkbox_layout.addWidget(self.clean_checkbox)

        layout.addLayout(checkbox_layout, stretch=1)

        self.PIC_button = GeneralButton(
            "Compute PIC", lambda: self.computePIC()
        )
        layout.addWidget(self.PIC_button, stretch=1)

    def computePIC(self):
        if self.file is None:
            ErrorDialog("EMG data not loaded.", "Error").exec_()
            return
        normalisation = "False" if self.normalisation_dropdown.get(
        ) == "False" else "ctrl_max_desc"
        avg_method = "all" if self.avg_method_dropdown.get() == "All" else "test_unit_average"
        clean = False if not self.clean_checkbox.checkState() else True

        compute_deltaf(
            average_method=avg_method,
            normalisation=normalisation,
            clean=clean)
