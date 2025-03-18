import os
import sys
import numpy as np
import scipy.io as sio
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QFileDialog,
    QDoubleSpinBox,
    QGridLayout,
    QProgressDialog,
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import RectangleSelector
from matplotlib.backend_bases import MouseButton
from typing import Dict, Any

# Import the implemented modules
from lib.bandpassingals import bandpassingals
from lib.batchprocessfilters import batchprocessfilters
from lib.calcSIL import calcSIL
from lib.demean import demean
from lib.extend import extend
from lib.fixedpointalg import fixedpointalg
from lib.formatsignalHDEMG import formatsignalHDEMG
from lib.getspikes import getspikes
from lib.minimizeCOVISI import minimizeCOVISI
from lib.notchsignals import notchsignals
from lib.openIntan import openIntan
from lib.openOEphys import openOEphys
from lib.OpenOTB4 import openOTB4
from lib.openOTBplus import openOTBplus
from lib.pcaesig import pcaesig
from lib.peeloff import peeloff
from lib.refineMUs import refineMUs
from lib.remduplicates import remduplicates
from lib.remoutliers import remoutliers
from lib.segmentsession import SegmentSession
from lib.segmenttargets import segmenttargets
from lib.whiteesig import whiteesig


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#262626")
        self.axes.set_facecolor("#262626")
        self.axes.xaxis.label.set_color("#f0f0f0")
        self.axes.yaxis.label.set_color("#f0f0f0")
        self.axes.tick_params(colors="#f0f0f0", which="both")
        super(MplCanvas, self).__init__(self.fig)


