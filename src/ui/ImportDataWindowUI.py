import os
from datetime import datetime
from pathlib import Path
from tkinter.filedialog import FileDialog

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QSizePolicy,
                             QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

from core.logger import logger
# Import custom components
from ui.components import (ActionButton, CleanCard, CleanTheme, SectionHeader,
                           Sidebar, VisualizationPanel)
from ui.components.CleanScrollBar import CleanScrollBar
from ui.components.Footer import Footer

# Define absolute path to the public icons folder (same logic as Sidebar.py)
ABS_PATH = Path(__file__).parent.parent
ICONS_PATH = ABS_PATH / "public"


def setup_ui(import_window):
    """Set up the UI for the import data window using custom components."""
    # Window props
    import_window.setWindowTitle("HDEMG Analysis - Import Data")
    import_window.setGeometry(100, 100, 1200, 800)
    import_window.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")
    # Main widget and layout
    import_window.central_widget = QWidget()
    import_window.setCentralWidget(import_window.central_widget)
    import_window.main_layout = QHBoxLayout(import_window.central_widget)
    import_window.main_layout.setContentsMargins(0, 0, 0, 0)
    import_window.main_layout.setSpacing(0)

    # Left sidebar
    import_window.sidebar_buttons = {}
    sidebar = _create_left_sidebar(import_window)
    left_scroll = QScrollArea()
    left_scroll.setWidgetResizable(True)
    left_scroll.setFixedWidth(180)
    CleanScrollBar.apply(left_scroll)
    left_scroll.setWidget(sidebar)
    sidebar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    import_window.left_sidebar_scroll_area = left_scroll
    import_window.main_layout.addWidget(left_scroll)
    import_window.central_stacked_widget = QStackedWidget()
    import_window.central_stacked_widget.setStyleSheet(
        "background-color: transparent;")
    import_window.import_data_page = _create_import_page(import_window)
    import_window.central_stacked_widget.addWidget(
        import_window.import_data_page)

    if hasattr(
            import_window,
            "mu_analysis_page") and import_window.mu_analysis_page is not None:
        import_window.central_stacked_widget.addWidget(
            import_window.mu_analysis_page)
    if hasattr(
            import_window,
            "decomposition_page") and import_window.decomposition_page is not None:
        import_window.central_stacked_widget.addWidget(
            import_window.decomposition_page)
    else:
        import_window.decomposition_page = create_placeholder_page(
            "Decomposition Page", import_window)
        import_window.central_stacked_widget.addWidget(
            import_window.decomposition_page)

    import_window.manual_editing_page = create_placeholder_page(
        "Manual Editing Page", import_window)
    import_window.central_stacked_widget.addWidget(
        import_window.manual_editing_page)
    import_window.main_layout.addWidget(
        import_window.central_stacked_widget, 1)
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

# NOTE: Creates 'Signal Preview' window


