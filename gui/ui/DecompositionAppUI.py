import sys
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QProgressBar,
    QFrame,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
import pyqtgraph as pg


def setup_ui(main_window):
    """
    Set up the UI for the HDEMG Decomposition Tool.

    Args:
        main_window: The main window instance
    """
    # Set window properties
    main_window.setWindowTitle("HDEMG Decomposition Tool")
    main_window.setGeometry(100, 100, 1200, 800)

    # Main widget and layout
    main_window.central_widget = QWidget()
    main_window.setCentralWidget(main_window.central_widget)
    main_window.main_layout = QHBoxLayout(main_window.central_widget)

    # Create the left panel for settings
    setup_left_panel(main_window)

    # Create the center panel for visualization
    setup_center_panel(main_window)

    # Create the right panel for status and results
    setup_right_panel(main_window)


def setup_left_panel(main_window):
    """Set up the left panel with settings and controls."""
    left_panel = QWidget()
    left_panel.setMaximumWidth(250)
    left_layout = QVBoxLayout(left_panel)

    # File Information section
    file_info_frame = QFrame()
    file_info_layout = QVBoxLayout(file_info_frame)

    file_info_label = QLabel("File Information")
    file_info_label.setFont(QFont("Arial", 10, QFont.Bold))

    main_window.file_info_display = QLabel("No file loaded")
    main_window.file_info_display.setWordWrap(True)
    main_window.file_info_display.setStyleSheet("color: #888;")

    file_info_layout.addWidget(file_info_label)
    file_info_layout.addWidget(main_window.file_info_display)

    # Algorithm Selection
    algo_label = QLabel("Algorithm Selection")
    main_window.algo_combo = QComboBox()
    main_window.algo_combo.addItem("Fast ICA")
    main_window.algo_combo.addItem("Other Algorithm 1")
    main_window.algo_combo.addItem("Other Algorithm 2")

    # Processing Options
    processing_label = QLabel("Processing Options")

    # Check EMG Quality
    check_emg_label = QLabel("Check EMG Quality")
    main_window.check_emg_dropdown = QComboBox()
    main_window.check_emg_dropdown.addItem("Yes")
    main_window.check_emg_dropdown.addItem("No")

    # COV Filter
    cov_filter_label = QLabel("COV Filter")
    main_window.cov_filter_dropdown = QComboBox()
    main_window.cov_filter_dropdown.addItem("Yes")
    main_window.cov_filter_dropdown.addItem("No")

    # Reference
    reference_label = QLabel("Reference")
    main_window.reference_dropdown = QComboBox()
    main_window.reference_dropdown.addItem("EMG amplitude")
    main_window.reference_dropdown.addItem("Target")

    # Set Configuration Button
    main_window.set_configuration_button = QPushButton("Set Configuration")
    main_window.set_configuration_button.setEnabled(False)

    # Segment Session
    main_window.segment_session_button = QPushButton("Segment Session")

    # Contrast Function
    contrast_label = QLabel("Contrast Function")
    main_window.contrast_function_dropdown = QComboBox()
    main_window.contrast_function_dropdown.addItem("skew")
    main_window.contrast_function_dropdown.addItem("logcosh")
    main_window.contrast_function_dropdown.addItem("square")

    # Initialisation
    init_label = QLabel("Initialisation")
    main_window.initialisation_dropdown = QComboBox()
    main_window.initialisation_dropdown.addItem("EMG max")
    main_window.initialisation_dropdown.addItem("Random")

    # Peel Off
    peel_label = QLabel("Peel Off")
    main_window.peeloff_dropdown = QComboBox()
    main_window.peeloff_dropdown.addItem("Yes")
    main_window.peeloff_dropdown.addItem("No")

    # Refine Motor Units
    refine_label = QLabel("Refine Motor Units")
    main_window.refine_mus_dropdown = QComboBox()
    main_window.refine_mus_dropdown.addItem("Yes")
    main_window.refine_mus_dropdown.addItem("No")

    # Iterations and Windows
    iter_layout = QHBoxLayout()
    iter_label = QLabel("Iterations")
    main_window.number_iterations_field = QSpinBox()
    main_window.number_iterations_field.setValue(75)
    main_window.number_iterations_field.setRange(1, 1000)

    windows_label = QLabel("Windows")
    main_window.number_windows_field = QSpinBox()
    main_window.number_windows_field.setValue(1)
    main_window.number_windows_field.setRange(1, 100)

    iter_layout.addWidget(iter_label)
    iter_layout.addWidget(main_window.number_iterations_field)
    iter_layout.addWidget(windows_label)
    iter_layout.addWidget(main_window.number_windows_field)

    # Threshold Target
    threshold_label = QLabel("Threshold Target")
    main_window.threshold_target_field = QDoubleSpinBox()
    main_window.threshold_target_field.setValue(0.8)
    main_window.threshold_target_field.setRange(0, 1)
    main_window.threshold_target_field.setSingleStep(0.1)

    # Duplicate Threshold
    duplicate_label = QLabel("Duplicate Threshold")
    main_window.duplicate_threshold_field = QDoubleSpinBox()
    main_window.duplicate_threshold_field.setValue(0.3)
    main_window.duplicate_threshold_field.setRange(0, 1)
    main_window.duplicate_threshold_field.setSingleStep(0.1)

    # SIL Threshold
    sil_label = QLabel("SIL Threshold")
    main_window.sil_threshold_field = QDoubleSpinBox()
    main_window.sil_threshold_field.setValue(0.9)
    main_window.sil_threshold_field.setRange(0, 1)
    main_window.sil_threshold_field.setSingleStep(0.1)

    # COV Threshold
    cov_threshold_label = QLabel("COV Threshold")
    main_window.cov_threshold_field = QDoubleSpinBox()
    main_window.cov_threshold_field.setValue(0.5)
    main_window.cov_threshold_field.setRange(0, 1)
    main_window.cov_threshold_field.setSingleStep(0.1)

    # Nb of extended channels
    channels_label = QLabel("Nb of extended channels")
    main_window.nb_extended_channels_field = QSpinBox()
    main_window.nb_extended_channels_field.setValue(1000)
    main_window.nb_extended_channels_field.setRange(10, 5000)

    # Add all widgets to left layout
    left_layout.addWidget(file_info_frame)
    left_layout.addWidget(algo_label)
    left_layout.addWidget(main_window.algo_combo)
    left_layout.addWidget(processing_label)
    left_layout.addWidget(check_emg_label)
    left_layout.addWidget(main_window.check_emg_dropdown)
    left_layout.addWidget(cov_filter_label)
    left_layout.addWidget(main_window.cov_filter_dropdown)
    left_layout.addWidget(reference_label)
    left_layout.addWidget(main_window.reference_dropdown)
    left_layout.addWidget(main_window.set_configuration_button)
    left_layout.addWidget(main_window.segment_session_button)
    left_layout.addWidget(contrast_label)
    left_layout.addWidget(main_window.contrast_function_dropdown)
    left_layout.addWidget(init_label)
    left_layout.addWidget(main_window.initialisation_dropdown)
    left_layout.addWidget(peel_label)
    left_layout.addWidget(main_window.peeloff_dropdown)
    left_layout.addWidget(refine_label)
    left_layout.addWidget(main_window.refine_mus_dropdown)
    left_layout.addLayout(iter_layout)
    left_layout.addWidget(threshold_label)
    left_layout.addWidget(main_window.threshold_target_field)
    left_layout.addWidget(duplicate_label)
    left_layout.addWidget(main_window.duplicate_threshold_field)
    left_layout.addWidget(sil_label)
    left_layout.addWidget(main_window.sil_threshold_field)
    left_layout.addWidget(cov_threshold_label)
    left_layout.addWidget(main_window.cov_threshold_field)
    left_layout.addWidget(channels_label)
    left_layout.addWidget(main_window.nb_extended_channels_field)
    left_layout.addStretch()

    main_window.main_layout.addWidget(left_panel)


