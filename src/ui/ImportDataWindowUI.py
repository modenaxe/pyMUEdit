import os
from pathlib import Path

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QStackedWidget,
                             QVBoxLayout, QWidget)

# Import custom components
from ui.components import (ActionButton, CleanCard, CleanTheme, SectionHeader,
                           Sidebar, VisualizationPanel)

# copied from dashboardui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
                             QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

# Import all required components
from ui.components import (ActionButton, CleanCard, CleanTheme, DatasetItem,
                           SectionHeader, Sidebar, VisualizationCard)
from ui.components.CleanScrollBar import CleanScrollBar

# defining absolute path to the public icons folder (same logic as Sidebar.py)
ABS_PATH = Path(__file__).parent.parent
ICONS_PATH = ABS_PATH / "public"



def setup_ui(import_window):
    """Set up the UI for the import data window using custom components."""
    # Set widget properties
    import_window.setWindowTitle("HDEMG Analysis - Import Data")
    import_window.setGeometry(100, 100, 1200, 800)
    import_window.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")

    # Main widget and layout
    import_window.central_widget = QWidget()
    import_window.setCentralWidget(import_window.central_widget)
    import_window.main_layout = QHBoxLayout(import_window.central_widget)
    import_window.main_layout.setContentsMargins(0, 0, 0, 0)
    import_window.main_layout.setSpacing(0)

    # Create main content layout
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(0)

    # Create right content area
    right_content = create_right_content(import_window)
    content_layout.addWidget(right_content, 1)

    # Add content to main layout
    content_layout.addLayout(content_layout, 1)

    # Add footer
    footer = create_footer(import_window)
    content_layout.addWidget(footer)

    import_window.main_layout.addWidget(content_widget)

    # Store references to functions for sidebar management
    import_window.update_sidebar_with_recent_files = lambda: update_sidebar_with_recent_files(
        import_window)
    import_window.restore_sidebar = lambda: restore_sidebar(import_window)


def create_right_content(import_window):
    """Create the right content area with dropzone and preview."""
    # Create scroll area for content
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("background: transparent; border: none;")

    # Create container widget
    right_content = QWidget()
    right_layout = QVBoxLayout(right_content)
    right_layout.setContentsMargins(25, 25, 25, 25)
    right_layout.setSpacing(10)

    # Add section header
    header = SectionHeader("Import HDEMG Data")
    right_layout.addWidget(header)

    # Create visualisations section
    preview_section = _create_visualizations_section(import_window)
    right_layout.addWidget(preview_section)

    # Create datasets section
    datasets_section = _create_datasets_section(import_window)
    right_layout.addWidget(datasets_section)

    # Create dropzone card
    dropzone_card = create_dropzone_card(import_window)
    right_layout.addWidget(dropzone_card)

    # Create preview section
    preview_section = create_preview_section(import_window)
    right_layout.addWidget(preview_section)

    # Create configuration section
    configuration_section = create_configuration_section(import_window)
    right_layout.addLayout(configuration_section)

    # Add stretch to push content to the top
    right_layout.addStretch(1)

    # Set the content widget to the scroll area
    scroll_area.setWidget(right_content)

    return scroll_area


