import sys
import os
import traceback
import numpy as np
import scipy.io as sio
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QLineEdit, QProgressBar, 
    QFrame, QGridLayout, QCheckBox, QRadioButton, QSpinBox,
    QDoubleSpinBox, QScrollArea, QFileDialog
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont

# Add necessary paths to the system path
current_dir = os.path.dirname(os.path.abspath(__file__))  # Algorithm_Selection_Decomposition folder
views_dir = os.path.dirname(current_dir)  # views folder
gui_dir = os.path.dirname(views_dir)  # gui folder
project_root = os.path.dirname(gui_dir)  # project root
sys.path.append(project_root)
sys.path.append(gui_dir)

# Import pyqtgraph for visualization
import pyqtgraph as pg

# Import workers from the root directory
from SaveMatWorker import SaveMatWorker
from DecompositionWorker import DecompositionWorker
from HDEMGdecomposition import prepare_parameters

# Import UI related modules from utils
from utils.config_and_input.openOTBplus import openOTBplus
from utils.config_and_input.segmentsession import SegmentSession


class DecompositionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Algorithm Selection & Decomposition")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize variables
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
        self.threads = []
        self.iteration_counter = 0
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Create the left panel for settings
        self.setup_left_panel()
        
        # Create the center panel for visualization
        self.setup_center_panel()
        
        # Create the right panel for status and results
        self.setup_right_panel()
        
    def setup_left_panel(self):
        left_panel = QWidget()
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        # Algorithm Selection
        algo_label = QLabel("Algorithm Selection")
        self.algo_combo = QComboBox()
        self.algo_combo.addItem("Fast ICA")
        self.algo_combo.addItem("Other Algorithm 1")
        self.algo_combo.addItem("Other Algorithm 2")
        
        # File Selection
        self.select_file_button = QPushButton("Select File")
        self.select_file_button.clicked.connect(self.select_file_button_pushed)
        
        self.edit_field_saving_3 = QLineEdit()
        self.edit_field_saving_3.setReadOnly(True)
        
        # Processing Options
        processing_label = QLabel("Processing Options")
        
        # Check EMG Quality
        check_emg_label = QLabel("Check EMG Quality")
        self.check_emg_dropdown = QComboBox()
        self.check_emg_dropdown.addItem("Yes")
        self.check_emg_dropdown.addItem("No")
        
        # COV Filter
        cov_filter_label = QLabel("COV Filter")
        self.cov_filter_dropdown = QComboBox()
        self.cov_filter_dropdown.addItem("Yes")
        self.cov_filter_dropdown.addItem("No")
        
        # Reference
        reference_label = QLabel("Reference")
        self.reference_dropdown = QComboBox()
        self.reference_dropdown.addItem("EMG amplitude")
        self.reference_dropdown.addItem("Target")
        
        # Set Configuration Button
        self.set_configuration_button = QPushButton("Set Configuration")
        self.set_configuration_button.clicked.connect(self.set_configuration_button_pushed)
        self.set_configuration_button.setEnabled(False)
        
        # Segment Session
        self.segment_session_button = QPushButton("Segment Session")
        self.segment_session_button.clicked.connect(self.segment_session_button_pushed)
        
        # Contrast Function
        contrast_label = QLabel("Contrast Function")
        self.contrast_function_dropdown = QComboBox()
        self.contrast_function_dropdown.addItem("Skew")
        self.contrast_function_dropdown.addItem("Logcosh")
        self.contrast_function_dropdown.addItem("Kurtosis")
        
        # Initialisation
        init_label = QLabel("Initialisation")
        self.initialisation_dropdown = QComboBox()
        self.initialisation_dropdown.addItem("EMG max")
        self.initialisation_dropdown.addItem("Random")
        
        # Peel Off
        peel_label = QLabel("Peel Off")
        self.peeloff_dropdown = QComboBox()
        self.peeloff_dropdown.addItem("Yes")
        self.peeloff_dropdown.addItem("No")
        
        # Refine Motor Units
        refine_label = QLabel("Refine Motor Units")
        self.refine_mus_dropdown = QComboBox()
        self.refine_mus_dropdown.addItem("Yes")
        self.refine_mus_dropdown.addItem("No")
        
        # Iterations and Windows
        iter_layout = QHBoxLayout()
        iter_label = QLabel("Iterations")
        self.number_iterations_field = QSpinBox()
        self.number_iterations_field.setValue(75)
        self.number_iterations_field.setRange(1, 1000)
        
        windows_label = QLabel("Windows")
        self.number_windows_field = QSpinBox()
        self.number_windows_field.setValue(1)
        self.number_windows_field.setRange(1, 100)
        
        iter_layout.addWidget(iter_label)
        iter_layout.addWidget(self.number_iterations_field)
        iter_layout.addWidget(windows_label)
        iter_layout.addWidget(self.number_windows_field)
        
        # Threshold Target
        threshold_label = QLabel("Threshold Target")
        self.threshold_target_field = QDoubleSpinBox()
        self.threshold_target_field.setValue(0.8)
        self.threshold_target_field.setRange(0, 1)
        self.threshold_target_field.setSingleStep(0.1)
        
        # Duplicate Threshold
        duplicate_label = QLabel("Duplicate Threshold")
        self.duplicate_threshold_field = QDoubleSpinBox()
        self.duplicate_threshold_field.setValue(0.3)
        self.duplicate_threshold_field.setRange(0, 1)
        self.duplicate_threshold_field.setSingleStep(0.1)
        
        # SIL Threshold
        sil_label = QLabel("SIL Threshold")
        self.sil_threshold_field = QDoubleSpinBox()
        self.sil_threshold_field.setValue(0.9)
        self.sil_threshold_field.setRange(0, 1)
        self.sil_threshold_field.setSingleStep(0.1)
        
        # COV Threshold
        cov_threshold_label = QLabel("COV Threshold")
        self.cov_threshold_field = QDoubleSpinBox()
        self.cov_threshold_field.setValue(0.5)
        self.cov_threshold_field.setRange(0, 1)
        self.cov_threshold_field.setSingleStep(0.1)
        
        # Nb of extended channels
        channels_label = QLabel("Nb of extended channels")
        self.nb_extended_channels_field = QSpinBox()
        self.nb_extended_channels_field.setValue(1000)
        self.nb_extended_channels_field.setRange(10, 5000)