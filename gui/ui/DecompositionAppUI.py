import sys
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QFrame,
    QApplication,
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg

# Import custom components
from ui.components import (
    CleanTheme,
    ActionButton,
    CollapsiblePanel,
    VisualizationPanel,
    FormDropdown,
    FormSpinBox,
    FormDoubleSpinBox,
    SettingsGroup,
    CleanScrollBar,
)


def setup_ui(main_window):
    """
    Set up the UI for the HDEMG Decomposition Tool with a clean, modern design.

    Args:
        main_window: The main window instance
    """
    # Set window properties
    main_window.setWindowTitle("HDEMG Decomposition Tool")
    main_window.setGeometry(100, 100, 1200, 800)
    main_window.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")

    # Main widget and layout
    main_window.central_widget = QWidget()
    main_window.setCentralWidget(main_window.central_widget)
    main_window.main_layout = QHBoxLayout(main_window.central_widget)
    main_window.main_layout.setContentsMargins(0, 0, 0, 0)
    main_window.main_layout.setSpacing(0)

    # Create the left panel for settings with a scroll area
    setup_left_panel(main_window)

    # Create the content area (center + right panels)
    content_widget = QWidget()
    content_layout = QHBoxLayout(content_widget)
    content_layout.setContentsMargins(20, 20, 20, 20)
    content_layout.setSpacing(20)

    # Create the center panel for visualization
    setup_center_panel(main_window, content_layout)

    # Create the right panel for status and results
    setup_right_panel(main_window, content_layout)

    main_window.main_layout.addWidget(content_widget)


