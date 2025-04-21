from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QGraphicsDropShadowEffect,
    QSpacerItem,
    QStackedWidget,
)
from PyQt5.QtGui import QFont, QColor, QCursor
from PyQt5.QtCore import Qt, QSize


def setup_ui(main_window):
    """Sets up the UI for the HDEMG dashboard."""
    # Main window settings
    main_window.setWindowTitle("HDEMG App")
    main_window.resize(1400, 700)
    main_window.setMinimumSize(1000, 600)
    main_window.setStyleSheet(f"background-color: {main_window.colors['bg_main']};")

    # Create main widget and layout
    main_widget = QWidget()
    main_window.main_h_layout = QHBoxLayout(main_widget)
    main_window.main_h_layout.setContentsMargins(0, 0, 0, 0)
    main_window.main_h_layout.setSpacing(0)
    main_window.setCentralWidget(main_widget)

    # Create Sidebar and add to layout
    main_window.sidebar_buttons = {}
    main_window.main_h_layout.addWidget(_create_left_sidebar(main_window))

    # Create the central stacked widget
    main_window.central_stacked_widget = QStackedWidget()
    main_window.central_stacked_widget.setStyleSheet("background-color: transparent;")

    # Dashboard page - Create this with a custom method
    main_window.dashboard_page = _create_dashboard_page(main_window)
    main_window.central_stacked_widget.addWidget(main_window.dashboard_page)

    # Add other pages based on imported modules
    if main_window.import_data_page is not None:
        main_window.central_stacked_widget.addWidget(main_window.import_data_page)

    if main_window.mu_analysis_page is not None:
        main_window.central_stacked_widget.addWidget(main_window.mu_analysis_page)

    # Placeholder pages
    main_window.manual_editing_page = create_placeholder_page("Manual Editing Page (Placeholder)", main_window)
    main_window.central_stacked_widget.addWidget(main_window.manual_editing_page)

    main_window.decomposition_page = create_placeholder_page("Decomposition Page (Placeholder)", main_window)
    main_window.central_stacked_widget.addWidget(main_window.decomposition_page)

    main_window.main_h_layout.addWidget(main_window.central_stacked_widget, 1)


def create_placeholder_page(title, main_window):
    """Creates a placeholder page with a title and back button."""
    page = QWidget()
    layout = QVBoxLayout(page)

    label = QLabel(title)
    label.setAlignment(getattr(Qt, "AlignCenter"))
    label.setFont(QFont("Arial", 16))

    back_button = QPushButton("Back to Dashboard")
    back_button.clicked.connect(main_window.show_dashboard_view)

    layout.addWidget(label)
    layout.addWidget(back_button)
    layout.addStretch()

    return page


def _create_left_sidebar(main_window):
    """Creates the left sidebar with navigation buttons."""
    sidebar = QFrame()
    sidebar.setObjectName("sidebar")
    sidebar.setFrameShape(QFrame.NoFrame)
    sidebar.setFixedWidth(200)
    sidebar.setStyleSheet("#sidebar { background-color: #fdfdfd; border: none; border-right: 1px solid #e0e0e0; }")
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(0, 15, 0, 15)
    sidebar_layout.setSpacing(5)

    # App title section
    app_title_layout = QHBoxLayout()
    app_title_layout.setContentsMargins(15, 0, 15, 0)
    app_icon_label = QLabel()
    app_icon_label.setPixmap(main_window.style().standardIcon(getattr(QStyle, "SP_ComputerIcon")).pixmap(QSize(24, 24)))
    app_title_label = QLabel("HDEMG App")
    app_title_label.setFont(QFont("Arial", 12, QFont.Bold))
    app_title_layout.addWidget(app_icon_label)
    app_title_layout.addWidget(app_title_label)
    app_title_layout.addStretch()
    sidebar_layout.addLayout(app_title_layout)
    sidebar_layout.addSpacerItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # Define Sidebar Buttons
    main_window.sidebar_buttons["dashboard"] = _create_sidebar_button_widget(
        "Dashboard", main_window.style().standardIcon(getattr(QStyle, "SP_DesktopIcon")), main_window
    )
    main_window.sidebar_buttons["import"] = _create_sidebar_button_widget(
        "Import Data", main_window.style().standardIcon(getattr(QStyle, "SP_DialogOpenButton")), main_window
    )
    main_window.sidebar_buttons["mu_analysis"] = _create_sidebar_button_widget(
        "MU Analysis", main_window.style().standardIcon(getattr(QStyle, "SP_FileDialogDetailedView")), main_window
    )
    main_window.sidebar_buttons["decomposition"] = _create_sidebar_button_widget(
        "Decomposition", main_window.style().standardIcon(getattr(QStyle, "SP_ArrowRight")), main_window
    )
    main_window.sidebar_buttons["manual_edit"] = _create_sidebar_button_widget(
        "Manual Editing", main_window.style().standardIcon(getattr(QStyle, "SP_DialogYesButton")), main_window
    )

    # Add buttons to layout
    for btn in main_window.sidebar_buttons.values():
        sidebar_layout.addWidget(btn)

    sidebar_layout.addStretch()
    return sidebar


