import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QScrollArea,
    QTabWidget,
    QFrame,
    QComboBox,
)

# Import custom components
from gui.ui.components import (
    CleanTheme,
    ActionButton,
    CleanCard,
    CollapsiblePanel,
    VisualizationPanel,
    FormField,
    SettingsGroup,
    SectionHeader,
    CleanScrollBar,
)


def setup_ui(main_window):
    """Setup the modern UI components for the MUedit Manual application."""
    # Set window properties
    main_window.setWindowTitle("MUedit - Manual Editing")
    main_window.setGeometry(100, 100, 1500, 850)
    main_window.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")

    # Configure PyQtGraph globally
    pg.setConfigOption("background", "w")  # White background
    pg.setConfigOption("foreground", CleanTheme.TEXT_PRIMARY)

    # Enable anti-aliasing for better looking plots
    pg.setConfigOption("antialias", True)

    # Create main widget and layout
    main_window.central_widget = QWidget()
    main_window.setCentralWidget(main_window.central_widget)
    main_layout = QHBoxLayout(main_window.central_widget)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(8)

    # Set up control panel and display panel
    setup_control_panel(main_window)
    setup_display_panel(main_window)

    # Add panels to main layout
    main_layout.addWidget(main_window.control_panel)
    main_layout.addWidget(main_window.display_panel, 1)  # The 1 is the stretch factor

    # Set up keyboard shortcuts
    main_window.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


def setup_control_panel(main_window):
    """Set up the control panel with all controls using modern UI components."""
    # Create a scrollable container for the control panel
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    # Apply clean scrollbar styling
    CleanScrollBar.apply(scroll_area)

    # Create the actual control panel container
    control_panel_widget = QWidget()
    control_panel_widget.setMinimumWidth(380)
    control_panel_widget.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")
    control_layout = QVBoxLayout(control_panel_widget)
    control_layout.setContentsMargins(5, 5, 5, 5)
    control_layout.setSpacing(15)

    # File selection section using SettingsGroup
    file_group = SettingsGroup("File Selection")

    # File selection with FormField
    file_select_layout = QHBoxLayout()
    file_select_layout.setSpacing(10)

    # Create file path field
    main_window.file_path_field = QLineEdit("File name")
    main_window.file_path_field.setReadOnly(True)
    main_window.file_path_field.setStyleSheet(
        f"""
        QLineEdit {{
            color: {CleanTheme.TEXT_PRIMARY};
            background-color: {CleanTheme.BG_CARD};
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
        }}
        """
    )

    # Select file button
    main_window.select_file_btn = ActionButton("Select file", primary=True)
    main_window.select_file_btn.clicked.connect(main_window.select_file_button_pushed)

    file_select_layout.addWidget(main_window.file_path_field, 1)  # 1 is stretch factor
    file_select_layout.addWidget(main_window.select_file_btn)

    # Custom field for file selection layout
    custom_field_widget = QWidget()
    custom_field_widget.setLayout(file_select_layout)
    file_group.add_field(custom_field_widget)

    control_layout.addWidget(file_group)

    # Create tab widget for sections
    main_window.tabs = create_tab_widget()

    # Add the different tabs
    mu_tab = create_mu_selection_tab(main_window)
    batch_tab = create_batch_processing_tab(main_window)
    viz_tab = create_visualization_tab(main_window)

    main_window.tabs.addTab(mu_tab, "MU Selection")
    main_window.tabs.addTab(batch_tab, "Batch Processing")
    main_window.tabs.addTab(viz_tab, "Visualization")
    control_layout.addWidget(main_window.tabs)

    # Save section using SettingsGroup
    save_group = SettingsGroup("Save the Edition")

    main_window.save_btn = ActionButton("Save", primary=True)
    main_window.save_btn.clicked.connect(main_window.save_button_pushed)

    save_group.add_field(main_window.save_btn)
    control_layout.addWidget(save_group)

    # Set the control panel as the scroll area's widget
    scroll_area.setWidget(control_panel_widget)

    # Set the scroll area as the control panel
    main_window.control_panel = scroll_area


def create_tab_widget():
    """Create a styled tab widget."""
    tabs = QTabWidget()
    tabs.setStyleSheet(
        f"""
        QTabWidget::pane {{
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 8px;
            background-color: {CleanTheme.BG_CARD};
        }}
        QTabBar::tab {{
            background-color: {CleanTheme.BG_MAIN};
            color: {CleanTheme.TEXT_PRIMARY};
            border: 1px solid {CleanTheme.BORDER};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 8px 10px;
            margin-right: 1px;
            font-size: 11px;
            min-width: 100px;
        }}
        QTabBar::tab:selected {{
            background-color: {CleanTheme.BG_CARD};
            border-bottom: 1px solid {CleanTheme.BG_CARD};
        }}
        """
    )
    # Set the minimum width for the tabs
    tabs.setMinimumWidth(380)
    return tabs