def create_preview_section(import_window):
    preview_card = CleanCard()
    preview_card.setMinimumHeight(500)
    preview_card.setAcceptDrops(True)  # Enable drop events

    preview_layout = QVBoxLayout()
    preview_layout.setContentsMargins(0, 0, 0, 0)
    preview_layout.setSpacing(5)

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

    import_window.preview_stacked_frame = QStackedWidget()

    import_window.preview_messages = QVBoxLayout()

    import_window.failure_message = QLabel("Error Loading Signal Preview")
    import_window.failure_message.setStyleSheet(
        "color: #FA0000; font-weight: bold;"
    )
    import_window.failure_message.setAlignment(Qt.AlignCenter)
    import_window.failure_message.setVisible(False)

    icon_container = QWidget()
    icon_layout = QHBoxLayout(icon_container)
    icon_layout.setContentsMargins(0, 0, 0, 0)
    icon_layout.setAlignment(Qt.AlignCenter)

    upload_icon_path = ICONS_PATH / "upload_icon.svg"

    if not upload_icon_path.exists():
        logger.warning(f"Icon not found at {upload_icon_path}")
    else:
        cloud_icon = QSvgWidget(str(upload_icon_path))
        cloud_icon.setStyleSheet("""
            background: transparent;
            margin-bottom: 8px;
        """)
        icon_layout.addWidget(cloud_icon)

    import_window.preview_message = QLabel(
        "Drag and drop your HDEMG files here\nor click 'Browse Files' above."
    )
    import_window.preview_message.setAlignment(Qt.AlignCenter)
    import_window.preview_message.setFont(QFont("Segoe UI", 12))
    import_window.preview_message.setStyleSheet(
        f"color: {CleanTheme.TEXT_SECONDARY};"
    )

    msg_container = QWidget()
    msg_layout = QVBoxLayout(msg_container)
    msg_layout.setAlignment(Qt.AlignCenter)
    msg_layout.addWidget(icon_container)
    msg_layout.addWidget(import_window.preview_message)

    import_window.preview_messages.addStretch()
    import_window.preview_messages.addWidget(import_window.failure_message)
    import_window.preview_messages.addWidget(msg_container)
    import_window.preview_messages.addStretch()

    import_window.preview_messages_widget = QWidget()
    import_window.preview_messages_widget.setLayout(
        import_window.preview_messages)
    import_window.preview_stacked_frame.addWidget(
        import_window.preview_messages_widget)

    import_window.preview_plot = pg.PlotWidget()
    import_window.preview_plot.setBackground("w")
    import_window.preview_plot.setLabel("left", "Amplitude", units="µV")
    import_window.preview_plot.setLabel("bottom", "Time", units="s")
    import_window.preview_plot.showGrid(x=True, y=True)
    import_window.preview_plot.setMinimumHeight(250)

    left_axis = import_window.preview_plot.getAxis("left")
    left_axis.setPen(pg.mkPen("black", width=2))
    bottom_axis = import_window.preview_plot.getAxis("bottom")
    bottom_axis.setPen(pg.mkPen("black", width=2))

    signal_panel = VisualizationPanel(plot_widget=import_window.preview_plot)
    import_window.preview_stacked_frame.addWidget(signal_panel)
    import_window.preview_stacked_frame.setCurrentIndex(0)

    preview_frame_layout = QVBoxLayout(preview_frame)
    preview_frame_layout.addWidget(
        import_window.preview_stacked_frame, stretch=3)

    lrbuttons = QWidget()
    button_layout = QHBoxLayout()
    import_window.left_button = ActionButton("←", primary=False)
    import_window.right_button = ActionButton("→", primary=False)
    import_window.left_button.setEnabled(False)
    import_window.right_button.setEnabled(False)
    import_window.left_button.clicked.connect(import_window.leftClicked)
    import_window.right_button.clicked.connect(import_window.rightClicked)
    button_layout.addWidget(import_window.left_button)
    button_layout.addWidget(import_window.right_button)
    lrbuttons.setLayout(button_layout)

    preview_layout.addWidget(preview_frame)
    preview_layout.addWidget(lrbuttons)

    preview_card.content_layout.addLayout(preview_layout)

    import_window.preview_frame = preview_frame
    import_window.dropzone = preview_card

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


'''
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
    # prev_btn = ActionButton("← Previous", primary=False)
    # prev_btn.clicked.connect(import_window.go_back)

    import_window.next_btn = ActionButton("Next →", primary=True)
    import_window.next_btn.clicked.connect(
        import_window.go_to_algorithm_screen)
    import_window.next_btn.setEnabled(False)

    # Add navigation buttons to layout
    # footer_layout.addWidget(prev_btn)
    footer_layout.addSpacing(10)
    footer_layout.addWidget(import_window.next_btn)
    return footer
'''


def find_sidebar(import_window):
    """Find the sidebar component in the application hierarchy."""
    if import_window.parent():
        sidebar = import_window.parent().findChild(Sidebar, "cleanSidebar")
        if sidebar:
            return sidebar
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


def create_placeholder_page(title, import_window):
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
    back_button = ActionButton("Back to Import View", primary=False)
    back_button.clicked.connect(import_window.show_import_data_view)
    layout.addItem(
        QSpacerItem(
            20,
            20,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding))
    layout.addWidget(back_button, 0, Qt.AlignmentFlag.AlignLeft)
    return page