def create_dropzone_card(import_window):
    """Create a clean card for the file dropzone."""
    dropzone_card = CleanCard()
    dropzone_card.setMinimumHeight(175)

    # Create layout for content
    dropzone_layout = QVBoxLayout()
    dropzone_layout.setContentsMargins(10, 10, 10, 10)
    dropzone_layout.setSpacing(10)
    dropzone_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Add SVG icon
    icon_container = QWidget()
    icon_layout = QHBoxLayout(icon_container)
    icon_layout.setContentsMargins(0, 0, 0, 0)
    icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    upload_icon_path = ICONS_PATH / "upload_icon.svg"
    if not upload_icon_path.exists():
        print(f"Warning: Icon {upload_icon_path} not found")
    cloud_icon = QSvgWidget(str(upload_icon_path))
    cloud_icon.setFixedSize(32, 22)
    cloud_icon.setStyleSheet("margin-bottom: 10px;")

    icon_layout.addWidget(cloud_icon)

    # Add descriptive text
    drag_label = QLabel("Drag and drop your HDEMG files here")
    drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    drag_label.setFont(QFont("Segoe UI", 12))
    drag_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")

    # Add file info label (hidden initially)
    import_window.file_info_label = QLabel("")
    import_window.file_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    import_window.file_info_label.setFont(QFont("Segoe UI", 11))
    import_window.file_info_label.setStyleSheet(
        f"color: #4CAF50; font-weight: bold;")
    import_window.file_info_label.setVisible(False)

    # Add "or" label
    or_label = QLabel("or")
    or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    or_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")

    # Add browse button
    browse_btn = ActionButton("Browse Files", primary=False)
    browse_btn.clicked.connect(import_window.select_file)

    # Add widgets to layout
    dropzone_layout.addStretch()
    dropzone_layout.addWidget(icon_container)
    dropzone_layout.addWidget(drag_label)
    dropzone_layout.addWidget(import_window.file_info_label)
    dropzone_layout.addWidget(or_label)
    dropzone_layout.addWidget(browse_btn, 0, Qt.AlignmentFlag.AlignCenter)
    dropzone_layout.addStretch()

    # Add layout to card
    dropzone_card.content_layout.addLayout(dropzone_layout)

    # Store reference to the dropzone for drag and drop events
    import_window.dropzone = dropzone_card

    # Setup drag and drop events later in ImportDataWindow.py
    return dropzone_card


# NOTE: Creates 'Signal Preview' window
def create_preview_section(import_window):
    """Create the signal preview section."""
    preview_card = CleanCard()
    preview_card.setMinimumHeight(200)

    # Create layout for content
    preview_layout = QVBoxLayout()
    preview_layout.setContentsMargins(0, 0, 0, 0)
    preview_layout.setSpacing(5)

    # Create preview frame
    preview_frame = QFrame()
    preview_frame.setObjectName("previewFrame")
    preview_frame.setStyleSheet(
        f"""
        #previewFrame {{
            background-color: {CleanTheme.BG_VISUALIZATION};
            border-radius: 6px;
        }}
    """
    )
    preview_frame.setMinimumHeight(220)

    # Create stacked widget to display either the label or the visualisation
    # of the file
    import_window.preview_stacked_frame = QStackedWidget()

    # Create preview messages
    import_window.preview_messages = QVBoxLayout()

    # Create import failure message
    import_window.failure_message = QLabel("Error Loading Signal Preview")
    import_window.failure_message.setStyleSheet(
        f"color: #FA0000; font-weight: bold;")
    import_window.failure_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    import_window.failure_message.setVisible(False)

    # Create preview message
    import_window.preview_message = QLabel(
        "No file selected. Import a file to see a preview.")
    import_window.preview_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    import_window.preview_message.setStyleSheet(
        f"color: {CleanTheme.TEXT_SECONDARY};")

    # Add preview messages to stacked frame as an active widget
    import_window.preview_messages.addStretch()
    import_window.preview_messages.addWidget(import_window.failure_message)
    import_window.preview_messages.addSpacing(20)
    import_window.preview_messages.addWidget(import_window.preview_message)
    import_window.preview_messages.addStretch()
    import_window.preview_messages_widget = QWidget()
    import_window.preview_messages_widget.setLayout(
        import_window.preview_messages)
    import_window.preview_stacked_frame.addWidget(
        import_window.preview_messages_widget)

    # Create visualization panel to preview the data in a selected file
    import_window.preview_plot = pg.PlotWidget()
    import_window.preview_plot.setBackground("w")  # White background
    import_window.preview_plot.setLabel("left",
                                        "Amplitude",
                                        units="µV",
                                        **{"colour": "black",
                                            "font-size": "12pt"})  # 12pt, black text
    import_window.preview_plot.setLabel("bottom",
                                        "Time",
                                        units="s",
                                        **{"colour": "black",
                                           "font-size": "12pt"})  # 12pt, black text
    import_window.preview_plot.showGrid(x=True, y=True)
    import_window.preview_plot.setMinimumHeight(250)

    # Ensures axis ticks are black & thicker
    left_axis = import_window.preview_plot.getAxis("left")
    left_axis.setPen(pg.mkPen("black", width=2))

    bottom_axis = import_window.preview_plot.getAxis("bottom")
    bottom_axis.setPen(pg.mkPen("black", width=2))

    signal_panel = VisualizationPanel(plot_widget=import_window.preview_plot)
    import_window.preview_stacked_frame.addWidget(signal_panel)
    import_window.preview_stacked_frame.setCurrentIndex(0)

    # Add message to preview frame
    preview_frame_layout = QVBoxLayout(preview_frame)
    preview_frame_layout.addWidget(
        import_window.preview_stacked_frame, stretch=3)

    # Add preview frame to layout
    preview_layout.addWidget(preview_frame)

    # left and right buttons
    lrbuttons = QWidget()
    button_layout = QHBoxLayout()
    import_window.left_button = ActionButton("←", primary=False)
    import_window.left_button.setEnabled(False)
    import_window.right_button = ActionButton("→", primary=False)
    import_window.right_button.setEnabled(False)
    import_window.left_button.clicked.connect(import_window.leftClicked)
    import_window.right_button.clicked.connect(import_window.rightClicked)
    button_layout.addWidget(import_window.left_button)
    button_layout.addWidget(import_window.right_button)
    lrbuttons.setLayout(button_layout)
    preview_layout.addWidget(lrbuttons)

    # Add layout to card
    preview_card.content_layout.addLayout(preview_layout)

    # Store reference to preview frame
    import_window.preview_frame = preview_frame

    return preview_card