def create_mu_selection_tab(main_window):
    """Create the Motor Unit Selection tab."""
    mu_tab = QWidget()
    mu_tab.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    mu_layout = QVBoxLayout(mu_tab)
    mu_layout.setContentsMargins(15, 15, 15, 15)
    mu_layout.setSpacing(10)

    # MU selection content
    mu_header = SectionHeader("Motor Unit Selection")
    mu_layout.addWidget(mu_header)

    # Create a scroll area for MU checkboxes
    mu_scroll_area = QScrollArea()
    mu_scroll_area.setWidgetResizable(True)
    mu_scroll_area.setFrameShape(QFrame.NoFrame)
    CleanScrollBar.apply(mu_scroll_area)

    checkbox_container = QWidget()
    checkbox_container.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    main_window.mu_checkbox_layout = QVBoxLayout(checkbox_container)
    main_window.mu_checkbox_layout.setContentsMargins(0, 0, 0, 0)
    main_window.mu_checkbox_layout.setSpacing(5)
    main_window.mu_checkboxes = []  # Store references to checkboxes

    # Initially add a label indicating no MUs
    no_mu_label = QLabel("No MUs loaded")
    no_mu_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY}; font-size: 13px;")
    main_window.mu_checkbox_layout.addWidget(no_mu_label)
    main_window.mu_checkbox_layout.addStretch()

    mu_scroll_area.setWidget(checkbox_container)
    mu_layout.addWidget(mu_scroll_area)

    # Add flag button in the MU selection tab
    main_window.flag_mu_btn = ActionButton("Flag selected MU(s) for deletion", primary=False)
    main_window.flag_mu_btn.clicked.connect(main_window.flag_mu_for_deletion_button_pushed)
    mu_layout.addWidget(main_window.flag_mu_btn)

    return mu_tab


def create_batch_processing_tab(main_window):
    """Create the Batch Processing tab."""
    batch_tab = QWidget()
    batch_tab.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    batch_layout = QVBoxLayout(batch_tab)
    batch_layout.setContentsMargins(15, 15, 15, 15)
    batch_layout.setSpacing(10)

    # Batch processing content
    batch_header = SectionHeader("Batch Processing")
    batch_layout.addWidget(batch_header)

    # Create batch processing buttons
    button_configs = [
        ("1 - Remove all the outliers", main_window.remove_all_outliers_button_pushed),
        ("2 - Update all MU filters", main_window.update_all_mu_filters_button_pushed),
        ("3 - Remove flagged MU", main_window.remove_flagged_mu_button_pushed),
        ("4 - Remove duplicates within grids", main_window.remove_duplicates_within_grids_button_pushed),
        ("5 - Remove duplicates between grids", main_window.remove_duplicates_between_grids_button_pushed),
    ]

    for text, handler in button_configs:
        btn = ActionButton(text, primary=False)
        btn.clicked.connect(handler)
        batch_layout.addWidget(btn)

        # Store button references
        if text.startswith("1 -"):
            main_window.remove_outliers_btn = btn
        elif text.startswith("2 -"):
            main_window.update_filters_btn = btn
        elif text.startswith("3 -"):
            main_window.remove_flagged_btn = btn
        elif text.startswith("4 -"):
            main_window.remove_duplicates_within_btn = btn
        elif text.startswith("5 -"):
            main_window.remove_duplicates_between_btn = btn

    batch_layout.addStretch()

    return batch_tab


