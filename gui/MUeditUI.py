import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QGridLayout,
)


def setup_ui(main_window):
    """Setup the main UI components for the MUedit application."""
    # Configure PyQtGraph globally
    pg.setConfigOption("background", "#262626")
    pg.setConfigOption("foreground", "#f0f0f0")

    main_window.setWindowTitle("MUedit")
    main_window.setGeometry(100, 100, 1500, 850)
    main_window.setStyleSheet("background-color: #262626;")

    # Create tabs dropdown
    main_window.tabs = QComboBox(main_window)
    main_window.tabs.addItems(["DECOMPOSITION", "MANUAL EDITING"])
    main_window.tabs.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 24pt; font-weight: bold;"
    )
    main_window.tabs.setGeometry(0, 810, 400, 40)
    main_window.tabs.currentTextChanged.connect(main_window.tabs_value_changed)

    # Create panels
    main_window.panel = QWidget(main_window)
    main_window.panel.setGeometry(0, 0, 400, 810)
    main_window.panel.setStyleSheet("background-color: #262626;")

    main_window.panel_2 = QWidget(main_window)
    main_window.panel_2.setGeometry(400, 0, 1100, 850)
    main_window.panel_2.setStyleSheet("background-color: #262626;")

    main_window.panel_3 = QWidget(main_window)
    main_window.panel_3.setGeometry(400, 0, 1100, 850)
    main_window.panel_3.setStyleSheet("background-color: #262626;")
    main_window.panel_3.setVisible(False)

    main_window.panel_4 = QWidget(main_window)
    main_window.panel_4.setGeometry(0, 0, 400, 810)
    main_window.panel_4.setStyleSheet("background-color: #262626;")
    main_window.panel_4.setVisible(False)

    # Set up decomposition panel
    setup_decomposition_panel(main_window)

    # Set up results panel
    setup_results_panel(main_window)


