from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QStackedWidget,
    QSizePolicy,
    QSpacerItem,
    QLabel,
    QFrame,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# Import all required components
from ui.components import (
    CleanTheme,
    CleanCard,
    VisualizationCard,
    ActionButton,
    DatasetItem,
    SectionHeader,
    Sidebar,
)


def setup_ui(main_window):
    """Sets up the UI for the HDEMG dashboard with improved sidebar."""
    # Main window settings
    main_window.setWindowTitle("HDEMG App")
    main_window.resize(1200, 700)
    main_window.setMinimumSize(1000, 600)
    # main_window.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")

    # Create main widget and layout
    main_widget = QWidget()
    main_window.main_h_layout = QHBoxLayout(main_widget)
    main_window.main_h_layout.setContentsMargins(0, 0, 0, 0)
    main_window.main_h_layout.setSpacing(0)
    main_window.setCentralWidget(main_widget)

    # Create sidebar with buttons
    main_window.sidebar_buttons = {}
    main_window.main_h_layout.addWidget(_create_left_sidebar(main_window))

    # Create the central stacked widget
    main_window.central_stacked_widget = QStackedWidget()
    main_window.central_stacked_widget.setStyleSheet("background-color: transparent;")

    # Dashboard page
    main_window.dashboard_page = _create_dashboard_page(main_window)
    main_window.central_stacked_widget.addWidget(main_window.dashboard_page)

    # Add other pages based on imported modules
    if hasattr(main_window, "import_data_page") and main_window.import_data_page is not None:
        main_window.central_stacked_widget.addWidget(main_window.import_data_page)

    if hasattr(main_window, "mu_analysis_page") and main_window.mu_analysis_page is not None:
        main_window.central_stacked_widget.addWidget(main_window.mu_analysis_page)

    # Placeholder pages
    main_window.manual_editing_page = create_placeholder_page("Manual Editing Page", main_window)
    main_window.central_stacked_widget.addWidget(main_window.manual_editing_page)

    main_window.decomposition_page = create_placeholder_page("Decomposition Page", main_window)
    main_window.central_stacked_widget.addWidget(main_window.decomposition_page)

    main_window.main_h_layout.addWidget(main_window.central_stacked_widget, 1)


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

    layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
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
                main_window.show_import_data_view if hasattr(main_window, "show_import_data_view") else lambda: None
            )
        elif key == "mu_analysis":
            button.clicked.connect(
                main_window.show_mu_analysis_view if hasattr(main_window, "show_mu_analysis_view") else lambda: None
            )
        elif key == "decomposition":
            button.clicked.connect(
                main_window.show_decomposition_view if hasattr(main_window, "show_decomposition_view") else lambda: None
            )
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
    dashboard_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    dashboard_scroll_area.setStyleSheet("background-color: transparent; border: none;")

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
    new_viz_btn = ActionButton("+ New Analysis", primary=True)
    new_viz_btn.clicked.connect(
        lambda: main_window.show_import_data_view() if hasattr(main_window, "show_import_data_view") else None
    )

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
    section_card.setObjectName("visualizationsSection")
    section_card.setMinimumSize(200, 300)

    # Add section title
    section_title = QLabel("Recent Visualizations")
    section_title.setObjectName("sectionTitle")
    section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
    section_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    section_card.layout.addWidget(section_title)

    # Create horizontal layout for visualization cards
    cards_layout = QHBoxLayout()
    cards_layout.setSpacing(15)

    # Add visualization cards
    if hasattr(main_window, "recent_visualizations") and main_window.recent_visualizations:
        for viz_data in main_window.recent_visualizations[:3]:  # Show only first three cards
            # Extract data for card
            title = viz_data.get("title", "Unnamed Visualization")
            date = viz_data.get("date", "Unknown date")
            viz_type = viz_data.get("type", "hdemg")

            # Create card for each visualization
            from ui.components.VisualizationCard import VisualizationCard
            card = VisualizationCard(title=title, date=date, viz_type=viz_type, viz_data=viz_data)
            
            # Connect the card's clicked signal
            card.clicked.connect(lambda viz_data=viz_data: main_window.open_visualization(viz_data))
            
            cards_layout.addWidget(card)
    else:
        # Create a placeholder card
        from ui.components.VisualizationCard import VisualizationCard
        empty_card = VisualizationCard(title="No Visualizations", date="Create your first visualization")
        cards_layout.addWidget(empty_card)

    section_card.layout.addLayout(cards_layout)

    return section_card


def _create_datasets_section(main_window):
    """Creates the Recent Datasets section with clean list items."""
    # Create a card to hold the datasets
    section_card = CleanCard()
    section_card.setObjectName("datasetsSection")
    section_card.setMinimumSize(200, 200)

    # Add section title
    section_title = QLabel("Recent Datasets")
    section_title.setObjectName("sectionTitle")
    section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
    section_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    section_card.layout.addWidget(section_title)

    # Create datasets container
    datasets_container = QWidget()
    datasets_layout = QVBoxLayout(datasets_container)
    datasets_layout.setContentsMargins(0, 0, 0, 0)
    datasets_layout.setSpacing(0)  # No spacing between items

    # Add dataset items
    if hasattr(main_window, "recent_datasets") and main_window.recent_datasets:
        for dataset in main_window.recent_datasets:
            dataset_item = DatasetItem(dataset["filename"], dataset["metadata"])
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

    section_card.layout.addWidget(datasets_container)

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


def refresh_visualizations_section(main_window):
    """
    Refreshes the visualization section of the dashboard with updated data.
    
    Args:
        main_window: The main window instance
    """
    # Find the visualization section card
    content_widget = main_window.dashboard_page.widget()
    if not content_widget:
        return
    
    viz_section = content_widget.findChild(QFrame, "visualizationsSection")
    if not viz_section:
        return
    
    # Find the cards layout
    cards_layout = None
    for i in range(viz_section.layout.count()):
        item = viz_section.layout.itemAt(i)
        if isinstance(item.layout(), QHBoxLayout):
            cards_layout = item.layout()
            break
    
    if not cards_layout:
        return
    
    # Clear existing cards
    while cards_layout.count():
        item = cards_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
    
    # Add updated visualization cards
    if hasattr(main_window, "recent_visualizations") and main_window.recent_visualizations:
        from ui.components.VisualizationCard import VisualizationCard
        
        for viz_data in main_window.recent_visualizations[:3]:  # Show up to 3 most recent
            title = viz_data.get("title", "Unnamed Visualization")
            date = viz_data.get("date", "Unknown date")
            viz_type = viz_data.get("type", "hdemg")
            
            card = VisualizationCard(title=title, date=date, viz_type=viz_type, viz_data=viz_data)
            # Use lambda with default argument to avoid late binding issues
            card.clicked.connect(lambda clicked=False, data=viz_data: main_window.open_visualization(data))
            cards_layout.addWidget(card)
    else:
        # Create a placeholder card
        from ui.components.VisualizationCard import VisualizationCard
        empty_card = VisualizationCard(title="No Visualizations", date="Create your first visualization")
        cards_layout.addWidget(empty_card)