def create_configuration_section(import_window):
    config_group = QHBoxLayout()
    import_window.set_configuration_button = ActionButton(
        "Set Configuration", primary=False)
    import_window.set_configuration_button.setEnabled(False)
    config_group.addWidget(import_window.set_configuration_button)

    import_window.segment_session_button = ActionButton(
        "Segment Session", primary=False)
    import_window.segment_session_button.setEnabled(False)
    config_group.addWidget(import_window.segment_session_button)

    import_window.channel_view_button = ActionButton(
        "Channel Viewer", primary=False)
    import_window.channel_view_button.setEnabled(False)
    config_group.addWidget(import_window.channel_view_button)

    return config_group


def create_footer(import_window):
    """Create the footer with file info and navigation buttons."""
    footer = QFrame()
    footer.setObjectName("footer")
    footer.setStyleSheet(
        f"""
        #footer {{
            background-color: {CleanTheme.BG_MAIN};
            border-top: 1px solid {CleanTheme.BORDER};
        }}
    """
    )

    footer_layout = QHBoxLayout(footer)
    footer_layout.setContentsMargins(20, 10, 20, 10)

    # Create file info labels
    import_window.footer_file_info = QLabel("No file selected")
    import_window.footer_file_info.setStyleSheet(
        f"color: {CleanTheme.TEXT_PRIMARY};")

    import_window.size_info = QLabel("Size: --")
    import_window.size_info.setStyleSheet(
        f"color: {CleanTheme.TEXT_SECONDARY};")

    import_window.format_info = QLabel("Format: --")
    import_window.format_info.setStyleSheet(
        f"color: {CleanTheme.TEXT_SECONDARY};")

    # Add file info to layout
    footer_layout.addWidget(import_window.footer_file_info)
    footer_layout.addStretch(1)
    footer_layout.addWidget(import_window.size_info)
    footer_layout.addSpacing(10)
    footer_layout.addWidget(import_window.format_info)
    footer_layout.addSpacing(20)

    # Create navigation buttons
    prev_btn = ActionButton("← Previous", primary=False)
    prev_btn.clicked.connect(import_window.go_back)

    import_window.next_btn = ActionButton("Next →", primary=True)
    import_window.next_btn.clicked.connect(
        import_window.go_to_algorithm_screen)
    import_window.next_btn.setEnabled(False)

    # Add navigation buttons to layout
    footer_layout.addWidget(prev_btn)
    footer_layout.addSpacing(10)
    footer_layout.addWidget(import_window.next_btn)

    return footer


def find_sidebar(import_window):
    """Find the sidebar component in the application hierarchy."""
    # First try to find it in the parent (main window)
    if import_window.parent():
        sidebar = import_window.parent().findChild(Sidebar, "cleanSidebar")
        if sidebar:
            return sidebar

    # If not found in parent, try to find it globally in the application
    for widget in QApplication.topLevelWidgets():
        sidebar = widget.findChild(Sidebar, "cleanSidebar")
        if sidebar:
            return sidebar

    return None


def update_sidebar_with_recent_files(import_window):
    """Update the sidebar to show recent files."""
    sidebar = find_sidebar(import_window)
    if sidebar and hasattr(sidebar, "add_recent_files_section"):
        sidebar.add_recent_files_section(
            import_window.recent_files,
            import_window.load_recent_file)