def _create_sidebar_button_widget(text, icon, main_window):
    """Creates a styled sidebar button."""
    btn = QPushButton(text)
    btn.setObjectName(f"sidebarBtn_{text.replace(' ', '_')}")
    btn.setIcon(icon)
    btn.setIconSize(QSize(18, 18))
    btn.setMinimumHeight(40)
    btn.setCursor(QCursor(getattr(Qt, "PointingHandCursor")))
    btn.setStyleSheet(
        f"""
        QPushButton {{
            text-align: left;
            padding-left: 15px;
            border: none;
            border-radius: 0;
            font-weight: bold;
            font-size: 9pt;
            color: {main_window.colors['text_primary']};
            background-color: transparent;
        }}
        QPushButton:hover {{
            background-color: {main_window.colors['sidebar_selected_bg']};
        }}
        QPushButton:disabled {{
            color: #aaa;
            background-color: transparent;
        }}
    """
    )
    return btn


def _create_dashboard_page(main_window):
    """Creates the dashboard page."""
    dashboard_scroll_area = QScrollArea()
    dashboard_scroll_area.setWidgetResizable(True)
    dashboard_scroll_area.setFrameShape(QFrame.NoFrame)
    dashboard_scroll_area.setStyleSheet("background-color: transparent; border: none;")

    content_area = QWidget()
    content_area.setObjectName("dashboardContentArea")
    content_area.setStyleSheet("background-color: transparent;")
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(25, 25, 25, 25)
    content_layout.setSpacing(20)
    dashboard_scroll_area.setWidget(content_area)

    # Header
    header_layout = QHBoxLayout()
    dashboard_title = QLabel("Dashboard")
    dashboard_title.setFont(QFont("Arial", 18, QFont.Bold))
    dashboard_title.setStyleSheet(f"color: {main_window.colors['text_primary']};")

    new_viz_btn = QPushButton("+ New Analysis")
    new_viz_btn.setFont(QFont("Arial", 9, QFont.Bold))
    new_viz_btn.setIcon(main_window.style().standardIcon(getattr(QStyle, "SP_FileDialogNewFolder")))
    new_viz_btn.setIconSize(QSize(14, 14))
    new_viz_btn.setCursor(QCursor(getattr(Qt, "PointingHandCursor")))
    new_viz_btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: {main_window.colors['accent']};
            color: white;
            border-radius: 4px;
            padding: 8px 15px;
        }}
        QPushButton:hover {{
            background-color: #333333;
        }}
    """
    )

    header_layout.addWidget(dashboard_title)
    header_layout.addStretch()
    header_layout.addWidget(new_viz_btn)
    content_layout.addLayout(header_layout)

    # Content Grid: Visualizations and Datasets Frames
    content_grid = QVBoxLayout()
    content_grid.setSpacing(20)

    # Top Row: Visualizations
    top_row = QHBoxLayout()
    top_row.setSpacing(20)
    viz_section_frame = _create_viz_section_frame(main_window)
    top_row.addWidget(viz_section_frame)
    content_grid.addLayout(top_row)

    # Bottom Row: Datasets
    bottom_row = QHBoxLayout()
    bottom_row.setSpacing(20)
    datasets_frame = _create_datasets_frame(main_window)
    bottom_row.addWidget(datasets_frame)
    content_grid.addLayout(bottom_row)

    content_layout.addLayout(content_grid)
    content_layout.addStretch(1)
    return dashboard_scroll_area


def _create_viz_section_frame(main_window):
    """Creates the visualization section frame."""
    viz_section_frame = QFrame()
    viz_section_frame.setObjectName("vizSectionFrame_Original")
    viz_section_frame.setFrameShape(QFrame.StyledPanel)
    viz_section_frame.setStyleSheet(
        """
        #vizSectionFrame_Original {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }
        #vizSectionFrame_Original > QScrollArea, #vizSectionFrame_Original > QLabel {
            border: none;
            background-color: transparent;
        }
    """
    )

    viz_layout = QVBoxLayout(viz_section_frame)
    viz_layout.setSpacing(10)

    viz_title = QLabel("Recent Analyses")
    viz_title.setFont(QFont("Arial", 12, QFont.Bold))
    viz_title.setStyleSheet("background: transparent; border: none;")

    viz_scroll_area = QScrollArea()
    viz_scroll_area.setObjectName("vizScrollArea_Original")
    viz_scroll_area.setWidgetResizable(True)
    viz_scroll_area.setFrameShape(QFrame.NoFrame)
    viz_scroll_area.setHorizontalScrollBarPolicy(getattr(Qt, "ScrollBarAsNeeded"))
    viz_scroll_area.setVerticalScrollBarPolicy(getattr(Qt, "ScrollBarAlwaysOff"))
    viz_scroll_area.setFixedHeight(220)
    viz_scroll_area.setStyleSheet("#vizScrollArea_Original { background-color: transparent; border: none; }")

    viz_container = QWidget()
    viz_container.setObjectName("vizContainer_Original")
    viz_container.setStyleSheet("background-color: transparent; border: none;")
    viz_container_layout = QHBoxLayout(viz_container)
    viz_container_layout.setSpacing(15)
    viz_container_layout.setContentsMargins(0, 5, 0, 5)

    if not main_window.recent_visualizations:
        no_viz_label = QLabel("No recent analyses found.")
        no_viz_label.setAlignment(getattr(Qt, "AlignCenter"))
        no_viz_label.setStyleSheet(f"color: {main_window.colors['text_secondary']};")
        viz_container_layout.addWidget(no_viz_label)
    else:
        for idx, viz_data in enumerate(main_window.recent_visualizations):
            # Create a card with custom click handling to open the visualization
            viz_card = create_clickable_viz_card(
                viz_data["title"], 
                viz_data["date"], 
                main_window, 
                viz_data["type"], 
                viz_data["icon"], 
                idx,
                viz_data.get("id", None)  # Pass the visualization ID to the card
            )
            viz_container_layout.addWidget(viz_card)

        # Add stretch to prevent cards from spreading too far apart when there are few
        viz_container_layout.addStretch()

    viz_scroll_area.setWidget(viz_container)
    viz_layout.addWidget(viz_title)
    viz_layout.addWidget(viz_scroll_area)

    return viz_section_frame


def _create_datasets_frame(main_window):
    """Creates the datasets frame."""
    datasets_frame = QFrame()
    datasets_frame.setObjectName("datasetsFrame_Original")
    datasets_frame.setFrameShape(QFrame.NoFrame)
    datasets_frame.setStyleSheet(
        """
        #datasetsFrame_Original {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }
        #datasetsFrame_Original > QLabel {
            background-color: transparent;
            border: none;
        }
    """
    )

    datasets_layout = QVBoxLayout(datasets_frame)
    datasets_layout.setSpacing(10)

    datasets_title = QLabel("Recent Datasets")
    datasets_title.setFont(QFont("Arial", 12, QFont.Bold))
    datasets_title.setStyleSheet("background: transparent; border: none;")
    datasets_layout.addWidget(datasets_title)

    if not main_window.recent_datasets:
        no_data_label = QLabel("No recent datasets found.")
        no_data_label.setAlignment(getattr(Qt, "AlignCenter"))
        no_data_label.setStyleSheet(f"color: {main_window.colors['text_secondary']};")
        datasets_layout.addWidget(no_data_label)
    else:
        for idx, dataset in enumerate(main_window.recent_datasets):
            dataset_entry = create_dataset_entry(dataset["filename"], dataset["metadata"], main_window, idx)
            datasets_layout.addWidget(dataset_entry)

    datasets_layout.addStretch()
    return datasets_frame


def create_clickable_viz_card(title, date, main_window, card_type="default", icon_style=None, idx=0, vis_id=None):
    """Creates a visualization card for the dashboard with click handling."""
    # Custom class to handle clicks properly
    class ClickableVisCard(QFrame):
        def __init__(self, title, vis_id=None, parent=None):
            super().__init__(parent)
            self.title = title
            self.vis_id = vis_id
            
        def mousePressEvent(self, event):
            # Call the parent window's open_visualization method with visualization ID
            main_window.open_visualization(self.title, self.vis_id)
            super().mousePressEvent(event)

    # Create the clickable card
    card = ClickableVisCard(title, vis_id)
    sanitized_title = title.replace(" ", "_").replace(":", "").lower()
    card.setObjectName(f"vizCard_{sanitized_title}_{idx}")
    card.setFrameShape(QFrame.StyledPanel)
    card.setFixedSize(250, 180)
    card.setProperty("title", title)
    card.setProperty("vis_id", vis_id)  # Store ID as a property for later use

    if card_type in main_window.colors:
        bg_color = main_window.colors.get(f"bg_card_{card_type}", main_window.colors["bg_card_default"])
    else:
        bg_color = main_window.colors["bg_card_default"]

    text_color = "white"
    border_color = darken_color(bg_color, 20, main_window)

    main_layout = QVBoxLayout(card)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(10)

    # Icon section
    icon_section = QFrame(card)
    icon_section.setObjectName(f"iconSection_{sanitized_title}_{idx}")
    icon_section.setStyleSheet(
        f"""
        #{icon_section.objectName()} {{
            background-color: {darken_color(bg_color, 10, main_window)};
            border: 1px solid {border_color};
            border-radius: 4px;
        }}
        #{icon_section.objectName()} QLabel {{
            color: {text_color};
            background-color: transparent;
            border: none;
        }}
    """
    )

    icon_layout = QVBoxLayout(icon_section)
    icon_layout.setContentsMargins(5, 5, 5, 5)

    chart_icon = QLabel()
    chart_icon.setObjectName(f"chartIcon_{sanitized_title}_{idx}")
    icon_to_use = icon_style if icon_style is not None else getattr(QStyle, "SP_FileDialogDetailedView")
    chart_icon.setPixmap(main_window.style().standardIcon(icon_to_use).pixmap(QSize(24, 24)))
    chart_icon.setAlignment(getattr(Qt, "AlignCenter"))
    chart_icon.setStyleSheet(
        f"#{chart_icon.objectName()} {{ color: {text_color}; background-color: transparent; border: none; }}"
    )

    icon_layout.addWidget(chart_icon)

    # Title section
    title_section = QFrame(card)
    title_section.setObjectName(f"titleSection_{sanitized_title}_{idx}")
    title_section.setStyleSheet(
        f"""
        #{title_section.objectName()} {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
        }}
        #{title_section.objectName()} QLabel {{
            color: {text_color};
            background-color: transparent;
            border: none;
        }}
    """
    )

    title_layout = QVBoxLayout(title_section)
    title_layout.setContentsMargins(5, 5, 5, 5)

    title_label = QLabel(title)
    title_label.setObjectName(f"titleLabel_{sanitized_title}_{idx}")
    title_label.setFont(QFont("Arial", 11, QFont.Bold))
    title_label.setAlignment(getattr(Qt, "AlignCenter"))
    title_label.setStyleSheet(
        f"#{title_label.objectName()} {{ color: {text_color}; background-color: transparent; border: none; }}"
    )

    title_layout.addWidget(title_label)

    # Date section
    date_section = QFrame(card)
    date_section.setObjectName(f"dateSection_{sanitized_title}_{idx}")
    date_section.setStyleSheet(
        f"""
        #{date_section.objectName()} {{
            background-color: {darken_color(bg_color, 15, main_window)};
            border: 1px solid {border_color};
            border-radius: 4px;
        }}
        #{date_section.objectName()} QLabel {{
            color: {text_color};
            background-color: transparent;
            border: none;
        }}
    """
    )

    date_layout = QVBoxLayout(date_section)
    date_layout.setContentsMargins(5, 5, 5, 5)

    date_label = QLabel(date)
    date_label.setObjectName(f"dateLabel_{sanitized_title}_{idx}")
    date_label.setAlignment(getattr(Qt, "AlignCenter"))
    date_label.setStyleSheet(
        f"#{date_label.objectName()} {{ color: {text_color}; font-size: 10px; background-color: transparent; border: none; }}"
    )

    date_layout.addWidget(date_label)

    # Add sections to main layout
    main_layout.addWidget(icon_section)
    main_layout.addWidget(title_section)
    main_layout.addWidget(date_section)

    card.setStyleSheet(
        f"""
        #{card.objectName()} {{
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: 8px;
        }}
        #{card.objectName()} > QLabel {{
            color: {text_color};
            background-color: transparent;
            border: none;
        }}
        #{card.objectName()} > QFrame {{
            border: none;
        }}
    """
    )

    card.setCursor(QCursor(getattr(Qt, "PointingHandCursor")))

    # Add shadow effect
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(10)
    shadow.setColor(QColor(0, 0, 0, 60))
    shadow.setOffset(2, 2)
    card.setGraphicsEffect(shadow)

    return card


def create_dataset_entry(filename, metadata, main_window, idx=0):
    """Creates a dataset entry for the dashboard."""
    sanitized_name = filename.replace(" ", "_").replace(".", "_").lower()
    entry = QFrame()
    entry.setObjectName(f"datasetEntry_{sanitized_name}_{idx}")
    entry.setStyleSheet(
        f"""
        #{entry.objectName()} {{
            background-color: #f2f2f2;
            border-radius: 4px;
            margin-bottom: 5px;
        }}
        #{entry.objectName()} QLabel, #{entry.objectName()} QPushButton {{
            background-color: transparent;
            border: none;
        }}
    """
    )

    entry_layout = QHBoxLayout(entry)
    entry_layout.setContentsMargins(12, 12, 12, 12)

    file_icon = QLabel()
    file_icon.setObjectName(f"fileIcon_{sanitized_name}_{idx}")
    file_icon.setPixmap(main_window.style().standardIcon(getattr(QStyle, "SP_FileIcon")).pixmap(QSize(16, 16)))

    file_info = QVBoxLayout()
    name_label = QLabel(filename)
    name_label.setObjectName(f"nameLabel_{sanitized_name}_{idx}")
    name_label.setFont(QFont("Arial", 10))

    meta_label = QLabel(metadata)
    meta_label.setObjectName(f"metaLabel_{sanitized_name}_{idx}")
    meta_label.setStyleSheet(
        f"#{meta_label.objectName()} {{ color: #777777; font-size: 10px; background-color: transparent; border: none; }}"
    )

    file_info.addWidget(name_label)
    file_info.addWidget(meta_label)

    options_btn = QPushButton("⋮")
    options_btn.setObjectName(f"optionsBtn_{sanitized_name}_{idx}")
    options_btn.setFixedSize(40, 40)
    options_btn.setFont(QFont("Arial", 30))
    options_btn.setCursor(QCursor(getattr(Qt, "PointingHandCursor")))
    options_btn.setStyleSheet(
        f"""
        #{options_btn.objectName()} {{
            background: transparent;
            border: none;
        }}
        #{options_btn.objectName()}:hover {{
            background-color: #e0e0e0;
            border-radius: 20px;
        }}
    """
    )

    entry_layout.addWidget(file_icon)
    entry_layout.addLayout(file_info, 1)
    entry_layout.addWidget(options_btn)

    return entry


def darken_color(hex_color, amount=20, main_window=None):
    """Darkens a hex color by the given amount."""
    try:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = max(0, r - amount)
        g = max(0, g - amount)
        b = max(0, b - amount)
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return "#aaaaaa"


def update_sidebar_selection(main_window, selected_key):
    """Updates the visual state of sidebar buttons based on selection."""
    selected_bg = main_window.colors.get("sidebar_selected_bg", "#e6e6e6")
    default_text_color = main_window.colors.get("text_primary", "#333333")
    disabled_text_color = "#aaa"

    for key, button in main_window.sidebar_buttons.items():
        base_layout = "text-align: left; padding-left: 15px; border: none; border-radius: 0;"
        base_font = "font-weight: bold; font-size: 9pt;"
        current_bg = "transparent"
        current_text = default_text_color

        if not button.isEnabled():
            current_text = disabled_text_color
        elif key == selected_key:
            current_bg = selected_bg

        style = f"""
            QPushButton {{ {base_layout} {base_font} background-color: {current_bg}; color: {current_text}; }}
            QPushButton:hover {{ background-color: {selected_bg}; color: {default_text_color}; }}
            QPushButton:disabled {{ color: {disabled_text_color}; background-color: transparent; }}
        """
        button.setStyleSheet(style)