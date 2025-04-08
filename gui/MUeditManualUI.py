import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QGroupBox,
)


def setup_ui(main_window):
    """Setup the main UI components for the MUedit Manual application."""
    # Set window properties
    main_window.setWindowTitle("MUedit - Manual Editing")
    main_window.setGeometry(100, 100, 1500, 850)
    main_window.setStyleSheet("background-color: #262626;")

    # Configure PyQtGraph globally
    pg.setConfigOption("background", "#262626")
    pg.setConfigOption("foreground", "#f0f0f0")

    # Create main widget and layout
    main_window.central_widget = QWidget()
    main_window.setCentralWidget(main_window.central_widget)
    main_layout = QHBoxLayout(main_window.central_widget)

    # Set up control panel
    setup_control_panel(main_window)

    # Set up display panel
    setup_display_panel(main_window)

    # Add panels to main layout
    main_layout.addWidget(main_window.control_panel)
    main_layout.addWidget(main_window.display_panel, 1)  # The 1 is the stretch factor

    # Set up keyboard shortcuts
    main_window.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


def setup_control_panel(main_window):
    """Set up the control panel with all controls."""
    main_window.control_panel = QWidget()
    main_window.control_panel.setFixedWidth(400)
    control_layout = QVBoxLayout(main_window.control_panel)

    # File selection section
    file_group = QGroupBox("File Selection")
    file_group.setStyleSheet("color: #8118FF; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;")
    file_layout = QVBoxLayout(file_group)

    file_select_layout = QHBoxLayout()
    main_window.file_path_field = QLineEdit("File name")
    main_window.file_path_field.setReadOnly(True)
    main_window.file_path_field.setStyleSheet(
        "color: #8118FF; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    main_window.select_file_btn = QPushButton("Select file")
    main_window.select_file_btn.setStyleSheet(
        "color: #8118FF; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.select_file_btn.clicked.connect(main_window.select_file_button_pushed)

    file_select_layout.addWidget(main_window.file_path_field)
    file_select_layout.addWidget(main_window.select_file_btn)

    file_layout.addLayout(file_select_layout)

    # Batch processing section
    batch_group = QGroupBox("Batch Processing")
    batch_group.setStyleSheet("color: #8F9ED9; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;")
    batch_layout = QVBoxLayout(batch_group)

    # Create batch processing buttons
    main_window.remove_outliers_btn = QPushButton("1 - Remove all the outliers")
    main_window.remove_outliers_btn.setStyleSheet(
        "color: #8F9ED9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.remove_outliers_btn.clicked.connect(main_window.remove_all_outliers_button_pushed)

    main_window.update_filters_btn = QPushButton("2 - Update all MU filters")
    main_window.update_filters_btn.setStyleSheet(
        "color: #8F9ED9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.update_filters_btn.clicked.connect(main_window.update_all_mu_filters_button_pushed)

    main_window.remove_flagged_btn = QPushButton("3 - Remove flagged MU")
    main_window.remove_flagged_btn.setStyleSheet(
        "color: #8F9ED9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.remove_flagged_btn.clicked.connect(main_window.remove_flagged_mu_button_pushed)

    main_window.remove_duplicates_within_btn = QPushButton("4 - Remove duplicates within grids")
    main_window.remove_duplicates_within_btn.setStyleSheet(
        "color: #8F9ED9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.remove_duplicates_within_btn.clicked.connect(main_window.remove_duplicates_within_grids_button_pushed)

    main_window.remove_duplicates_between_btn = QPushButton("5 - Remove duplicates between grids")
    main_window.remove_duplicates_between_btn.setStyleSheet(
        "color: #8F9ED9; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.remove_duplicates_between_btn.clicked.connect(main_window.remove_duplicates_between_grids_button_pushed)

    batch_layout.addWidget(main_window.remove_outliers_btn)
    batch_layout.addWidget(main_window.update_filters_btn)
    batch_layout.addWidget(main_window.remove_flagged_btn)
    batch_layout.addWidget(main_window.remove_duplicates_within_btn)
    batch_layout.addWidget(main_window.remove_duplicates_between_btn)

    # Visualization section
    viz_group = QGroupBox("Visualization")
    viz_group.setStyleSheet("color: #61C7BF; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;")
    viz_layout = QVBoxLayout(viz_group)

    reference_layout = QHBoxLayout()
    reference_label = QLabel("Reference")
    reference_label.setStyleSheet("color: #61C7BF; font-family: 'Poppins'; font-size: 18pt;")

    main_window.reference_dropdown = QComboBox()
    main_window.reference_dropdown.setStyleSheet(
        "color: #61C7BF; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.reference_dropdown.currentIndexChanged.connect(main_window.reference_dropdown_value_changed)

    main_window.sil_checkbox = QCheckBox("SIL")
    main_window.sil_checkbox.setStyleSheet("color: #61C7BF; font-family: 'Poppins'; font-size: 18pt;")
    main_window.sil_checkbox.stateChanged.connect(main_window.sil_checkbox_value_changed)

    reference_layout.addWidget(reference_label)
    reference_layout.addWidget(main_window.reference_dropdown)
    reference_layout.addWidget(main_window.sil_checkbox)

    main_window.plot_spiketrains_btn = QPushButton("Plot MU spike trains")
    main_window.plot_spiketrains_btn.setStyleSheet(
        "color: #61C7BF; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.plot_spiketrains_btn.clicked.connect(main_window.plot_mu_spiketrains_button_pushed)

    main_window.plot_firingrates_btn = QPushButton("Plot MU firing rates")
    main_window.plot_firingrates_btn.setStyleSheet(
        "color: #61C7BF; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.plot_firingrates_btn.clicked.connect(main_window.plot_mu_firingrates_button_pushed)

    viz_layout.addLayout(reference_layout)
    viz_layout.addWidget(main_window.plot_spiketrains_btn)
    viz_layout.addWidget(main_window.plot_firingrates_btn)

    # Save section
    save_group = QGroupBox("Save the Edition")
    save_group.setStyleSheet("color: #f0f0f0; font-family: 'Poppins'; font-size: 18pt; font-weight: bold;")
    save_layout = QVBoxLayout(save_group)

    main_window.save_btn = QPushButton("Save")
    main_window.save_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.save_btn.clicked.connect(main_window.save_button_pushed)

    save_layout.addWidget(main_window.save_btn)

    # Add all sections to control panel
    control_layout.addWidget(file_group)
    control_layout.addWidget(batch_group)
    control_layout.addWidget(viz_group)
    control_layout.addWidget(save_group)
    control_layout.addStretch()


def setup_display_panel(main_window):
    """Set up the display panel with all controls and plots."""
    main_window.display_panel = QWidget()
    display_layout = QVBoxLayout(main_window.display_panel)

    # MU selection toolbar
    mu_toolbar = QWidget()
    mu_toolbar_layout = QHBoxLayout(mu_toolbar)

    mu_label = QLabel("MU displayed #")
    mu_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins'; font-size: 24pt; font-weight: bold;")

    main_window.mu_dropdown = QComboBox()
    main_window.mu_dropdown.setEnabled(False)
    main_window.mu_dropdown.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.mu_dropdown.currentIndexChanged.connect(main_window.mu_displayed_dropdown_value_changed)
    main_window.mu_dropdown.addItem("No MUs")

    main_window.flag_mu_btn = QPushButton("Flag MU for deletion")
    main_window.flag_mu_btn.setStyleSheet(
        "color: #FF0000; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.flag_mu_btn.clicked.connect(main_window.flag_mu_for_deletion_button_pushed)

    main_window.remove_outliers_single_btn = QPushButton("Remove outliers")
    main_window.remove_outliers_single_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.remove_outliers_single_btn.clicked.connect(main_window.remove_outliers_button_pushed)

    main_window.undo_btn = QPushButton("Undo")
    main_window.undo_btn.setStyleSheet(
        "color: #63D412; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.undo_btn.clicked.connect(main_window.undo_button_pushed)

    main_window.sil_info = QLineEdit()
    main_window.sil_info.setReadOnly(True)
    main_window.sil_info.setStyleSheet(
        "color: #ffffff; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )

    mu_toolbar_layout.addWidget(mu_label)
    mu_toolbar_layout.addWidget(main_window.mu_dropdown)
    mu_toolbar_layout.addWidget(main_window.flag_mu_btn)
    mu_toolbar_layout.addWidget(main_window.remove_outliers_single_btn)
    mu_toolbar_layout.addWidget(main_window.undo_btn)
    mu_toolbar_layout.addWidget(main_window.sil_info)

    # Action buttons
    action_buttons = QWidget()
    action_layout = QHBoxLayout(action_buttons)

    main_window.add_spikes_btn = QPushButton("Add spikes")
    main_window.add_spikes_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.add_spikes_btn.clicked.connect(main_window.add_spikes_button_pushed)

    main_window.delete_spikes_btn = QPushButton("Delete spikes")
    main_window.delete_spikes_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.delete_spikes_btn.clicked.connect(main_window.delete_spikes_button_pushed)

    main_window.delete_dr_btn = QPushButton("Delete DR")
    main_window.delete_dr_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.delete_dr_btn.clicked.connect(main_window.delete_dr_button_pushed)

    main_window.lock_spikes_btn = QPushButton("Lock spikes")
    main_window.lock_spikes_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.lock_spikes_btn.clicked.connect(main_window.lock_spikes_button_pushed)

    main_window.update_mu_filter_btn = QPushButton("Update MU filter")
    main_window.update_mu_filter_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.update_mu_filter_btn.clicked.connect(main_window.update_mu_filter_button_pushed)

    main_window.extend_mu_filter_btn = QPushButton("Extend MU filter")
    main_window.extend_mu_filter_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.extend_mu_filter_btn.clicked.connect(main_window.extend_mu_filter_button_pushed)

    action_layout.addWidget(main_window.add_spikes_btn)
    action_layout.addWidget(main_window.delete_spikes_btn)
    action_layout.addWidget(main_window.delete_dr_btn)
    action_layout.addWidget(main_window.lock_spikes_btn)
    action_layout.addWidget(main_window.update_mu_filter_btn)
    action_layout.addWidget(main_window.extend_mu_filter_btn)

    # Navigation buttons
    nav_buttons = QWidget()
    nav_layout = QHBoxLayout(nav_buttons)

    main_window.scroll_left_btn = QPushButton("< Scroll left")
    main_window.scroll_left_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.scroll_left_btn.clicked.connect(main_window.scroll_left_button_pushed)

    main_window.zoom_in_btn = QPushButton("Zoom in")
    main_window.zoom_in_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.zoom_in_btn.clicked.connect(main_window.zoom_in_button_pushed)

    main_window.zoom_out_btn = QPushButton("Zoom out")
    main_window.zoom_out_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.zoom_out_btn.clicked.connect(main_window.zoom_out_button_pushed)

    main_window.scroll_right_btn = QPushButton("Scroll right >")
    main_window.scroll_right_btn.setStyleSheet(
        "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
    )
    main_window.scroll_right_btn.clicked.connect(main_window.scroll_right_button_pushed)

    nav_layout.addWidget(main_window.scroll_left_btn)
    nav_layout.addWidget(main_window.zoom_in_btn)
    nav_layout.addWidget(main_window.zoom_out_btn)
    nav_layout.addWidget(main_window.scroll_right_btn)

    # Plots
    main_window.sil_plot = pg.PlotWidget()
    main_window.sil_plot.setBackground("#262626")
    main_window.sil_plot.setLabel("left", "SIL")
    main_window.sil_plot.getAxis("left").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.sil_plot.getAxis("bottom").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.sil_plot.getAxis("left").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.sil_plot.getAxis("bottom").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.sil_plot.setVisible(False)  # Initially hidden until SIL checkbox is checked

    main_window.spiketrain_plot = pg.PlotWidget()
    main_window.spiketrain_plot.setBackground("#262626")
    main_window.spiketrain_plot.setLabel("left", "Pulse train (au)")
    main_window.spiketrain_plot.setLabel("bottom", "Time (s)")
    main_window.spiketrain_plot.getAxis("left").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.spiketrain_plot.getAxis("bottom").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.spiketrain_plot.getAxis("left").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.spiketrain_plot.getAxis("bottom").setTextPen(pg.mkPen(color="#f0f0f0"))

    main_window.dr_plot = pg.PlotWidget()
    main_window.dr_plot.setBackground("#262626")
    main_window.dr_plot.setLabel("left", "Discharge rate (pps)")
    main_window.dr_plot.setLabel("bottom", "Time (s)")
    main_window.dr_plot.getAxis("left").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.dr_plot.getAxis("bottom").setPen(pg.mkPen(color="#f0f0f0"))
    main_window.dr_plot.getAxis("left").setTextPen(pg.mkPen(color="#f0f0f0"))
    main_window.dr_plot.getAxis("bottom").setTextPen(pg.mkPen(color="#f0f0f0"))

    # Add plots and controls to the display panel
    display_layout.addWidget(mu_toolbar)
    display_layout.addWidget(main_window.sil_plot, 1)  # The 1 is the stretch factor
    display_layout.addWidget(main_window.spiketrain_plot, 3)
    display_layout.addWidget(main_window.dr_plot, 2)
    display_layout.addWidget(action_buttons)
    display_layout.addWidget(nav_buttons)
