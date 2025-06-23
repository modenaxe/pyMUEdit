from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication, QScrollArea
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtSvg import QSvgWidget

# Import custom components
from ui.components import CleanTheme, CleanCard, ActionButton, SectionHeader, Sidebar


def setup_ui(import_window):
    """Set up the UI for the import data window using custom components."""
    # Set widget properties
    import_window.setWindowTitle("HDEMG Analysis - Import Data")
    import_window.resize(1200, 800)

    # Set up main layout
    main_layout = QVBoxLayout(import_window)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Create main content layout
    content_layout = QHBoxLayout()
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(0)

    # Create right content area
    right_content = create_right_content(import_window)
    content_layout.addWidget(right_content, 1)

    # Add content to main layout
    main_layout.addLayout(content_layout, 1)

    # Add footer
    footer = create_footer(import_window)
    main_layout.addWidget(footer)

    # Store references to functions for sidebar management
    import_window.update_sidebar_with_recent_files = lambda: update_sidebar_with_recent_files(import_window)
    import_window.restore_sidebar = lambda: restore_sidebar(import_window)


def create_right_content(import_window):
    """Create the right content area with dropzone and preview."""
    # Create scroll area for content
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("background: transparent; border: none;")

    # Create container widget
    right_content = QWidget()
    right_layout = QVBoxLayout(right_content)
    right_layout.setContentsMargins(25, 25, 25, 25)
    right_layout.setSpacing(20)

    # Add section header
    header = SectionHeader("Import HDEMG Data")
    right_layout.addWidget(header)

    # Create dropzone card
    dropzone_card = create_dropzone_card(import_window)
    right_layout.addWidget(dropzone_card)

    # Create preview section
    preview_section = create_preview_section(import_window)
    right_layout.addWidget(preview_section)

    # Add stretch to push content to the top
    right_layout.addStretch(1)

    # Set the content widget to the scroll area
    scroll_area.setWidget(right_content)

    return scroll_area


def create_dropzone_card(import_window):
    """Create a clean card for the file dropzone."""
    dropzone_card = CleanCard()
    dropzone_card.setMinimumHeight(250)

    # Create layout for content
    dropzone_layout = QVBoxLayout()
    dropzone_layout.setContentsMargins(20, 20, 20, 20)
    dropzone_layout.setSpacing(15)
    dropzone_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Add SVG icon
    icon_container = QWidget()
    icon_layout = QHBoxLayout(icon_container)
    icon_layout.setContentsMargins(0, 0, 0, 0)
    icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    cloud_icon = QSvgWidget("public/upload_icon.svg")
    cloud_icon.setFixedSize(48, 33)
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
    import_window.file_info_label.setStyleSheet(f"color: #4CAF50; font-weight: bold;")
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


def create_preview_section(import_window):
    """Create the signal preview section."""
    preview_card = CleanCard()
    preview_card.setMinimumHeight(200)

    # Create layout for content
    preview_layout = QVBoxLayout()
    preview_layout.setContentsMargins(0, 0, 0, 0)
    preview_layout.setSpacing(15)

    # Add section header
    preview_header = QLabel("Signal Preview")
    preview_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
    preview_header.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
    preview_layout.addWidget(preview_header)

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

    # Create preview message
    import_window.preview_message = QLabel("No file selected. Import a file to see a preview.")
    import_window.preview_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    import_window.preview_message.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")

    # Add message to preview frame
    preview_frame_layout = QVBoxLayout(preview_frame)
    preview_frame_layout.addWidget(import_window.preview_message)

    # Add preview frame to layout
    preview_layout.addWidget(preview_frame)

    # Add layout to card
    preview_card.content_layout.addLayout(preview_layout)

    # Store reference to preview frame
    import_window.preview_frame = preview_frame

    return preview_card


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
    import_window.footer_file_info.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")

    import_window.size_info = QLabel("Size: --")
    import_window.size_info.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")

    import_window.format_info = QLabel("Format: --")
    import_window.format_info.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")

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
    import_window.next_btn.clicked.connect(import_window.go_to_algorithm_screen)
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
        sidebar.add_recent_files_section(import_window.recent_files, import_window.load_recent_file)


def restore_sidebar(import_window):
    """Restore the sidebar to its default state."""
    sidebar = find_sidebar(import_window)
    if sidebar and hasattr(sidebar, "clear_recent_files_section"):
        sidebar.clear_recent_files_section()