def restore_sidebar(import_window):
    """Restore the sidebar to its default state."""
    sidebar = find_sidebar(import_window)
    if sidebar and hasattr(sidebar, "clear_recent_files_section"):
        sidebar.clear_recent_files_section()

def create_placeholder_page(title, main_window):
    """Creates a placeholder page with a title and back button."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(30, 30, 30, 30)

    # Create section header
    header = SectionHeader(title)
    layout.addWidget(header)

    # Create info message
    message = QLabel("This feature is under development")
    message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    message.setStyleSheet(
        f"""
        font-size: 14px;
        color: {CleanTheme.TEXT_SECONDARY};
        background-color: {CleanTheme.BG_CARD};
        border: 1px solid {CleanTheme.BORDER};
        border-radius: 8px;
        padding: 40px;
        margin: 20px 0;
    """
    )

    layout.addWidget(message)

    # Back button
    back_button = ActionButton("Back to Dashboard", primary=False)
    back_button.clicked.connect(main_window.show_dashboard_view)

    layout.addItem(
        QSpacerItem(
            20,
            20,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding))
    layout.addWidget(back_button, 0, Qt.AlignmentFlag.AlignLeft)

    return page


def _create_left_sidebar(main_window):
    """Creates the improved left sidebar with SVG icons."""
    # Create sidebar with app title
    sidebar = Sidebar("HDEMG App")

    # Define icon names
    icons = {
        "dashboard": "dashboard_icon",
        "import": "import_data_icon",
        "decomposition": "decomposition_icon",
        "manual_edit": "mu_editing_icon",
        "mu_analysis": "mu_analysis_icon",
    }

    # Menu items mapped to display names
    menu_items = {
        "dashboard": "Dashboard",
        "import": "Import Data",
        "decomposition": "Decomposition",
        "manual_edit": "MU Editing",
        "mu_analysis": "MU Analysis",
    }

    # Add buttons to sidebar and store references
    for key, display_name in menu_items.items():
        icon_name = icons.get(key)
        is_selected = key == "dashboard"  # Dashboard is initially selected
        button = sidebar.add_button(key, display_name, icon_name, is_selected)

        # Store reference and connect signal
        main_window.sidebar_buttons[key] = button

        # Connect button events based on key
        if key == "dashboard":
            button.clicked.connect(main_window.show_dashboard_view)
        elif key == "import":
            button.clicked.connect(
                main_window.show_import_data_view if hasattr(
                    main_window, "show_import_data_view") else lambda: None)
        elif key == "mu_analysis":
            button.clicked.connect(
                main_window.show_mu_analysis_view if hasattr(
                    main_window, "show_mu_analysis_view") else lambda: None)
        elif key == "decomposition":
            button.clicked.connect(
                main_window.show_decomposition_view if hasattr(
                    main_window, "show_decomposition_view") else lambda: None)
        elif key == "manual_edit":
            button.clicked.connect(
                main_window.show_manual_editing_view
                if hasattr(main_window, "show_manual_editing_view")
                else lambda: None
            )

    return sidebar


def _create_dashboard_page(main_window):
    """Creates the clean dashboard page."""
    # Create a scrollable dashboard
    dashboard_scroll_area = QScrollArea()
    dashboard_scroll_area.setWidgetResizable(True)
    dashboard_scroll_area.setFrameShape(QScrollArea.NoFrame)
    dashboard_scroll_area.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    dashboard_scroll_area.setStyleSheet(
        "background-color: transparent; border: none;")

    # Create content widget
    content_area = QWidget()
    content_area.setObjectName("dashboardContentArea")
    content_area.setStyleSheet("background-color: transparent;")

    # Set up the main layout
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(20, 20, 20, 20)
    content_layout.setSpacing(20)

    # Add dashboard header section
    header_layout = QHBoxLayout()

    # Dashboard title
    dashboard_title = QLabel("Dashboard")
    dashboard_title.setFont(QFont("Segoe UI", 20, QFont.Normal))
    dashboard_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")

    # New Visualization button
    new_viz_btn = ActionButton("+ New Visualization", primary=True)
    new_viz_btn.clicked.connect(
        lambda: main_window.show_import_data_view() if hasattr(
            main_window, "show_import_data_view") else None)

    header_layout.addWidget(dashboard_title)
    header_layout.addStretch(1)
    header_layout.addWidget(new_viz_btn)

    content_layout.addLayout(header_layout)

    # Create visualizations section
    visualizations_card = _create_visualizations_section(main_window)
    content_layout.addWidget(visualizations_card)

    # Create datasets section
    datasets_card = _create_datasets_section(main_window)
    content_layout.addWidget(datasets_card)

    # Add stretch to push content to the top
    content_layout.addStretch(1)

    # Set the content widget to the scroll area
    dashboard_scroll_area.setWidget(content_area)

    return dashboard_scroll_area


def _create_visualizations_section(main_window):
    """Creates the Recent Visualizations section with cards."""
    # Create a card to hold the visualizations
    section_card = CleanCard()
    section_card.setMinimumSize(200, 300)
    section_layout = QVBoxLayout()
    section_layout.setContentsMargins(0, 0, 0, 0)
    section_layout.setSpacing(15)

    # Add section title
    section_title = QLabel("Recent Visualizations")
    section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
    section_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    section_layout.addWidget(section_title)

    # Create horizontal layout for visualization cards
    cards_layout = QHBoxLayout()
    cards_layout.setSpacing(15)

    # Add visualization cards
    if hasattr(
            main_window,
            "recent_visualizations") and main_window.recent_visualizations:
        for i, viz_data in enumerate(
                main_window.recent_visualizations[:3]):  # Show only first 3 cards
            # Create card for each visualization with index and state_path
            card = VisualizationCard(
                title=viz_data["title"],
                date=viz_data["date"],
                icon=viz_data.get("icon", "visualization_icon"),
                state_path=viz_data.get("state_path"),
                index=i  # Pass index to track which card was clicked
            )
            cards_layout.addWidget(card)
    else:
        # Create a placeholder card
        empty_card = VisualizationCard(
            title="No Visualizations",
            date="Create your first visualization")
        cards_layout.addWidget(empty_card)

    section_layout.addLayout(cards_layout)
    section_card.layout.addLayout(section_layout)

    return section_card


def _create_datasets_section(main_window):
    """Creates the Recent Datasets section with clean list items."""
    # Create a card to hold the datasets
    section_card = CleanCard()
    section_card.setMinimumSize(200, 200)
    section_layout = QVBoxLayout()
    section_layout.setContentsMargins(0, 0, 0, 5)
    section_layout.setSpacing(15)

    # Add section title
    section_title = QLabel("Recent Datasets")
    section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
    section_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    section_layout.addWidget(section_title)

    # Create datasets container
    datasets_container = QWidget()
    datasets_layout = QVBoxLayout(datasets_container)
    datasets_layout.setContentsMargins(0, 0, 0, 0)
    datasets_layout.setSpacing(0)  # No spacing between items

    # Add dataset items
    if hasattr(main_window, "recent_datasets") and main_window.recent_datasets:
        for dataset in main_window.recent_datasets:
            # Create dataset item that will open the file when clicked
            dataset_item = DatasetItem(
                dataset["filename"], dataset["metadata"])

            # Store the full path for later use
            if "pathname" in dataset:
                dataset_item.setProperty("pathname", dataset["pathname"])

            # Connect the click event if applicable
            if hasattr(main_window, "open_dataset"):
                dataset_item.mousePressEvent = lambda event, d=dataset: main_window.open_dataset(
                    d)

            datasets_layout.addWidget(dataset_item)
    else:
        # Create an empty state message
        empty_label = QLabel("No recent datasets found")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet(
            f"""
            color: {CleanTheme.TEXT_SECONDARY};
            padding: 20px;
            font-size: 12px;
        """
        )
        datasets_layout.addWidget(empty_label)

    section_layout.addWidget(datasets_container)
    section_card.layout.addLayout(section_layout)

    return section_card


def update_sidebar_selection(main_window, selected_key):
    """Updates the visual state of sidebar buttons based on selection."""
    # Use the sidebar's built-in selection method
    sidebar = main_window.findChild(Sidebar)
    if sidebar:
        sidebar.select_button(selected_key)
    else:
        # Fallback if sidebar isn't found
        for key, button in main_window.sidebar_buttons.items():
            if hasattr(button, "set_selected"):
                button.set_selected(key == selected_key)
            else:
                # Older style buttons
                button.blockSignals(True)
                button.setChecked(key == selected_key)
                button.blockSignals(False)