import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGraphicsSceneMouseEvent,
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
    QListView, # moy
    QSizePolicy,
    QSpacerItem,
    QApplication,
    QLayout,
    QToolButton,
)
from PyQt5.QtGui  import QIcon
from PyQt5.QtCore import QSize, QTimer  
from pathlib import Path

# Import custom components
from ui.components import (
    CleanTheme,
    ActionButton,
    CleanCard,
    CollapsiblePanel,
    VisualizationPanelForEdit,
    Sidebar,
    SettingsGroup,
    SectionHeader,
    CleanScrollBar,
    GoodSlider,
)
from ui.components.ActionButtonedit import ActionButtonedit
class FixedPopupComboBox(QComboBox): # set a new class for dropout moy
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        popup_view = QListView(self) # set xuanting
        popup_view.setStyleSheet("""
            QListView::item:hover,
            QListView::item:selected { background: #E0E0E0; color: black; }
        """)
        self.setView(popup_view)

    def showPopup(self): # use the bar location and move the dropdown under it
        super().showPopup()
        popup = self.view().window()
        geo   = popup.geometry()
        geo.moveTopLeft(self.mapToGlobal(
            self.rect().bottomLeft()
        ))
        popup.setGeometry(geo)

def setup_ui(main_window):
    """Setup the modern UI components for the MUedit Manual application."""
    
    # Set window properties
    main_window.setWindowTitle("MUedit - Manual Editing")
    main_window.setGeometry(100, 100, 1500, 850)
    main_window.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")

    # Configure PyQtGraph globally
    pg.setConfigOption("background", "w")  # White background
    pg.setConfigOption("foreground", CleanTheme.TEXT_PRIMARY)

    # Disable anti-aliasing for better performance
    pg.setConfigOption("antialias", False)

    # Create main widget and layout
    main_window.central_widget = QWidget()
    main_window.setCentralWidget(main_window.central_widget)
    main_layout = QHBoxLayout(main_window.central_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(8)

    # Set up control panel and display panel
    setup_display_panel(main_window)
    setup_control_panel(main_window)
    attach_control_pannel_to_sidebar(main_window)

    # Add panels to main layout
    
    main_layout.addWidget(main_window.display_panel, 1)  # The 1 is the stretch factor
    
    # Set up keyboard shortcuts
    main_window.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

from PyQt5.QtGui import QFont # alex
# Apply Sil
def set_standard_label_style(label, size=10, bold=False):
    font = QFont("Segoe UI")
    font.setPointSize(size)
    font.setBold(bold)
    label.setFont(font)
    label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")


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
    control_panel_widget.setStyleSheet(f"background-color: {CleanTheme.BG_SIDEBAR};")
    control_layout = QVBoxLayout(control_panel_widget)
    control_layout.setContentsMargins(0, 0, 0, 0)

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
    main_window.select_file_btn = ActionButtonedit("Select file", primary=True)
    main_window.select_file_btn.clicked.connect(main_window.select_file_button_pushed)

    file_select_layout.addWidget(main_window.file_path_field, 1)  # 1 is stretch factor
    file_select_layout.addWidget(main_window.select_file_btn)

    # Custom field for file selection layout
    custom_field_widget = QWidget()
    custom_field_widget.setLayout(file_select_layout)
    file_group.add_field(custom_field_widget)

    control_layout.addWidget(file_group)

    file_group.setVisible(False)

    # ===================== Tabs: MU Selection / Batch / Visualization =====================
    main_window.tabs = create_tab_widget()

    # Add the different tabs
    mu_tab = create_mu_selection_tab(main_window)
    batch_tab = create_batch_processing_tab(main_window)
    viz_tab = create_visualization_tab(main_window)

    main_window.tabs.tabBar().setVisible(False)

    main_window.tabs.addTab(mu_tab, "MU Selection")
    main_window.tabs.addTab(batch_tab, "Batch Processing")
    main_window.tabs.addTab(viz_tab, "Visualization")
    control_layout.addWidget(main_window.tabs)

    main_window.mu_edit_tabs = main_window.tabs

    # Save section using SettingsGroup
    save_group = SettingsGroup("Save the Edition")

    main_window.save_btn = ActionButtonedit("Save", primary=True)
    main_window.save_btn.clicked.connect(main_window.save_button_pushed)

    save_group.add_field(main_window.save_btn)
    control_layout.addWidget(save_group)

    save_group.hide()

    # Set the control panel as the scroll area's widget
    scroll_area.setWidget(control_panel_widget)

    # Set the scroll area as the control panel
    main_window.control_panel = scroll_area

def attach_control_pannel_to_sidebar(main_window):
    """
    Insert the MU-Editing subpanel (tabs + sub-buttons) into the app's left Sidebar,
    right below the top app title/buttons.
    """    
    sidebar = find_sidebar(main_window)
    if not sidebar:
        return
    
    # Subpanel holds the three sub-buttons and the tab stack
    subpanel = QWidget()
    subpanel.setVisible(False) # shown only when "MU Editing" is active
    sub_lay = QVBoxLayout(subpanel)
    sub_lay.setSpacing(6)

    sub_btns = []
    
    def _switch(idx:int):    
        """Switch the stacked tabs and update button active state."""
        main_window.tabs.setCurrentIndex(idx)
        for i, btn in enumerate(sub_btns):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def _sub_btn(text, idx):
        """
        Create a tab-like button:
        - primary=False for light style
        - tabs=True enables the special active-state stylesheet in ActionButtonedit
        """
        b = ActionButtonedit(text, primary=False, tabs=True)
        b.setFixedHeight(28)
        b.clicked.connect(lambda _, i=idx: _switch(i))
        sub_lay.addWidget(b)
        sub_btns.append(b)
        return b    
    
    # Create the three sub-buttons and default to the first tab
    _sub_btn("MU Selection",    0).click()
    _sub_btn("Batch Processing",1)
    _sub_btn("Visualization",   2)
    
    sub_lay.addWidget(main_window.control_panel)

    sidebar.layout.insertWidget(2, subpanel, 999)

    main_window.sub_panel = subpanel
    
    def list_widgets(layout: QLayout, depth=0):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            prefix = "  " * depth
            if item.widget():
                w = item.widget()
                name = w.objectName() or w.__class__.__name__
                print(f"{prefix}- {name}")
            elif item.layout():
                print(f"{prefix}- SubLayout:")
                list_widgets(item.layout(), depth+1)
        for i in range(sidebar.layout.count()):
            item    = sidebar.layout.itemAt(i)
            w       = item.widget()
            name    = w.objectName() if w else item.layout().__class__.__name__
            factor  = sidebar.layout.stretch(i)
            print(f"index={i}, {name}, stretch={factor}")

def create_tab_widget():
    """Create a styled tab widget."""
    tabs = QTabWidget()
    tabs.setStyleSheet(
        f"""
        QTabWidget::pane {{
            border-radius: 8px;
            background-color: {CleanTheme.BG_CARD};
        }}
        QTabBar::tab {{
            background-color: {CleanTheme.BG_MAIN};
            color: {CleanTheme.TEXT_PRIMARY};
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
    tabs.setMaximumWidth(320)
    return tabs


def create_mu_selection_tab(main_window):
    """Create the Motor Unit Selection tab."""
    mu_tab = QWidget()
    mu_tab.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    mu_layout = QVBoxLayout(mu_tab)
    mu_layout.setContentsMargins(0, 0, 0, 0)
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
    main_window.mu_checkbox_layout.setContentsMargins(0, 0, 2, 0)
    main_window.mu_checkbox_layout.setSpacing(5)
    main_window.mu_checkboxes = []  # Store references to checkboxes

    # Initially add a label indicating no MUs
    no_mu_label = QLabel("No MUs loaded")
    set_standard_label_style(no_mu_label, size=13, bold=False)
    main_window.mu_checkbox_layout.addWidget(no_mu_label)
    main_window.mu_checkbox_layout.addStretch()

    mu_scroll_area.setWidget(checkbox_container)
    mu_layout.addWidget(mu_scroll_area)

    # Add flag button in the MU selection tab
    main_window.flag_mu_btn = ActionButtonedit("Flag selected MU(s) for deletion", primary=False, blue=True)
    main_window.flag_mu_btn.clicked.connect(main_window.flag_mu_for_deletion_button_pushed)
    
    # Add unflag button in the MU selection tab
    main_window.unflag_mu_btn = ActionButtonedit("UnFlag selected MU(s) for deletion", primary=False, blue=True)
    main_window.unflag_mu_btn.clicked.connect(main_window.unflag_mu_for_deletion_button_pushed)

    mu_layout.addWidget(main_window.flag_mu_btn)
    mu_layout.addWidget(main_window.unflag_mu_btn)

    return mu_tab


def create_batch_processing_tab(main_window):
    """Create the Batch Processing tab."""
    batch_tab = QWidget()
    batch_tab.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    batch_layout = QVBoxLayout(batch_tab)
    batch_layout.setSpacing(10)
    batch_layout.setContentsMargins(0, 0, 0, 0)

    # Batch processing content
    batch_header = SectionHeader("Batch Processing")
    batch_layout.addWidget(batch_header)

    # Label, handler, attribute name for later access    
    action_batch_configs = [
    ("1 - Remove all the outliers", main_window.remove_all_outliers_button_pushed, "remove_outliers_all_btn"),
    ("2 - Update all MU filters", main_window.update_all_mu_filters_button_pushed, "update_mu_filter_all_btn"),
    ("3 - Remove flagged MU", main_window.remove_flagged_mu_button_pushed, "remove_flagged_mu_btn"),
    ("4 - Remove duplicates within grids", main_window.remove_duplicates_within_grids_button_pushed, "remove_duplicates_within_btn"),
    ("5 - Remove duplicates between grids", main_window.remove_duplicates_between_grids_button_pushed, "remove_duplicates_between_btn"),
    ]

    for label, handler, attr_name in action_batch_configs:
        btn = ActionButtonedit(label, primary=False)
        btn.clicked.connect(handler)
        btn.setMinimumHeight(34)
        btn.setMaximumHeight(34)
        batch_layout.addWidget(btn)
        setattr(main_window, attr_name, btn)
    
    batch_layout.addStretch(1)

    return batch_tab


def create_visualization_tab(main_window):
    """Create the Visualization tab."""
    viz_tab = QWidget()
    viz_tab.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};")
    viz_layout = QVBoxLayout(viz_tab)
    viz_layout.setSpacing(10)
    viz_layout.setContentsMargins(0, 0, 0, 0)

    # Visualization content
    viz_header = SectionHeader("Visualization")
    viz_layout.addWidget(viz_header)

    # Reference selection - create a panel for this
    ref_panel = CollapsiblePanel("Reference Settings")
    ref_contents = QWidget()
    ref_layout = QVBoxLayout(ref_contents)
    ref_layout.setContentsMargins(0, 0, 0, 0)
    ref_layout.setSpacing(8)

    row1 = QWidget()
    row1_layout = QHBoxLayout(row1)
    row1_layout.setContentsMargins(0, 0, 0, 0)
    row1_layout.setSpacing(6)

    reference_label = QLabel("Reference")
    set_standard_label_style(reference_label)

    # Create a dropdown for reference selection
    main_window.reference_dropdown = FixedPopupComboBox() # change to new class moy
    main_window.reference_dropdown.setMinimumHeight(28)
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

    row1_layout.addWidget(reference_label)
    row1_layout.addWidget(main_window.reference_dropdown, 1)
    ref_layout.addWidget(row1)   
    from ui.components import ToggleSwitch
    row2 = QWidget()
    row2_lay = QHBoxLayout(row2)
    row2_lay.setContentsMargins(0,0,0,0)
    row2_lay.setSpacing(6)
    apply_lbl = QLabel("Apply SIL")                 
    set_standard_label_style(apply_lbl)

    # SIL toggle (Apply SIL)
    main_window.sil_switch = ToggleSwitch()        
    main_window.sil_switch.toggled.connect(    
        main_window.sil_checkbox_value_changed)
    main_window.sil_checkbox = main_window.sil_switch
    row2_lay.addWidget(apply_lbl)
    row2_lay.addStretch(1)               
    row2_lay.addWidget(main_window.sil_switch)

    ref_layout.addWidget(row2)  

    ref_panel.add_widget(ref_contents)
    viz_layout.addWidget(ref_panel)
    main_window.action_buttons["sil_checkbox_value_changed"] = main_window.sil_switch

    # Create visualization buttons panel
    button_panel = CollapsiblePanel("Plot Options")

    # Add plot buttons to the panel
    main_window.plot_spiketrains_btn = ActionButtonedit("Plot MU spike trains", primary=False, blue=True)
    main_window.plot_spiketrains_btn.clicked.connect(main_window.plot_mu_spiketrains_button_pushed)
    button_panel.add_widget(main_window.plot_spiketrains_btn)

    main_window.plot_firingrates_btn = ActionButtonedit("Plot MU firing rates", primary=False, blue=True)
    main_window.plot_firingrates_btn.clicked.connect(main_window.plot_mu_firingrates_button_pushed)
    button_panel.add_widget(main_window.plot_firingrates_btn)
    
    
    row3 = QWidget()
    row3_lay = QHBoxLayout(row3)
    row3_lay.setContentsMargins(0,0,0,0)
    row3_lay.setSpacing(6)
    
    aa_lbl = QLabel("Always Anti-Aliasing on Plot")                 
    set_standard_label_style(aa_lbl)
    row3_lay.setContentsMargins(0,0,0,0)
    row3_lay.setSpacing(6)
    row3_lay.addWidget(aa_lbl)

    main_window.aa_switch = ToggleSwitch()        
    main_window.aa_switch.toggled.connect(main_window.aa_checkbox_value_changed)
    row3_lay.addWidget(main_window.aa_switch)
    
    button_panel.add_widget(row3)
    
    # Spike plot order toggle (ascending recruitment)
    row4 = QWidget()
    row4_lay = QHBoxLayout(row4)
    row4_lay.setContentsMargins(0,0,0,0)
    row4_lay.setSpacing(6)
    
    sps_lbl = QLabel("Spikes Plot Ascending")                 
    set_standard_label_style(sps_lbl)
    row4_lay.setContentsMargins(0,0,0,0)
    row4_lay.setSpacing(6)
    row4_lay.addWidget(sps_lbl)

    main_window.sps_switch = ToggleSwitch(checked=True)        
    main_window.sps_switch.toggled.connect(main_window.sps_checkbox_value_changed)
    row4_lay.addWidget(main_window.sps_switch)
    
    button_panel.add_widget(row4)

    viz_layout.addWidget(button_panel)
    viz_layout.addStretch()

    return viz_tab


def setup_display_panel(main_window):
    """Set up the display panel with all controls and plots using modern UI components."""
    # Use a VisualizationPanelForEdit instead of a basic CleanCard for better semantics
    # main_window.setStyleSheet(f"border: 1px solid blue;")
    main_window.display_panel = VisualizationPanelForEdit("EMG Signal Edit")
    title_lbl = main_window.display_panel.title_label  
    # main_window.display_panel.setStyleSheet("border: 1px solid red;")

    font = title_lbl.font()
    font.setPointSize(20)       
    font.setBold(True)      
    title_lbl.setFont(font)

    main_window.help_button = QToolButton()
    main_window.help_button.setText("?")
    main_window.help_button.setFixedSize(30, 30)
    main_window.help_button.setStyleSheet("""
        QToolButton {
            font-weight: bold;
            font-size: 22px;
            border: 2px solid #f0f0f0;
            border-radius: 12px;
            background-color: white;
        }
        QToolButton:hover {
            background-color: #ddd;
        }
    """)
    main_window.help_button.clicked.connect(
        main_window.help_button_pushed
    )
    
    main_window.select_file_title_btn = ActionButtonedit("Press here to select file", primary=True)
    main_window.select_file_title_btn.set_blue()
    main_window.select_file_title_btn.setFixedHeight(40)
    select_btn = main_window.select_file_title_btn
    main_window.select_file_title_btn.clicked.connect(
        main_window.select_file_button_pushed
    )

    save_btn = ActionButtonedit("Save", primary=True) 
    save_btn.setFixedHeight(40)
    save_btn.clicked.connect(main_window.save_button_pushed)
    main_window.floating_save_btn = save_btn
    
    saveas_btn = ActionButtonedit("Save As", primary=True) 
    saveas_btn.setFixedHeight(40)
    saveas_btn.clicked.connect(main_window.saveas_button_pushed)
    main_window.floating_saveas_btn = saveas_btn

    select_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) 
    save_btn.setSizePolicy(QSizePolicy.Fixed,     QSizePolicy.Fixed)
    saveas_btn.setSizePolicy(QSizePolicy.Fixed,     QSizePolicy.Fixed)  

    hdr = QWidget()
    h_lay = QHBoxLayout(hdr)
    h_lay.setContentsMargins(0, 0, 15, 0)
    h_lay.setSpacing(5)

    spacer = QWidget()
    spacer.setFixedWidth(12)

    # h_lay.addWidget(main_window.display_panel.title_label)  
    main_window.display_panel.header.layout.addWidget(hdr)
    h_lay.addWidget(main_window.help_button)
    h_lay.addStretch()
    h_lay.addWidget(select_btn) 
    h_lay.addWidget(spacer)
    h_lay.addWidget(save_btn)
    h_lay.addWidget(saveas_btn)

    # main_window.display_panel.content_layout.insertWidget(0, hdr)

    # Create main container for all visualization elements
    display_widget = QWidget()
    display_layout = QVBoxLayout(display_widget)
    display_layout.setContentsMargins(0, 0, 0, 0)
    display_layout.setSpacing(10)

    ICON_DIR = Path(__file__).resolve().parent.parent / "public"
    def _ico(name):    
        return QIcon(str(ICON_DIR / f"{name}.png"))
    main_window.undo_title_btn = ActionButtonedit("Undo", icon=_ico("undo"), primary=False) # alex
    main_window.undo_title_btn.setFixedHeight(24)
    main_window.undo_title_btn.clicked.connect(main_window.undo_button_pushed)
    main_window.redo_title_btn = ActionButtonedit("Redo", icon=_ico("redu"), primary=False) # new redo btn moy
    main_window.redo_title_btn.setFixedHeight(24)
    main_window.redo_title_btn.clicked.connect(main_window.redo_button_pushed)

    for btn, name in (
        (main_window.undo_title_btn, "undo"),
        (main_window.redo_title_btn, "redo")):
        btn.setText("")           
        btn.setIcon(_ico(name))      
        btn.setIconSize(QSize(18, 18))
        btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #eee;
            }
        """)
    
    # Zoom Silder
    main_window.zoom_slider = GoodSlider(default=0, on_value_changed=main_window.slider_value_changed, display_value=False)
    
    undo_row = QWidget()
    undo_row.setObjectName("undo_row")
    undo_layout = QHBoxLayout(undo_row)
    undo_layout.setContentsMargins(0, 0, 0, 0)
    undo_layout.setSpacing(0) 
    
    undo_layout.addStretch(2)
    undo_layout.addWidget(main_window.undo_title_btn, stretch=1)
    undo_layout.addWidget(main_window.redo_title_btn, stretch=1) # new redo btn moy
    undo_layout.addStretch(18)
    undo_layout.addWidget(main_window.zoom_slider, stretch=6)
    subheader = main_window.display_panel.subheader

    subheader.title_label.hide()
    subheader_layout = subheader.layout
    subheader_layout.addWidget(undo_row)
    subheader.setObjectName("subheader")
    subheader.setStyleSheet("""
        QWidget {
            border-bottom: 2px solid qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop: 0 transparent,
                stop: 0.05 transparent,
                stop: 0.051 #f0f0f0,
                stop: 0.949 #f0f0f0,
                stop: 0.95 transparent,
                stop: 1 transparent
            );
        }
    """)


    help_sil_layout = QVBoxLayout()
    help_sil_layout.setContentsMargins(0, 0, 0, 0)
    help_sil_layout.setSpacing(0)

    help_layout = QHBoxLayout()
    help_layout.setContentsMargins(0, 15, 0, 0)
    help_layout.addStretch()
    help_widget = QWidget()
    help_widget.setLayout(help_layout)
    help_sil_layout.addWidget(help_widget)

    # SIL info display
    main_window.sil_info = QLabel("Tile and SIL value")
    main_window.sil_info.setStyleSheet(
        f"""
        QLabel {{
            color: {CleanTheme.TEXT_PRIMARY};
            padding: 8px;
            font-size: 20px;
        }}
        """
    )
    main_window.sil_info.setAlignment(Qt.AlignCenter)
    help_sil_layout.addWidget(main_window.sil_info, alignment = Qt.AlignCenter)
    
    display_layout.addLayout(help_sil_layout)

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
    main_window.sil_plot = create_plot_widget(main_window, "SIL", "")
    main_window.sil_plot.setVisible(False)  # Initially hidden until SIL checkbox is checked

    main_window.spiketrain_plot = create_plot_widget(main_window, "Pulse train (au)", "Time (s)")
    main_window.dr_plot = create_plot_widget(main_window, "Discharge rate (pps)", "Time (s)")

    # Add plots to the layout
    main_window.plots_layout.addWidget(main_window.sil_plot)
    main_window.plots_layout.addWidget(main_window.spiketrain_plot)
    main_window.plots_layout.addWidget(main_window.dr_plot)

    display_layout.addWidget(plots_scroll_area, 1)  # 1 is stretch factor
    # horizontal pan‑slider just below all plots moy
    from PyQt5.QtWidgets import QSlider
    main_window.pan_slider = QSlider(Qt.Horizontal, parent=display_widget)
    main_window.pan_slider.setRange(0, 1000)      # 0 = far left, 1000 = far right
    main_window.pan_slider.setSingleStep(1)
    main_window.pan_slider.setPageStep(10)
    main_window.pan_slider.setFixedHeight(18)
    main_window.pan_slider.setStyleSheet("""
        QSlider::handle:horizontal {
            background-color: #8E8E93;
            width: 150px;
            height: 4px;
            margin: -4px 0;
            border-radius: 6px;
        }

        QSlider::groove:horizontal {
            background: #E5E5EA;
            height: 4px;
            border-radius: 2px;
        }

        QSlider::sub-page:horizontal {
            background: #BEBEBF;E5E5EA
            border-radius: 2px;
        }
    """)

    main_window.pan_slider.valueChanged.connect(main_window.pan_slider_changed)
    mid = (main_window.pan_slider.minimum() + main_window.pan_slider.maximum()) // 2
    main_window.pan_slider.setValue(mid)
    display_layout.addWidget(main_window.pan_slider)


   # Action buttons - use a card with a proper title
    action_card = CleanCard()
    action_card.setStyleSheet(f"background-color: {CleanTheme.BG_CARD};border: none;")#moy

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
        ("Remove outliers", main_window.remove_outliers_button_pushed, "remove_outliers_single_btn"),
        ("Lock spikes", main_window.lock_spikes_button_pushed, "lock_spikes_btn"),
        ("Update MU filter", main_window.update_mu_filter_button_pushed, "update_mu_filter_btn"),
        ("Extend MU filter", main_window.extend_mu_filter_button_pushed, "extend_mu_filter_btn"),
    ]

    # Create action buttons and store references
    main_window.action_buttons = {}
    for text, handler, attr_name in action_button_configs:
        btn = ActionButtonedit(text, primary=False)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.clicked.connect(handler)
        btn.setMinimumHeight(36)
        btn.setMaximumHeight(36)
        action_layout.addWidget(btn)
        # Store reference to button in main_window
        setattr(main_window, attr_name, btn)
        main_window.action_buttons[handler.__name__] = btn     
        if text in {"Add spikes", "Delete spikes", "Update MU filter", "Extend MU filter", "Lock spikes"}:
            btn.set_blue()
        if text in {"Delete spikes", "Delete DR", "Remove outliers"}:
            spacer = QWidget()
            spacer.setFixedWidth(20)
            action_layout.addWidget(spacer)  

    action_card.content_layout.addWidget(action_container)
    display_layout.addWidget(action_card)

    main_window.tip_bar = QLabel("")
    main_window.tip_bar.setFixedHeight(15)
    main_window.tip_bar.setAlignment(Qt.AlignCenter)
    set_standard_label_style(main_window.tip_bar, size=12)
    '''main_window.tip_bar.setStyleSheet(f"""
        background-color: {CleanTheme.BG_CARD};
        color: black;
        font-weight: bold;
    """)'''
    display_layout.addWidget(main_window.tip_bar)
    
    # Timer for tip bar
    main_window.tip_timer = QTimer(main_window)
    main_window.tip_timer.setSingleShot(True)
    main_window.tip_timer.timeout.connect(main_window.clear_tip)

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

    # Add all visualization elements to the panel
    main_window.display_panel.set_plot_widget(display_widget)