def setup_left_panel(main_window):
    """Set up the left panel with settings and controls."""
    # Create a container for the scroll area to control positioning
    left_container = QWidget()
    left_container.setMinimumWidth(250)
    left_container.setMaximumWidth(300)
    left_container_layout = QVBoxLayout(left_container)
    left_container_layout.setContentsMargins(0, 0, 0, 0)

    # Create a scrollable container for the left panel
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Apply the clean scrollbar styling
    CleanScrollBar.apply(scroll_area)

    # Create the actual panel that will contain all controls
    left_panel = QWidget()
    left_panel.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(15, 15, 15, 15)
    left_layout.setSpacing(15)

    # File Information panel
    file_info_group = SettingsGroup("File Information")
    main_window.file_info_display = QLabel("No file loaded")
    main_window.file_info_display.setWordWrap(True)
    main_window.file_info_display.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    file_info_group.add_field(main_window.file_info_display)
    left_layout.addWidget(file_info_group)

    # Algorithm Selection panel
    algo_panel = CollapsiblePanel("Algorithm Selection")
    algo_field = FormDropdown("Algorithm", ["Fast ICA", "Other Algorithm 1", "Other Algorithm 2"])
    main_window.algo_combo = algo_field.dropdown
    # Use system styles for dropdown arrows
    main_window.algo_combo.setStyleSheet(
        f"""
        QComboBox {{
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 4px;
            padding: 5px 8px;
            background-color: white;
            min-height: 20px;
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid {CleanTheme.BORDER};
        }}
        """
    )
    main_window.algo_combo.setCurrentText("Fast ICA")  # Set initial value
    algo_panel.add_widget(algo_field)
    left_layout.addWidget(algo_panel)

    # Processing Options panel
    options_panel = CollapsiblePanel("Processing Options")

    check_emg_field = FormDropdown("Check EMG Quality", ["Yes", "No"])
    main_window.check_emg_dropdown = check_emg_field.dropdown
    main_window.check_emg_dropdown.setStyleSheet(main_window.algo_combo.styleSheet())  # Use same style
    main_window.check_emg_dropdown.setCurrentText("Yes")  # Set initial value
    options_panel.add_widget(check_emg_field)

    cov_filter_field = FormDropdown("COV Filter", ["Yes", "No"])
    main_window.cov_filter_dropdown = cov_filter_field.dropdown
    main_window.cov_filter_dropdown.setStyleSheet(main_window.algo_combo.styleSheet())  # Use same style
    main_window.cov_filter_dropdown.setCurrentText("Yes")  # Set initial value
    options_panel.add_widget(cov_filter_field)

    reference_field = FormDropdown("Reference", ["EMG amplitude", "Target"])
    main_window.reference_dropdown = reference_field.dropdown
    main_window.reference_dropdown.setStyleSheet(main_window.algo_combo.styleSheet())  # Use same style
    main_window.reference_dropdown.setCurrentText("EMG amplitude")  # Set initial value
    options_panel.add_widget(reference_field)

    left_layout.addWidget(options_panel)

    # Advanced Options panel
    advanced_panel = CollapsiblePanel("Advanced Options")

    contrast_field = FormDropdown("Contrast Function", ["square", "skew", "logcosh"])
    main_window.contrast_function_dropdown = contrast_field.dropdown
    main_window.contrast_function_dropdown.setStyleSheet(main_window.algo_combo.styleSheet())  # Use same style
    main_window.contrast_function_dropdown.setCurrentText("square")  # Set initial value
    advanced_panel.add_widget(contrast_field)

    init_field = FormDropdown("Initialisation", ["EMG max", "Random"])
    main_window.initialisation_dropdown = init_field.dropdown
    main_window.initialisation_dropdown.setStyleSheet(main_window.algo_combo.styleSheet())  # Use same style
    main_window.initialisation_dropdown.setCurrentText("Random")  # Set initial value
    advanced_panel.add_widget(init_field)

    peel_field = FormDropdown("Peel Off", ["Yes", "No"])
    main_window.peeloff_dropdown = peel_field.dropdown
    main_window.peeloff_dropdown.setStyleSheet(main_window.algo_combo.styleSheet())  # Use same style
    main_window.peeloff_dropdown.setCurrentText("Yes")  # Set initial value
    advanced_panel.add_widget(peel_field)

    refine_field = FormDropdown("Refine Motor Units", ["Yes", "No"])
    main_window.refine_mus_dropdown = refine_field.dropdown
    main_window.refine_mus_dropdown.setStyleSheet(main_window.algo_combo.styleSheet())  # Use same style
    main_window.refine_mus_dropdown.setCurrentText("Yes")  # Set initial value
    advanced_panel.add_widget(refine_field)

    left_layout.addWidget(advanced_panel)

    # Common style for spinboxes
    spinbox_style = f"""
    QSpinBox, QDoubleSpinBox {{
        border: 1px solid {CleanTheme.BORDER};
        border-radius: 4px;
        padding: 5px;
        background-color: white;
        min-height: 20px;
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        width: 16px;
        border-left: 1px solid {CleanTheme.BORDER};
    }}
    """

    # Parameters panel
    params_panel = CollapsiblePanel("Parameters")

    iter_field = FormSpinBox("Iterations", 78, 1, 1000)  # Updated to match screenshot
    main_window.number_iterations_field = iter_field.spinbox
    main_window.number_iterations_field.setStyleSheet(spinbox_style)
    params_panel.add_widget(iter_field)

    windows_field = FormSpinBox("Windows", 7, 1, 100)  # Updated to match screenshot
    main_window.number_windows_field = windows_field.spinbox
    main_window.number_windows_field.setStyleSheet(spinbox_style)
    params_panel.add_widget(windows_field)

    threshold_field = FormDoubleSpinBox("Threshold Target", 1.00, 0, 1, 0.1)  # Updated to match screenshot
    main_window.threshold_target_field = threshold_field.spinbox
    main_window.threshold_target_field.setStyleSheet(spinbox_style)
    params_panel.add_widget(threshold_field)

    duplicate_field = FormDoubleSpinBox("Duplicate Threshold", 0.3, 0, 1, 0.1)
    main_window.duplicate_threshold_field = duplicate_field.spinbox
    main_window.duplicate_threshold_field.setStyleSheet(spinbox_style)
    params_panel.add_widget(duplicate_field)

    sil_field = FormDoubleSpinBox("SIL Threshold", 0.9, 0, 1, 0.1)
    main_window.sil_threshold_field = sil_field.spinbox
    main_window.sil_threshold_field.setStyleSheet(spinbox_style)
    params_panel.add_widget(sil_field)

    cov_field = FormDoubleSpinBox("COV Threshold", 0.5, 0, 1, 0.1)
    main_window.cov_threshold_field = cov_field.spinbox
    main_window.cov_threshold_field.setStyleSheet(spinbox_style)
    params_panel.add_widget(cov_field)

    channels_field = FormSpinBox("Extended Channels", 99, 10, 5000)  # Updated to match screenshot
    main_window.nb_extended_channels_field = channels_field.spinbox
    main_window.nb_extended_channels_field.setStyleSheet(spinbox_style)
    params_panel.add_widget(channels_field)

    left_layout.addWidget(params_panel)

    # Add stretch to push everything to the top
    left_layout.addStretch(1)

    # Set the left panel as the scroll area's widget
    scroll_area.setWidget(left_panel)

    # Add the scroll area to the container layout
    left_container_layout.addWidget(scroll_area)

    # Add the container to the main layout
    main_window.main_layout.addWidget(left_container)