def setup_center_panel(main_window):
    """Set up the center panel with visualizations."""
    center_panel = QWidget()
    center_layout = QVBoxLayout(center_panel)

    # Status display field
    main_window.edit_field = QLineEdit()
    main_window.edit_field.setReadOnly(True)
    main_window.edit_field.setText("Ready")

    # Decomposition Controls section
    controls_layout = QHBoxLayout()
    decomp_label = QLabel("Decomposition Controls")
    decomp_label.setFont(QFont("Arial", 10, QFont.Bold))

    main_window.start_button = QPushButton("▶ Start Decomposition")
    main_window.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px;")
    main_window.start_button.setEnabled(False)  # Initially disabled until data is loaded

    controls_layout.addWidget(decomp_label)
    controls_layout.addStretch()
    controls_layout.addWidget(main_window.start_button)

    # Signal Processing Visualization section
    signal_label = QLabel("Signal Processing Visualization")
    signal_label.setFont(QFont("Arial", 10, QFont.Bold))

    # Signal visualization area using pyqtgraph
    main_window.ui_plot_reference = pg.PlotWidget()
    main_window.ui_plot_reference.setBackground("w")  # White background
    main_window.ui_plot_reference.setLabel("left", "Amplitude")
    main_window.ui_plot_reference.setLabel("bottom", "Time (s)")
    main_window.ui_plot_reference.showGrid(x=True, y=True)

    # Motor Unit Outputs section
    motor_unit_label = QLabel("Motor Unit Outputs")
    motor_unit_label.setFont(QFont("Arial", 10, QFont.Bold))

    # Motor unit visualization area using pyqtgraph
    main_window.ui_plot_pulsetrain = pg.PlotWidget()
    main_window.ui_plot_pulsetrain.setBackground("w")  # White background
    main_window.ui_plot_pulsetrain.setLabel("left", "Amplitude")
    main_window.ui_plot_pulsetrain.setLabel("bottom", "Time (s)")
    main_window.ui_plot_pulsetrain.showGrid(x=True, y=True)

    # Add all widgets to center layout
    center_layout.addWidget(main_window.edit_field)
    center_layout.addLayout(controls_layout)
    center_layout.addWidget(signal_label)
    center_layout.addWidget(main_window.ui_plot_reference, stretch=3)
    center_layout.addWidget(motor_unit_label)
    center_layout.addWidget(main_window.ui_plot_pulsetrain, stretch=2)

    main_window.main_layout.addWidget(center_panel, stretch=3)