def create_plot_widget(main_window, y_label, x_label=""):
    """Create a standardized plot widget with consistent styling."""
    class NewViewBox(pg.ViewBox):
        def __init__(self, zoom_slider, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.zoom_slider = zoom_slider      
    
        def wheelEvent(self, event):
            event.accept()
            delta = event.delta()
            cur = self.zoom_slider.get_slider_value()

            if delta > 0:
                self.zoom_slider.set_slider_value(cur + 1)
            elif delta < 0:
                self.zoom_slider.set_slider_value(cur - 1)
        
        def keyPressEvent(self, event):
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                QApplication.sendEvent(main_window, event)
                event.ignore()
            super().keyPressEvent(event)
    
    plot = pg.PlotWidget(viewBox=NewViewBox(main_window.zoom_slider))

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

    # Disable plot option
    plot.setContextMenuActionVisible('Transforms',False)
    plot.setContextMenuActionVisible('Downsample',False)
    plot.setContextMenuActionVisible('Average',False)
    plot.setContextMenuActionVisible('Alpha',False)

    return plot


def create_mu_checkbox(main_window, array_idx, mu_idx, text, sil_value, is_checked=False):
    """Helper function to create a styled checkbox for motor unit selection."""
    checkbox = QCheckBox(text)
    checkbox.setStyleSheet(
        f"""
        QCheckBox {{
            color: {CleanTheme.TEXT_PRIMARY};
            font-size: 13px;
            font-family: "Segoe UI";
            font-weight: normal;
            font-style: normal;
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
    
def find_sidebar(main_window):
    """Find the sidebar component in the application hierarchy."""
    # First try to find it in the parent (main window)
    if main_window.parent():
        sidebar = main_window.parent().findChild(Sidebar, "cleanSidebar")
        if sidebar:
            return sidebar

    # If not found in parent, try to find it globally in the application
    for widget in QApplication.topLevelWidgets():
        sidebar = widget.findChild(Sidebar, "cleanSidebar")
        if sidebar:
            return sidebar
    return None