def create_visualization_tab(main_window):
    """Create the Visualization tab."""
    viz_tab = QWidget()
    viz_tab.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    viz_layout = QVBoxLayout(viz_tab)
    viz_layout.setContentsMargins(15, 15, 15, 15)
    viz_layout.setSpacing(10)

    # Visualization content
    viz_header = SectionHeader("Visualization")
    viz_layout.addWidget(viz_header)

    # Reference selection - create a panel for this
    ref_panel = CollapsiblePanel("Reference Settings")
    ref_contents = QWidget()
    ref_layout = QHBoxLayout(ref_contents)
    ref_layout.setSpacing(10)

    reference_label = QLabel("Reference")
    reference_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")

    # Create a dropdown for reference selection
    main_window.reference_dropdown = QComboBox()
    main_window.reference_dropdown.setStyleSheet(
        f"""
        QComboBox {{
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 4px;
            padding: 5px;
            background-color: {CleanTheme.BG_CARD};
            min-height: 25px;
        }}
        """
    )
    main_window.reference_dropdown.currentIndexChanged.connect(main_window.reference_dropdown_value_changed)

    main_window.sil_checkbox = QCheckBox("SIL")
    main_window.sil_checkbox.setStyleSheet(
        f"""
        QCheckBox {{
            color: {CleanTheme.TEXT_PRIMARY};
        }}
        QCheckBox::indicator {{
            width: 15px;
            height: 15px;
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 3px;
        }}
        QCheckBox::indicator:checked {{
            background-color: #4C72B0;
            border: 1px solid #4C72B0;
        }}
        """
    )
    main_window.sil_checkbox.stateChanged.connect(main_window.sil_checkbox_value_changed)

    ref_layout.addWidget(reference_label)
    ref_layout.addWidget(main_window.reference_dropdown, 1)  # 1 is stretch factor
    ref_layout.addWidget(main_window.sil_checkbox)

    ref_panel.add_widget(ref_contents)
    viz_layout.addWidget(ref_panel)

    # Create visualization buttons panel
    button_panel = CollapsiblePanel("Plot Options")

    # Add plot buttons to the panel
    main_window.plot_spiketrains_btn = ActionButton("Plot MU spike trains", primary=False)
    main_window.plot_spiketrains_btn.clicked.connect(main_window.plot_mu_spiketrains_button_pushed)
    button_panel.add_widget(main_window.plot_spiketrains_btn)

    main_window.plot_firingrates_btn = ActionButton("Plot MU firing rates", primary=False)
    main_window.plot_firingrates_btn.clicked.connect(main_window.plot_mu_firingrates_button_pushed)
    button_panel.add_widget(main_window.plot_firingrates_btn)

    viz_layout.addWidget(button_panel)
    viz_layout.addStretch()

    return viz_tab