def _create_left_sidebar(import_window):
    """Creates the improved left sidebar with SVG icons."""
    # Create sidebar with app title
    sidebar = Sidebar("HDEMG App")

    export_session_button = ActionButton("Export Session", primary=True)
    export_session_button.setMinimumHeight(40)  # Match SidebarButton height
    export_session_button.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Fixed)
    export_session_button.setCursor(QCursor(Qt.PointingHandCursor))
    export_session_button.clicked.connect(import_window.export_session)
    import_window.sidebar_buttons["export_session_button"] = export_session_button

    sidebar.layout.insertWidget(1, export_session_button)

    spacer = QSpacerItem(0, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)
    sidebar.layout.insertSpacerItem(2, spacer)

    upload_session_button = ActionButton("Load Session", primary=True)
    upload_session_button.setMinimumHeight(40)
    upload_session_button.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Fixed)
    upload_session_button.setCursor(QCursor(Qt.PointingHandCursor))
    upload_session_button.clicked.connect(import_window.load_session)
    import_window.sidebar_buttons["upload_session_button"] = upload_session_button

    sidebar.layout.insertWidget(1, upload_session_button)

    spacer = QSpacerItem(0, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)
    sidebar.layout.insertSpacerItem(2, spacer)

    # Define icon names
    icons = {
        "import": "import_data_icon",
        "decomposition": "decomposition_icon",
        "manual_edit": "mu_editing_icon",
        "mu_analysis": "mu_analysis_icon",
    }
    # Menu items mapped to display names
    menu_items = {
        "import": "Import Data",
        "decomposition": "Decomposition",
        "manual_edit": "MU Editing",
        "mu_analysis": "MU Analysis",
    }
    # Add buttons to sidebar and store references
    for key, display_name in menu_items.items():
        icon_name = icons.get(key)
        is_selected = key == "import"  # Import is initially selected
        button = sidebar.add_button(key, display_name, icon_name, is_selected)
        # Store reference and connect signal
        import_window.sidebar_buttons[key] = button
        # Connect button events based on key
        if key == "import":
            button.clicked.connect(
                import_window.show_import_data_view if hasattr(
                    import_window, "show_import_data_view") else lambda: None)
        elif key == "mu_analysis":
            button.clicked.connect(
                import_window.show_mu_analysis_view if hasattr(
                    import_window, "show_mu_analysis_view") else lambda: None)
        elif key == "decomposition":
            button.clicked.connect(
                import_window.show_decomposition_view if hasattr(
                    import_window,
                    "show_decomposition_view") else lambda: None)
        elif key == "manual_edit":
            button.clicked.connect(
                import_window.show_manual_editing_view
                if hasattr(import_window, "show_manual_editing_view")
                else lambda: None
            )
    return sidebar


def _create_import_page(import_window):
    right_layout = QWidget()
    right_v = QVBoxLayout(right_layout)
    right_v.setContentsMargins(0, 0, 0, 0)
    right_v.setSpacing(0)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("background: transparent; border: none;")

    content_area = QWidget()
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(25, 25, 25, 25)
    content_layout.setSpacing(10)

    header = SectionHeader("Import HDEMG Data")
    content_layout.addWidget(header)

    header_container = QWidget()
    header_layout = QHBoxLayout(header_container)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(10)
    header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    import_window.file_info_label = QLabel("No file selected")
    import_window.file_info_label.setStyleSheet(f"""
        color: {CleanTheme.TEXT_SECONDARY};
        font-size: 12px;
    """)

    browse_btn = ActionButton("Browse Files", primary=True)
    browse_btn.clicked.connect(import_window.select_file)
    browse_btn.setFixedHeight(36)
    browse_btn.setMinimumWidth(160)

    header_layout.addWidget(import_window.file_info_label)
    header_layout.addStretch(1)
    header_layout.addWidget(browse_btn)

    content_layout.addWidget(header_container)

    dropzone_card = create_preview_section(import_window)
    content_layout.addWidget(dropzone_card)

    configuration_section = create_configuration_section(import_window)
    content_layout.addLayout(configuration_section)

    content_layout.addStretch(1)
    scroll_area.setWidget(content_area)

    right_v.addWidget(scroll_area, 1)

    import_window.footer = Footer(
        on_prev=None,
        on_next=import_window.go_to_algorithm_screen
    )
    import_window.footer.next_btn.setEnabled(False)
    import_window.footer.prev_btn.hide()
    import_window.footer.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Fixed)
    import_window.footer.setFixedHeight(64)
    right_v.addWidget(import_window.footer, 0)

    return right_layout


def update_sidebar_selection(import_window, selected_key):
    """Updates the visual state of sidebar buttons based on selection."""
    # Use the sidebar's built-in selection method
    sidebar = import_window.findChild(Sidebar)
    if sidebar:
        sidebar.select_button(selected_key)
    else:
        # Fallback if sidebar isn't found
        for key, button in import_window.sidebar_buttons.items():
            if hasattr(button, "set_selected"):
                button.set_selected(key == selected_key)
            else:
                # Older style buttons
                button.blockSignals(True)
                button.setChecked(key == selected_key)
                button.blockSignals(False)