def setup_center_panel(main_window, parent_layout):
    """Set up the center panel with visualizations."""
    center_panel = QWidget()
    center_layout = QVBoxLayout(center_panel)
    center_layout.setContentsMargins(0, 0, 0, 0)
    center_layout.setSpacing(20)

    # File information display at the top
    main_window.edit_field = QLabel("Ready")
    main_window.edit_field.setStyleSheet(
        f"""
        QLabel {{
            color: {CleanTheme.TEXT_PRIMARY};
            background-color: {CleanTheme.BG_CARD};
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 4px;
            padding: 8px 12px;
        }}
        """
    )
    center_layout.addWidget(main_window.edit_field)

    # Decomposition Controls section
    controls_layout = QHBoxLayout()
    controls_layout.setContentsMargins(0, 0, 0, 0)
    controls_layout.setSpacing(10)

    controls_title = QLabel("Decomposition Controls")
    controls_title.setFont(main_window.font())
    controls_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {CleanTheme.TEXT_PRIMARY};")
    controls_layout.addWidget(controls_title)

    controls_layout.addStretch(1)

    main_window.start_button = ActionButton("▶ Start Decomposition", primary=True)
    main_window.start_button.setEnabled(True)  # Set to True for visual consistency with image
    controls_layout.addWidget(main_window.start_button)

    center_layout.addLayout(controls_layout)

    # Create and setup signal processing visualization with PyQtGraph
    main_window.ui_plot_reference = pg.PlotWidget()
    main_window.ui_plot_reference.setBackground("w")  # White background
    main_window.ui_plot_reference.setLabel("left", "Amplitude")
    main_window.ui_plot_reference.setLabel("bottom", "Time (s)")
    main_window.ui_plot_reference.showGrid(x=True, y=True)
    main_window.ui_plot_reference.setMinimumHeight(250)

    signal_panel = VisualizationPanel("Signal Processing Visualization", main_window.ui_plot_reference)
    center_layout.addWidget(signal_panel, 3)  # Give it more stretch

    # Create and setup motor unit outputs visualization with PyQtGraph
    main_window.ui_plot_pulsetrain = pg.PlotWidget()
    main_window.ui_plot_pulsetrain.setBackground("w")  # White background
    main_window.ui_plot_pulsetrain.setLabel("left", "Amplitude")
    main_window.ui_plot_pulsetrain.setLabel("bottom", "Time (s)")
    main_window.ui_plot_pulsetrain.showGrid(x=True, y=True)
    main_window.ui_plot_pulsetrain.setMinimumHeight(200)

    motor_panel = VisualizationPanel("Motor Unit Outputs", main_window.ui_plot_pulsetrain)
    center_layout.addWidget(motor_panel, 2)  # Give it slightly less stretch than the signal plot

    parent_layout.addWidget(center_panel, 4)  # Add with stretch to make it wider


def setup_right_panel(main_window, parent_layout):
    """Set up the right panel with status and results."""
    right_panel = QWidget()
    right_panel.setMaximumWidth(250)
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(20)

    # Processing Status group
    status_group = SettingsGroup("Processing Status")

    main_window.status_progress = QProgressBar()
    main_window.status_progress.setValue(0)
    main_window.status_progress.setStyleSheet(
        f"""
        QProgressBar {{
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 4px;
            text-align: center;
            background-color: white;
        }}
        QProgressBar::chunk {{
            background-color: #4CAF50;
            border-radius: 3px;
        }}
        """
    )
    status_group.add_field(main_window.status_progress)

    main_window.status_text = QLabel("Ready to start decomposition")
    main_window.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_window.status_text.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    status_group.add_field(main_window.status_text)

    right_layout.addWidget(status_group)

    # Analysis Results group
    results_group = SettingsGroup("Analysis Results")

    main_window.motor_units_label = QLabel("Motor Units: --")
    main_window.motor_units_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY}; font-weight: bold;")
    results_group.add_field(main_window.motor_units_label)

    main_window.sil_value_label = QLabel("SIL: --")
    main_window.sil_value_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    results_group.add_field(main_window.sil_value_label)

    main_window.cov_value_label = QLabel("CoV: --")
    main_window.cov_value_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    results_group.add_field(main_window.cov_value_label)

    # Save Output button
    main_window.save_output_button = ActionButton("💾 Save Output", primary=True)
    main_window.save_output_button.setEnabled(True)  # Set to True for visual consistency with image
    results_group.add_field(main_window.save_output_button)

    right_layout.addWidget(results_group)

    # Configuration buttons
    config_group = SettingsGroup("Configuration")
    main_window.set_configuration_button = ActionButton("Set Configuration", primary=False)
    main_window.set_configuration_button.setEnabled(True)
    config_group.add_field(main_window.set_configuration_button)

    main_window.segment_session_button = ActionButton("Segment Session", primary=False)
    config_group.add_field(main_window.segment_session_button)

    right_layout.addWidget(config_group)

    # Navigation group
    nav_group = SettingsGroup("Navigation")

    main_window.edit_mode_btn = ActionButton("✏️ Editing Mode", primary=False)
    main_window.edit_mode_btn.setEnabled(True)  # Set to True for visual consistency with image
    nav_group.add_field(main_window.edit_mode_btn)

    main_window.analysis_mode_btn = ActionButton("📊 Analysis Mode", primary=False)
    nav_group.add_field(main_window.analysis_mode_btn)

    main_window.export_btn = ActionButton("📤 Export", primary=False)
    nav_group.add_field(main_window.export_btn)

    # Back to Import button
    main_window.back_to_import_btn = ActionButton("← Back to Import", primary=False)
    nav_group.add_field(main_window.back_to_import_btn)

    right_layout.addWidget(nav_group)

    right_layout.addStretch(1)
    parent_layout.addWidget(right_panel, 1)


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