def setup_display_panel(main_window):
    """Set up the display panel with all controls and plots using modern UI components."""
    # Use a VisualizationPanel instead of a basic CleanCard for better semantics
    main_window.display_panel = VisualizationPanel("EMG Signal Analysis")

    # Create main container for all visualization elements
    display_widget = QWidget()
    display_layout = QVBoxLayout(display_widget)
    display_layout.setContentsMargins(0, 0, 0, 0)
    display_layout.setSpacing(15)

    # SIL info display
    main_window.sil_info = QLineEdit()
    main_window.sil_info.setReadOnly(True)
    main_window.sil_info.setStyleSheet(
        f"""
        QLineEdit {{
            color: {CleanTheme.TEXT_PRIMARY};
            background-color: {CleanTheme.BG_CARD};
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
        }}
        """
    )
    display_layout.addWidget(main_window.sil_info)

    # Create a scroll area for plots when multiple MUs are selected
    plots_scroll_area = QScrollArea()
    plots_scroll_area.setWidgetResizable(True)
    plots_scroll_area.setFrameShape(QFrame.NoFrame)
    CleanScrollBar.apply(plots_scroll_area)

    main_window.plots_container = QWidget()
    main_window.plots_container.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    main_window.plots_layout = QVBoxLayout(main_window.plots_container)
    main_window.plots_layout.setContentsMargins(0, 0, 0, 0)
    main_window.plots_layout.setSpacing(10)
    plots_scroll_area.setWidget(main_window.plots_container)
    main_window.plots_scroll_area = plots_scroll_area

    # Create the plots with a helper function
    main_window.sil_plot = create_plot_widget("SIL", "")
    main_window.sil_plot.setVisible(False)  # Initially hidden until SIL checkbox is checked

    main_window.spiketrain_plot = create_plot_widget("Pulse train (au)", "Time (s)")
    main_window.dr_plot = create_plot_widget("Discharge rate (pps)", "Time (s)")

    # Add plots to the layout
    main_window.plots_layout.addWidget(main_window.sil_plot)
    main_window.plots_layout.addWidget(main_window.spiketrain_plot)
    main_window.plots_layout.addWidget(main_window.dr_plot)

    display_layout.addWidget(plots_scroll_area, 1)  # 1 is stretch factor

    # Action buttons - use a card with a proper title
    action_card = CleanCard()
    action_card.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")

    # Add header to the card
    action_header = SectionHeader("Editing Actions")
    action_card.content_layout.addWidget(action_header)

    # Add button container
    action_container = QWidget()
    action_container.setMaximumHeight(60)
    action_layout = QHBoxLayout(action_container)
    action_layout.setContentsMargins(0, 0, 0, 0)
    action_layout.setSpacing(8)

    # Define all action buttons
    action_button_configs = [
        ("Add spikes", main_window.add_spikes_button_pushed, "add_spikes_btn"),
        ("Delete spikes", main_window.delete_spikes_button_pushed, "delete_spikes_btn"),
        ("Delete DR", main_window.delete_dr_button_pushed, "delete_dr_btn"),
        ("Lock spikes", main_window.lock_spikes_button_pushed, "lock_spikes_btn"),
        ("Update MU filter", main_window.update_mu_filter_button_pushed, "update_mu_filter_btn"),
        ("Extend MU filter", main_window.extend_mu_filter_button_pushed, "extend_mu_filter_btn"),
        ("Remove outliers", main_window.remove_outliers_button_pushed, "remove_outliers_single_btn"),
        ("Undo", main_window.undo_button_pushed, "undo_btn"),
    ]

    # Create action buttons and store references
    for text, handler, attr_name in action_button_configs:
        btn = ActionButton(text, primary=False)
        btn.clicked.connect(handler)
        btn.setMinimumHeight(36)
        btn.setMaximumHeight(36)
        action_layout.addWidget(btn)
        # Store reference to button in main_window
        setattr(main_window, attr_name, btn)

    action_card.content_layout.addWidget(action_container)
    display_layout.addWidget(action_card)

    # Navigation buttons - simple row of buttons in a frame
    nav_frame = QFrame()
    nav_frame.setFrameShape(QFrame.StyledPanel)
    nav_frame.setStyleSheet(
        f"""
        QFrame {{
            background-color: {CleanTheme.BG_CARD};
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 8px;
        }}
        """
    )

    nav_layout = QHBoxLayout(nav_frame)
    nav_layout.setContentsMargins(10, 10, 10, 10)
    nav_layout.setSpacing(15)

    # Define navigation buttons
    nav_button_configs = [
        ("< Scroll left", main_window.scroll_left_button_pushed, "scroll_left_btn"),
        ("Zoom in", main_window.zoom_in_button_pushed, "zoom_in_btn"),
        ("Zoom out", main_window.zoom_out_button_pushed, "zoom_out_btn"),
        ("Scroll right >", main_window.scroll_right_button_pushed, "scroll_right_btn"),
    ]

    # Create navigation buttons and store references
    for text, handler, attr_name in nav_button_configs:
        btn = ActionButton(text, primary=False)
        btn.clicked.connect(handler)
        btn.setMinimumWidth(btn.sizeHint().width() + 20)  # Make buttons slightly wider
        btn.setMinimumHeight(36)
        nav_layout.addWidget(btn)
        # Store reference to button in main_window
        setattr(main_window, attr_name, btn)

    display_layout.addWidget(nav_frame)

    # Add all visualization elements to the panel
    main_window.display_panel.set_plot_widget(display_widget)


def create_plot_widget(y_label, x_label=""):
    """Create a standardized plot widget with consistent styling."""
    plot = pg.PlotWidget()
    plot.setBackground("w")  # White background
    if y_label:
        plot.setLabel("left", y_label)
    if x_label:
        plot.setLabel("bottom", x_label)

    # Style the axes
    plot.getAxis("left").setPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))
    plot.getAxis("bottom").setPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))
    plot.getAxis("left").setTextPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))
    plot.getAxis("bottom").setTextPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))

    # Add grid
    plot.showGrid(x=True, y=True, alpha=0.3)

    return plot


def create_mu_checkbox(main_window, array_idx, mu_idx, text, sil_value, is_checked=False):
    """Helper function to create a styled checkbox for motor unit selection."""
    checkbox = QCheckBox(text)
    checkbox.setStyleSheet(
        f"""
        QCheckBox {{
            color: {CleanTheme.TEXT_PRIMARY};
            font-size: 13px;
            padding: 2px 0;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 3px;
        }}
        QCheckBox::indicator:checked {{
            background-color: #4C72B0;
            border: 1px solid #4C72B0;
        }}
        """
    )
    checkbox.setObjectName(f"Array_{array_idx+1}_MU_{mu_idx+1}")
    checkbox.setChecked(is_checked)
    checkbox.stateChanged.connect(main_window.mu_checkbox_state_changed)

    return checkbox