def setup_right_panel(main_window):
    """Set up the right panel with status and results."""
    right_panel = QWidget()
    right_panel.setMaximumWidth(250)
    right_layout = QVBoxLayout(right_panel)

    # Processing Status section
    status_label = QLabel("Processing Status")

    main_window.status_progress = QProgressBar()
    main_window.status_progress.setValue(0)

    main_window.status_text = QLabel("Ready")

    # Analysis Results section
    results_label = QLabel("Analysis Results")
    results_label.setFont(QFont("Arial", 10, QFont.Bold))

    main_window.motor_units_label = QLabel("Motor Units: --")

    main_window.sil_value_label = QLabel("SIL: --")

    main_window.cov_value_label = QLabel("CoV: --")

    # Save Output button
    main_window.save_output_button = QPushButton("💾 Save Output")
    main_window.save_output_button.setEnabled(False)

    # Navigation section
    nav_label = QLabel("Navigation")
    nav_label.setFont(QFont("Arial", 10, QFont.Bold))

    main_window.edit_mode_btn = QPushButton("✏️ Editing Mode")
    main_window.edit_mode_btn.setEnabled(False)

    main_window.analysis_mode_btn = QPushButton("📊 Analysis Mode")

    main_window.export_btn = QPushButton("📤 Export")

    # Back to Import button
    main_window.back_to_import_btn = QPushButton("← Back to Import")

    # Add all widgets to right layout
    right_layout.addWidget(status_label)
    right_layout.addWidget(main_window.status_progress)
    right_layout.addWidget(main_window.status_text)
    right_layout.addSpacing(20)
    right_layout.addWidget(results_label)
    right_layout.addWidget(main_window.motor_units_label)
    right_layout.addWidget(main_window.sil_value_label)
    right_layout.addWidget(main_window.cov_value_label)
    right_layout.addWidget(main_window.save_output_button)
    right_layout.addSpacing(20)
    right_layout.addWidget(nav_label)
    right_layout.addWidget(main_window.edit_mode_btn)
    right_layout.addWidget(main_window.analysis_mode_btn)
    right_layout.addWidget(main_window.export_btn)
    right_layout.addWidget(main_window.back_to_import_btn)
    right_layout.addStretch()

    main_window.main_layout.addWidget(right_panel)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow

    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()

    app = QApplication(sys.argv)
    window = TestWindow()
    setup_ui(window)
    window.show()
    sys.exit(app.exec_())