class MUedit(QMainWindow):
    def __init__(self):
        super().__init__()

        self.filename = None
        self.pathname = None
        self.filename2 = None
        self.pathname2 = None
        self.MUdecomp = {"config": None}
        self.Configuration = None
        self.MUedition = None
        self.Backup = {"lock": 0}
        self.graphstart = None
        self.graphend = None
        self.roi = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MUedit")
        self.setGeometry(100, 100, 1500, 850)
        self.setStyleSheet("background-color: #262626;")

        # Create tabs dropdown
        self.tabs = QComboBox(self)
        self.tabs.addItems(["DECOMPOSITION", "MANUAL EDITING"])
        self.tabs.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 24pt; font-weight: bold;"
        )
        self.tabs.setGeometry(0, 810, 400, 40)
        self.tabs.currentTextChanged.connect(self.tabs_value_changed)

        # Create panels
        self.panel = QWidget(self)
        self.panel.setGeometry(0, 0, 400, 810)
        self.panel.setStyleSheet("background-color: #262626;")

        self.panel_2 = QWidget(self)
        self.panel_2.setGeometry(400, 0, 1100, 850)
        self.panel_2.setStyleSheet("background-color: #262626;")

        self.panel_3 = QWidget(self)
        self.panel_3.setGeometry(400, 0, 1100, 850)
        self.panel_3.setStyleSheet("background-color: #262626;")
        self.panel_3.setVisible(False)

        self.panel_4 = QWidget(self)
        self.panel_4.setGeometry(0, 0, 400, 810)
        self.panel_4.setStyleSheet("background-color: #262626;")
        self.panel_4.setVisible(False)

        # Set up decomposition panel
        self.setup_decomposition_panel()

        # Set up results panel
        self.setup_results_panel()

    def setup_decomposition_panel(self):
        layout = QVBoxLayout(self.panel)

        # Filename field and select button
        file_layout = QHBoxLayout()
        self.edit_field_saving_3 = QLineEdit("File name")
        self.edit_field_saving_3.setReadOnly(True)
        self.edit_field_saving_3.setStyleSheet(
            "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        self.select_file_button = QPushButton("Select file")
        self.select_file_button.setStyleSheet(
            "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.select_file_button.clicked.connect(self.select_file_button_pushed)

        file_layout.addWidget(self.edit_field_saving_3)
        file_layout.addWidget(self.select_file_button)

        # Config and segment buttons
        config_layout = QHBoxLayout()
        self.set_configuration_button = QPushButton("Set configuration")
        self.set_configuration_button.setStyleSheet(
            "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.set_configuration_button.clicked.connect(self.set_configuration_button_pushed)

        self.segment_session_button = QPushButton("Segment session")
        self.segment_session_button.setStyleSheet(
            "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.segment_session_button.clicked.connect(self.segment_session_button_pushed)

        config_layout.addWidget(self.set_configuration_button)
        config_layout.addWidget(self.segment_session_button)

        # Parameter controls
        params_layout = QGridLayout()

        # Reference dropdown
        self.reference_label = QLabel("Reference")
        self.reference_label.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.reference_dropdown = QComboBox()
        self.reference_dropdown.addItems(["Target", "EMG amplitude"])
        self.reference_dropdown.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # Check EMG dropdown
        self.check_emg_label = QLabel("Check EMG")
        self.check_emg_label.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.check_emg_dropdown = QComboBox()
        self.check_emg_dropdown.addItems(["Yes", "No"])
        self.check_emg_dropdown.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # Peeloff dropdown
        self.peeloff_label = QLabel("Peeloff")
        self.peeloff_label.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.peeloff_dropdown = QComboBox()
        self.peeloff_dropdown.addItems(["Yes", "No"])
        self.peeloff_dropdown.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # CoV filter dropdown
        self.cov_filter_label = QLabel("CoV filter")
        self.cov_filter_label.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.cov_filter_dropdown = QComboBox()
        self.cov_filter_dropdown.addItems(["Yes", "No"])
        self.cov_filter_dropdown.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # Initialisation dropdown
        self.initialisation_label = QLabel("Initialisation")
        self.initialisation_label.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.initialisation_dropdown = QComboBox()
        self.initialisation_dropdown.addItems(["EMG max", "Random"])
        self.initialisation_dropdown.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # Refine MUs dropdown
        self.refine_mus_label = QLabel("Refine MUs")
        self.refine_mus_label.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.refine_mus_dropdown = QComboBox()
        self.refine_mus_dropdown.addItems(["Yes", "No"])
        self.refine_mus_dropdown.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # Contrast function dropdown
        self.contrast_function_label = QLabel("Contrast function")
        self.contrast_function_label.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.contrast_function_dropdown = QComboBox()
        self.contrast_function_dropdown.addItems(["skew", "kurtosis", "logcosh"])
        self.contrast_function_dropdown.setStyleSheet(
            "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # Numerical parameters
        self.number_iterations_label = QLabel("Number of iterations")
        self.number_iterations_label.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.number_iterations_field = QSpinBox()
        self.number_iterations_field.setRange(1, 1000)
        self.number_iterations_field.setValue(150)
        self.number_iterations_field.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        self.number_windows_label = QLabel("Number of windows")
        self.number_windows_label.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.number_windows_field = QSpinBox()
        self.number_windows_field.setRange(1, 100)
        self.number_windows_field.setValue(1)
        self.number_windows_field.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        self.threshold_target_label = QLabel("Threshold target")
        self.threshold_target_label.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.threshold_target_field = QDoubleSpinBox()
        self.threshold_target_field.setRange(0, 1)
        self.threshold_target_field.setValue(0.9)
        self.threshold_target_field.setSingleStep(0.1)
        self.threshold_target_field.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        self.nb_extended_channels_label = QLabel("Nb of extended channels")
        self.nb_extended_channels_label.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.nb_extended_channels_field = QSpinBox()
        self.nb_extended_channels_field.setRange(1, 10000)
        self.nb_extended_channels_field.setValue(1000)
        self.nb_extended_channels_field.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        self.duplicate_threshold_label = QLabel("Duplicate threshold")
        self.duplicate_threshold_label.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.duplicate_threshold_field = QDoubleSpinBox()
        self.duplicate_threshold_field.setRange(0, 1)
        self.duplicate_threshold_field.setValue(0.3)
        self.duplicate_threshold_field.setSingleStep(0.1)
        self.duplicate_threshold_field.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        self.sil_threshold_label = QLabel("SIL threshold")
        self.sil_threshold_label.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.sil_threshold_field = QDoubleSpinBox()
        self.sil_threshold_field.setRange(0, 1)
        self.sil_threshold_field.setValue(0.9)
        self.sil_threshold_field.setSingleStep(0.1)
        self.sil_threshold_field.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        self.cov_threshold_label = QLabel("COV threshold")
        self.cov_threshold_label.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )
        self.cov_threshold_field = QDoubleSpinBox()
        self.cov_threshold_field.setRange(0, 1)
        self.cov_threshold_field.setValue(0.5)
        self.cov_threshold_field.setSingleStep(0.1)
        self.cov_threshold_field.setStyleSheet(
            "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
        )

        # Add parameters to grid
        params_layout.addWidget(self.reference_label, 0, 0)
        params_layout.addWidget(self.reference_dropdown, 0, 1)
        params_layout.addWidget(self.check_emg_label, 1, 0)
        params_layout.addWidget(self.check_emg_dropdown, 1, 1)
        params_layout.addWidget(self.contrast_function_label, 2, 0)
        params_layout.addWidget(self.contrast_function_dropdown, 2, 1)
        params_layout.addWidget(self.initialisation_label, 3, 0)
        params_layout.addWidget(self.initialisation_dropdown, 3, 1)
        params_layout.addWidget(self.cov_filter_label, 4, 0)
        params_layout.addWidget(self.cov_filter_dropdown, 4, 1)
        params_layout.addWidget(self.peeloff_label, 5, 0)
        params_layout.addWidget(self.peeloff_dropdown, 5, 1)
        params_layout.addWidget(self.refine_mus_label, 6, 0)
        params_layout.addWidget(self.refine_mus_dropdown, 6, 1)

        params_layout.addWidget(self.number_iterations_label, 7, 0)
        params_layout.addWidget(self.number_iterations_field, 7, 1)
        params_layout.addWidget(self.number_windows_label, 8, 0)
        params_layout.addWidget(self.number_windows_field, 8, 1)
        params_layout.addWidget(self.threshold_target_label, 9, 0)
        params_layout.addWidget(self.threshold_target_field, 9, 1)
        params_layout.addWidget(self.nb_extended_channels_label, 10, 0)
        params_layout.addWidget(self.nb_extended_channels_field, 10, 1)
        params_layout.addWidget(self.duplicate_threshold_label, 11, 0)
        params_layout.addWidget(self.duplicate_threshold_field, 11, 1)
        params_layout.addWidget(self.sil_threshold_label, 12, 0)
        params_layout.addWidget(self.sil_threshold_field, 12, 1)
        params_layout.addWidget(self.cov_threshold_label, 13, 0)
        params_layout.addWidget(self.cov_threshold_field, 13, 1)

        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;"
        )
        self.start_button.clicked.connect(self.start_button_pushed)

        # Add layouts to main layout
        layout.addLayout(file_layout)
        layout.addLayout(config_layout)
        layout.addLayout(params_layout)
        layout.addWidget(self.start_button)
        layout.addStretch()

    def setup_results_panel(self):
        layout = QVBoxLayout(self.panel_2)

        # Create edit field
        self.edit_field = QLineEdit()
        self.edit_field.setStyleSheet(
            "color: #ffffff; background-color: #262626; font-family: 'Poppins'; font-size: 24pt; font-weight: bold;"
        )
        self.edit_field.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create plot areas
        self.ui_axes_decomp_2 = MplCanvas(self, width=5, height=4)
        self.ui_axes_decomp_2.axes.set_xlabel("Time (s)")
        self.ui_axes_decomp_2.axes.set_ylabel("Reference")

        self.ui_axes_decomp_1 = MplCanvas(self, width=5, height=4)
        self.ui_axes_decomp_1.axes.set_xlabel("Time (s)")
        self.ui_axes_decomp_1.axes.set_ylabel("Pulse train")

        # Add widgets to layout
        layout.addWidget(self.edit_field)
        layout.addWidget(self.ui_axes_decomp_2)
        layout.addWidget(self.ui_axes_decomp_1)

    # Event handlers
    def tabs_value_changed(self, value):
        if value == "DECOMPOSITION":
            self.panel.setVisible(True)
            self.panel_4.setVisible(False)
            self.panel_3.setVisible(False)
            self.panel_2.setVisible(True)
        else:
            self.panel.setVisible(False)
            self.panel_4.setVisible(True)
            self.panel_3.setVisible(True)
            self.panel_2.setVisible(False)

    def select_file_button_pushed(self):
        file, path = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
        if file:
            self.filename = os.path.basename(file)
            self.pathname = os.path.dirname(file) + "/"
            self.edit_field_saving_3.setText(self.filename)

            self.select_file_button.setStyleSheet(
                "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
            )
            self.set_configuration_button.setStyleSheet(
                "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
            )
            self.segment_session_button.setStyleSheet(
                "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
            )
            self.start_button.setStyleSheet(
                "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;"
            )
            self.edit_field.setText(" ")

            # Load files
            ext = os.path.splitext(self.filename)[1]
            if ext == ".otb+":  # OT Biolab+
                self.MUdecomp["config"], signal = openOTBplus(self.pathname, self.filename, 1)
                if self.MUdecomp["config"]:
                    self.MUdecomp["config"].hide()
                    self.set_configuration_button.setEnabled(True)
            # elif ext == ".mat":
            #     file_data = sio.loadmat(os.path.join(self.pathname, self.filename))
            #     signal = file_data["signal"]
            #     self.set_configuration_button.setEnabled(False)
            # elif ext == ".otb4":  # OT Biolab24
            #     self.MUdecomp["config"], signal = openOTB4(self.pathname, self.filename, 0)
            #     if self.MUdecomp["config"]:
            #         self.MUdecomp["config"].hide()
            #         self.set_configuration_button.setEnabled(True)
            # elif ext == ".rhd":  # RHD Intan Tech
            #     self.MUdecomp["config"], signal = openIntan(self.pathname, self.filename, 1)
            #     if self.MUdecomp["config"]:
            #         self.MUdecomp["config"].hide()
            #         self.set_configuration_button.setEnabled(True)
            # elif ext == ".oebin":  # Open Ephys GUI
            #     self.MUdecomp["config"], signal = openOEphys(self.pathname, self.filename, 1)
            #     if self.MUdecomp["config"]:
            #         self.MUdecomp["config"].hide()
            #         self.set_configuration_button.setEnabled(True)

            self.reference_dropdown.clear()

            # Update the list of signals for reference
            if "auxiliaryname" in signal:
                self.reference_dropdown.addItem("EMG amplitude")
                for name in signal["auxiliaryname"]:
                    self.reference_dropdown.addItem(name)
            elif "target" in signal:
                if isinstance(signal["path"], np.ndarray) and isinstance(signal["target"], np.ndarray):
                    path_reshaped = signal["path"].reshape(1, -1) if signal["path"].ndim == 1 else signal["path"]
                    target_reshaped = (
                        signal["target"].reshape(1, -1) if signal["target"].ndim == 1 else signal["target"]
                    )
                    signal["auxiliary"] = np.vstack((path_reshaped, target_reshaped))
                else:
                    signal["auxiliary"] = np.vstack((np.array([signal["path"]]), np.array([signal["target"]])))

                signal["auxiliaryname"] = ["Path", "Target"]
                self.reference_dropdown.addItem("EMG amplitude")
                for name in signal["auxiliaryname"]:
                    self.reference_dropdown.addItem(name)
            else:
                self.reference_dropdown.addItem("EMG amplitude")

            savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
            sio.savemat(savename, {"signal": signal}, do_compression=True)
            self.select_file_button.setStyleSheet(
                "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
            )
            self.edit_field.setText("Data loaded")

    def set_configuration_button_pushed(self):
        if self.MUdecomp["config"]:
            if self.pathname is not None and self.filename is not None:
                self.MUdecomp["config"].pathname.setText(self.pathname + self.filename + "_decomp.mat")
            self.MUdecomp["config"].show()
            self.set_configuration_button.setStyleSheet(
                "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
            )

    def segment_session_button_pushed(self):
        self.segment_session = SegmentSession()

        if self.pathname is not None and self.filename is not None:
            self.segment_session.pathname.setText(self.pathname + self.filename + "_decomp.mat")

        # Setup the dropdown contents before setting the current item
        self.segment_session.reference_dropdown.clear()
        for i in range(self.reference_dropdown.count()):
            self.segment_session.reference_dropdown.addItem(self.reference_dropdown.itemText(i))

        try:
            if self.segment_session.pathname.text():
                self.segment_session.file = sio.loadmat(self.segment_session.pathname.text())
        except Exception as e:
            print(f"Warning: Could not load file: {e}")

        # Set current text after file is loaded
        self.segment_session.reference_dropdown.setCurrentText(self.reference_dropdown.currentText())

        # Show the window
        self.segment_session.show()

        # Update button appearance
        self.segment_session_button.setStyleSheet(
            "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
        )

    def set_axis_colors(self, ax, color, axis="both"):
        # X-axis
        if axis in ["x", "both"]:
            ax.xaxis.label.set_color(color)
            ax.tick_params(axis="x", colors=color)
            ax.spines["bottom"].set_color(color)

        # Y-axis
        if axis in ["y", "both"]:
            ax.yaxis.label.set_color(color)
            ax.tick_params(axis="y", colors=color)
            ax.spines["left"].set_color(color)

    def start_button_pushed(self):
        # NOT WORKING RN
        self.set_axis_colors(self.ui_axes_decomp_2.axes, color="#f0f0f0")

        if self.check_emg_dropdown.currentText() == "Yes":
            parameters: Dict[str, Any] = {"checkEMG": 1}
        else:
            parameters: Dict[str, Any] = {"checkEMG": 0}

        # update the residual EMG by removing the motor units with the highest SIL value
        if self.peeloff_dropdown.currentText() == "Yes":
            parameters["peeloff"] = 1
        else:
            parameters["peeloff"] = 0

        # filter out the motor units with a coefficient of variation of their ISI > than parameters.covthr
        if self.cov_filter_dropdown.currentText() == "Yes":
            parameters["covfilter"] = 1
        else:
            parameters["covfilter"] = 0

        # realign the discharge time with the peak of the MUAP (channel with the MUAP with the highest p2p amplitude from double diff EMG signal
        if self.initialisation_dropdown.currentText() == "EMG max":
            parameters["initialization"] = 1
        else:
            parameters["initialization"] = 0

        # refine the MU spike train over the entire signal 1-remove the discharge times that generate outliers in the discharge rate and 2- reevaluate the MU pulse train
        if self.refine_mus_dropdown.currentText() == "Yes":
            parameters["refineMU"] = 1
        else:
            parameters["refineMU"] = 0

        parameters["NITER"] = self.number_iterations_field.value()  # number of iteration for each grid
        parameters["nwindows"] = self.number_windows_field.value()  # number of segmented windows over each contraction
        parameters["thresholdtarget"] = self.threshold_target_field.value()
        parameters["nbextchan"] = self.nb_extended_channels_field.value()
        parameters["duplicatesthresh"] = self.duplicate_threshold_field.value()
        parameters["silthr"] = self.sil_threshold_field.value()
        parameters["covthr"] = self.cov_threshold_field.value()
        parameters["CoVDR"] = 0.3
        parameters["edges"] = 0.5
        parameters["contrastfunc"] = self.contrast_function_dropdown.currentText()
        parameters["peeloffwin"] = 0.025

        # self.edit_field.setText("Saving data")
        # # Save file
        # if self.pathname is not None and self.filename is not None:
        #     savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
        # sio.savemat(savename, {"signal": signal, "parameters": parameters}, do_compression=True)
        # self.edit_field.setText("Data saved")
        # self.start_button.setStyleSheet(
        #     "color: #f0f0f0; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;"
        # )

    def roi_callback(self, eclick, erelease):
        x = [eclick.xdata, erelease.xdata]
        x = sorted(x)
        x[0] = max(0, x[0])
        x[1] = min(len(self.ref_signal), x[1])

        if not hasattr(self, "coordinatesplateau"):
            self.coordinatesplateau = []

        self.coordinatesplateau.extend([int(x[0]), int(x[1])])
        self.roi = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MUedit()
    window.show()
    sys.exit(app.exec_())