def setup_decomposition_panel(main_window):
    """Set up the decomposition panel with all controls."""
    layout = QVBoxLayout(main_window.panel)

    # Filename field and select button
    file_layout = QHBoxLayout()
    main_window.edit_field_saving_3 = QLineEdit("File name")
    main_window.edit_field_saving_3.setReadOnly(True)
    main_window.edit_field_saving_3.setStyleSheet(
        "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.select_file_button = QPushButton("Select file")
    main_window.select_file_button.setStyleSheet(
        "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.select_file_button.clicked.connect(main_window.select_file_button_pushed)

    file_layout.addWidget(main_window.edit_field_saving_3)
    file_layout.addWidget(main_window.select_file_button)

    # Config and segment buttons
    config_layout = QHBoxLayout()
    main_window.set_configuration_button = QPushButton("Set configuration")
    main_window.set_configuration_button.setStyleSheet(
        "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.set_configuration_button.clicked.connect(main_window.set_configuration_button_pushed)

    main_window.segment_session_button = QPushButton("Segment session")
    main_window.segment_session_button.setStyleSheet(
        "color: #cf80ff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.segment_session_button.clicked.connect(main_window.segment_session_button_pushed)

    config_layout.addWidget(main_window.set_configuration_button)
    config_layout.addWidget(main_window.segment_session_button)

    # Parameter controls
    params_layout = QGridLayout()

    # Reference dropdown
    main_window.reference_label = QLabel("Reference")
    main_window.reference_label.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.reference_dropdown = QComboBox()
    main_window.reference_dropdown.addItems(["Target", "EMG amplitude"])
    main_window.reference_dropdown.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # Check EMG dropdown
    main_window.check_emg_label = QLabel("Check EMG")
    main_window.check_emg_label.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.check_emg_dropdown = QComboBox()
    main_window.check_emg_dropdown.addItems(["Yes", "No"])
    main_window.check_emg_dropdown.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # Peeloff dropdown
    main_window.peeloff_label = QLabel("Peeloff")
    main_window.peeloff_label.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.peeloff_dropdown = QComboBox()
    main_window.peeloff_dropdown.addItems(["Yes", "No"])
    main_window.peeloff_dropdown.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # CoV filter dropdown
    main_window.cov_filter_label = QLabel("CoV filter")
    main_window.cov_filter_label.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.cov_filter_dropdown = QComboBox()
    main_window.cov_filter_dropdown.addItems(["Yes", "No"])
    main_window.cov_filter_dropdown.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # Initialisation dropdown
    main_window.initialisation_label = QLabel("Initialisation")
    main_window.initialisation_label.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.initialisation_dropdown = QComboBox()
    main_window.initialisation_dropdown.addItems(["EMG max", "Random"])
    main_window.initialisation_dropdown.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # Refine MUs dropdown
    main_window.refine_mus_label = QLabel("Refine MUs")
    main_window.refine_mus_label.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.refine_mus_dropdown = QComboBox()
    main_window.refine_mus_dropdown.addItems(["Yes", "No"])
    main_window.refine_mus_dropdown.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # Contrast function dropdown
    main_window.contrast_function_label = QLabel("Contrast function")
    main_window.contrast_function_label.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.contrast_function_dropdown = QComboBox()
    main_window.contrast_function_dropdown.addItems(["skew", "kurtosis", "logcosh"])
    main_window.contrast_function_dropdown.setStyleSheet(
        "color: #8f9ed9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # Numerical parameters
    main_window.number_iterations_label = QLabel("Number of iterations")
    main_window.number_iterations_label.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.number_iterations_field = QSpinBox()
    main_window.number_iterations_field.setRange(1, 1000)
    main_window.number_iterations_field.setValue(150)
    main_window.number_iterations_field.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.number_windows_label = QLabel("Number of windows")
    main_window.number_windows_label.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.number_windows_field = QSpinBox()
    main_window.number_windows_field.setRange(1, 100)
    main_window.number_windows_field.setValue(1)
    main_window.number_windows_field.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.threshold_target_label = QLabel("Threshold target")
    main_window.threshold_target_label.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.threshold_target_field = QDoubleSpinBox()
    main_window.threshold_target_field.setRange(0, 1)
    main_window.threshold_target_field.setValue(0.9)
    main_window.threshold_target_field.setSingleStep(0.1)
    main_window.threshold_target_field.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.nb_extended_channels_label = QLabel("Nb of extended channels")
    main_window.nb_extended_channels_label.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.nb_extended_channels_field = QSpinBox()
    main_window.nb_extended_channels_field.setRange(1, 10000)
    main_window.nb_extended_channels_field.setValue(1000)
    main_window.nb_extended_channels_field.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.duplicate_threshold_label = QLabel("Duplicate threshold")
    main_window.duplicate_threshold_label.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.duplicate_threshold_field = QDoubleSpinBox()
    main_window.duplicate_threshold_field.setRange(0, 1)
    main_window.duplicate_threshold_field.setValue(0.3)
    main_window.duplicate_threshold_field.setSingleStep(0.1)
    main_window.duplicate_threshold_field.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.sil_threshold_label = QLabel("SIL threshold")
    main_window.sil_threshold_label.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.sil_threshold_field = QDoubleSpinBox()
    main_window.sil_threshold_field.setRange(0, 1)
    main_window.sil_threshold_field.setValue(0.9)
    main_window.sil_threshold_field.setSingleStep(0.1)
    main_window.sil_threshold_field.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.cov_threshold_label = QLabel("COV threshold")
    main_window.cov_threshold_label.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.cov_threshold_field = QDoubleSpinBox()
    main_window.cov_threshold_field.setRange(0, 1)
    main_window.cov_threshold_field.setValue(0.5)
    main_window.cov_threshold_field.setSingleStep(0.1)
    main_window.cov_threshold_field.setStyleSheet(
        "color: #61c7bf; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    # Add parameters to grid
    params_layout.addWidget(main_window.reference_label, 0, 0)
    params_layout.addWidget(main_window.reference_dropdown, 0, 1)
    params_layout.addWidget(main_window.check_emg_label, 1, 0)
    params_layout.addWidget(main_window.check_emg_dropdown, 1, 1)
    params_layout.addWidget(main_window.contrast_function_label, 2, 0)
    params_layout.addWidget(main_window.contrast_function_dropdown, 2, 1)
    params_layout.addWidget(main_window.initialisation_label, 3, 0)
    params_layout.addWidget(main_window.initialisation_dropdown, 3, 1)
    params_layout.addWidget(main_window.cov_filter_label, 4, 0)
    params_layout.addWidget(main_window.cov_filter_dropdown, 4, 1)
    params_layout.addWidget(main_window.peeloff_label, 5, 0)
    params_layout.addWidget(main_window.peeloff_dropdown, 5, 1)
    params_layout.addWidget(main_window.refine_mus_label, 6, 0)
    params_layout.addWidget(main_window.refine_mus_dropdown, 6, 1)

    params_layout.addWidget(main_window.number_iterations_label, 7, 0)
    params_layout.addWidget(main_window.number_iterations_field, 7, 1)
    params_layout.addWidget(main_window.number_windows_label, 8, 0)
    params_layout.addWidget(main_window.number_windows_field, 8, 1)
    params_layout.addWidget(main_window.threshold_target_label, 9, 0)
    params_layout.addWidget(main_window.threshold_target_field, 9, 1)
    params_layout.addWidget(main_window.nb_extended_channels_label, 10, 0)
    params_layout.addWidget(main_window.nb_extended_channels_field, 10, 1)
    params_layout.addWidget(main_window.duplicate_threshold_label, 11, 0)
    params_layout.addWidget(main_window.duplicate_threshold_field, 11, 1)
    params_layout.addWidget(main_window.sil_threshold_label, 12, 0)
    params_layout.addWidget(main_window.sil_threshold_field, 12, 1)
    params_layout.addWidget(main_window.cov_threshold_label, 13, 0)
    params_layout.addWidget(main_window.cov_threshold_field, 13, 1)

    # Start button
    main_window.start_button = QPushButton("Start")
    main_window.start_button.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;"
    )
    main_window.start_button.clicked.connect(main_window.start_button_pushed)

    # Add layouts to main layout
    layout.addLayout(file_layout)
    layout.addLayout(config_layout)
    layout.addLayout(params_layout)
    layout.addWidget(main_window.start_button)
    layout.addStretch()


def setup_results_panel(main_window):
    """Set up the results panel with all controls."""
    layout = QVBoxLayout(main_window.panel_2)

    # Create edit field
    main_window.edit_field = QLineEdit()
    main_window.edit_field.setStyleSheet(
        "color: #ffffff; background-color: #262626; font-family: 'Poppins'; font-size: 24pt; font-weight: bold;"
    )
    main_window.edit_field.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Create plot areas using PyQtGraph
    main_window.ui_plot_reference = pg.PlotWidget()
    main_window.ui_plot_reference.setBackground("#262626")
    main_window.ui_plot_reference.getAxis("left").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_reference.getAxis("bottom").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_reference.getAxis("left").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_reference.getAxis("bottom").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_reference.setLabel("left", "Reference")
    main_window.ui_plot_reference.setLabel("bottom", "Time (s)")

    main_window.ui_plot_pulsetrain = pg.PlotWidget()
    main_window.ui_plot_pulsetrain.setBackground("#262626")
    main_window.ui_plot_pulsetrain.getAxis("left").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_pulsetrain.getAxis("bottom").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_pulsetrain.getAxis("left").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_pulsetrain.getAxis("bottom").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.ui_plot_pulsetrain.setLabel("left", "Pulse train")
    main_window.ui_plot_pulsetrain.setLabel("bottom", "Time (s)")

    # Add widgets to layout
    layout.addWidget(main_window.edit_field)
    layout.addWidget(main_window.ui_plot_reference)
    layout.addWidget(main_window.ui_plot_pulsetrain)
