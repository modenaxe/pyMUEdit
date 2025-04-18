from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QToolButton, QStyle
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, QSize


def setup_ui(import_window):
    """Set up the UI for the import data window."""
    # Set widget properties
    import_window.setWindowTitle("HDEMG Analysis - Import Data")
    import_window.resize(1200, 800)
    import_window.setStyleSheet(f"background-color: {import_window.colors['bg_main']};")

    # Set up main widget layout
    import_window.central_widget = QWidget()
    import_window.setLayout(QVBoxLayout())
    import_window.layout().setContentsMargins(0, 0, 0, 0)
    import_window.layout().setSpacing(0)

    # Create header, content area, and footer
    create_header(import_window)
    create_content_area(import_window)
    create_footer(import_window)


def create_header(import_window):
    """Create the header with title and a Back button."""
    header = QFrame()
    header.setObjectName("header")
    header.setFrameShape(QFrame.NoFrame)
    header.setStyleSheet(
        f"""
        #header {{
            background-color: {import_window.colors['bg_main']};
            border-bottom: 1px solid {import_window.colors['border']};
        }}
    """
    )
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(20, 10, 20, 10)

    # Title with icon
    title_layout = QHBoxLayout()
    title_icon = QLabel()
    title_icon.setPixmap(
        import_window.style().standardIcon(getattr(QStyle, "SP_FileDialogDetailedView")).pixmap(QSize(24, 24))
    )
    title_label = QLabel("HDEMG Analysis - Import Data")
    title_label.setFont(QFont("Arial", 14, QFont.Bold))
    title_layout.addWidget(title_icon)
    title_layout.addWidget(title_label)
    title_layout.addStretch()

    # Back button to return to dashboard
    back_btn = QPushButton("Back")
    back_btn.setStyleSheet("padding: 8px 12px;")
    back_btn.clicked.connect(import_window.return_to_dashboard_requested)

    header_layout.addLayout(title_layout)
    header_layout.addWidget(back_btn)

    import_window.layout().addWidget(header)


def create_content_area(import_window):
    """Create the main content area with sidebar and dropzone."""
    content_container = QFrame()
    content_container.setObjectName("contentContainer")
    content_container.setStyleSheet(
        f"""
        #contentContainer {{
            background-color: {import_window.colors['bg_main']};
            border: none;
        }}
    """
    )

    content_layout = QHBoxLayout(content_container)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(0)

    # Create sidebar in content area
    create_sidebar(import_window, content_layout)
    # Create right panel with dropzone and preview
    create_right_panel(import_window, content_layout)

    import_window.layout().addWidget(content_container, 1)


def create_sidebar(import_window, parent_layout):
    """Create the left sidebar with Import button and recent files."""
    sidebar = QFrame()
    sidebar.setObjectName("sidebar")
    sidebar.setFixedWidth(280)
    sidebar.setStyleSheet(
        f"""
        #sidebar {{
            background-color: {import_window.colors['bg_sidebar']};
            border-right: 1px solid {import_window.colors['border']};
        }}
    """
    )

    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(20, 20, 20, 20)
    sidebar_layout.setSpacing(15)

    # Import File button
    import_btn = QPushButton("  Import File")
    import_btn.setObjectName("importButton")
    import_btn.setIcon(import_window.style().standardIcon(getattr(QStyle, "SP_DialogOpenButton")))
    import_btn.setIconSize(QSize(16, 16))
    import_btn.setMinimumHeight(40)
    import_btn.setStyleSheet(
        f"""
        #importButton {{
            background-color: {import_window.colors['button_bg']};
            color: {import_window.colors['button_text']};
            border: none;
            border-radius: 4px;
            padding: 10px;
            font-weight: bold;
            text-align: left;
        }}
        #importButton:hover {{
            background-color: #444444;
        }}
    """
    )
    import_btn.clicked.connect(import_window.select_file)

    recent_label = QLabel("Recent Files")
    recent_label.setFont(QFont("Arial", 12, QFont.Bold))
    recent_label.setContentsMargins(0, 10, 0, 0)

    sidebar_layout.addWidget(import_btn)
    sidebar_layout.addWidget(recent_label)

    # Updated: File items now have a defined background color so they remain visible on hover.
    for file in import_window.recent_files:
        file_item = create_file_item(import_window, file)
        sidebar_layout.addWidget(file_item)

    sidebar_layout.addStretch(1)

    # Expand/collapse button (optional)
    expand_btn = QToolButton()
    expand_btn.setIcon(import_window.style().standardIcon(getattr(QStyle, "SP_ArrowLeft")))
    expand_btn.setIconSize(QSize(16, 16))
    expand_btn.setFixedSize(32, 32)
    expand_btn.setStyleSheet(
        """
        QToolButton {
            background-color: #e0e0e0;
            border: none;
            border-radius: 16px;
        }
        QToolButton:hover {
            background-color: #d0d0d0;
        }
    """
    )
    sidebar_layout.addWidget(expand_btn, 0, getattr(Qt, "AlignHCenter"))

    parent_layout.addWidget(sidebar)


def create_file_item(import_window, filename):
    """Create a file item for the recent files list."""

    # Create a custom frame for file items that handles clicks properly
    class ClickableFileItem(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.filename = filename

        def mousePressEvent(self, event):
            # Explicitly call the load_recent_file method with the filename
            if hasattr(import_window, "load_recent_file"):
                import_window.load_recent_file(self.filename)
            super().mousePressEvent(event)

    # Create the custom item
    item = ClickableFileItem()
    item.setObjectName(f"fileItem_{filename.replace('.', '_')}")
    item.setMinimumHeight(40)
    # Instead of a transparent background, we use the sidebar color
    item.setStyleSheet(
        f"""
        #fileItem_{filename.replace('.', '_')} {{
            background-color: {import_window.colors['bg_sidebar']};
            border-radius: 4px;
        }}
        #fileItem_{filename.replace('.', '_')}:hover {{
            background-color: #eaeaea;
        }}
    """
    )
    item_layout = QHBoxLayout(item)
    item_layout.setContentsMargins(10, 5, 10, 5)

    file_icon = QLabel()
    file_icon.setPixmap(import_window.style().standardIcon(getattr(QStyle, "SP_FileIcon")).pixmap(QSize(16, 16)))
    file_label = QLabel(filename)

    item_layout.addWidget(file_icon)
    item_layout.addWidget(file_label)
    item_layout.addStretch()

    item.setCursor(QCursor(getattr(Qt, "PointingHandCursor")))
    return item


def create_right_panel(import_window, parent_layout):
    """Create the right panel with dropzone and preview."""
    right_panel = QFrame()
    right_panel.setObjectName("rightPanel")
    right_panel.setStyleSheet(
        f"""
        #rightPanel {{
            background-color: {import_window.colors['bg_main']};
            border: none;
        }}
    """
    )
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(20, 20, 20, 20)
    right_layout.setSpacing(20)

    # Create dropzone
    import_window.dropzone = create_dropzone(import_window)
    preview_label = QLabel("Signal Preview")
    preview_label.setFont(QFont("Arial", 14))
    preview_label.setContentsMargins(0, 10, 0, 10)

    import_window.preview_frame = QFrame()
    import_window.preview_frame.setObjectName("previewFrame")
    import_window.preview_frame.setMinimumHeight(300)
    import_window.preview_frame.setStyleSheet(
        f"""
        #previewFrame {{
            background-color: #f0f0f0;
            border: 1px solid {import_window.colors['border']};
            border-radius: 4px;
        }}
    """
    )
    import_window.preview_message = QLabel("No file selected. Import a file to see a preview.")
    import_window.preview_message.setAlignment(getattr(Qt, "AlignCenter"))
    preview_layout = QVBoxLayout(import_window.preview_frame)
    preview_layout.addWidget(import_window.preview_message)

    right_layout.addWidget(import_window.dropzone)
    right_layout.addWidget(preview_label)
    right_layout.addWidget(import_window.preview_frame)

    parent_layout.addWidget(right_panel, 1)


def create_dropzone(import_window):
    """Create a dropzone for files."""
    dropzone = QFrame()
    dropzone.setObjectName("dropzone")
    dropzone.setMinimumHeight(200)
    dropzone.setStyleSheet(
        f"""
        #dropzone {{
            background-color: {import_window.colors['bg_dropzone']};
            border: 2px dashed {import_window.colors['border']};
            border-radius: 8px;
        }}
    """
    )
    dropzone_layout = QVBoxLayout(dropzone)

    cloud_icon = QLabel()
    cloud_icon_pixmap = import_window.style().standardIcon(getattr(QStyle, "SP_DriveNetIcon")).pixmap(QSize(48, 48))
    cloud_icon.setPixmap(cloud_icon_pixmap)
    cloud_icon.setAlignment(getattr(Qt, "AlignCenter"))

    drag_label = QLabel("Drag and drop your HDEMG files here")
    drag_label.setAlignment(getattr(Qt, "AlignCenter"))
    drag_label.setFont(QFont("Arial", 12))

    or_label = QLabel("or")
    or_label.setAlignment(getattr(Qt, "AlignCenter"))

    import_window.file_info_label = QLabel("")
    import_window.file_info_label.setAlignment(getattr(Qt, "AlignCenter"))
    import_window.file_info_label.setFont(QFont("Arial", 11))
    import_window.file_info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
    import_window.file_info_label.setVisible(False)

    browse_btn = QPushButton("Browse Files")
    browse_btn.setObjectName("browseButton")
    browse_btn.setFixedWidth(150)
    browse_btn.setStyleSheet(
        f"""
        #browseButton {{
            background-color: #e0e0e0;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }}
        #browseButton:hover {{
            background-color: #d0d0d0;
        }}
    """
    )
    browse_btn.clicked.connect(import_window.select_file)

    dropzone_layout.addStretch()
    dropzone_layout.addWidget(cloud_icon)
    dropzone_layout.addWidget(drag_label)
    dropzone_layout.addWidget(import_window.file_info_label)
    dropzone_layout.addWidget(or_label)
    dropzone_layout.addWidget(browse_btn, 0, getattr(Qt, "AlignCenter"))
    dropzone_layout.addStretch()

    # The actual event handlers will be set in the main class

    return dropzone


def create_footer(import_window):
    """Create footer with file info and navigation."""
    footer = QFrame()
    footer.setObjectName("footer")
    footer.setFrameShape(QFrame.NoFrame)
    footer.setStyleSheet(
        f"""
        #footer {{
            background-color: {import_window.colors['bg_main']};
            border-top: 1px solid {import_window.colors['border']};
        }}
    """
    )
    footer_layout = QHBoxLayout(footer)
    footer_layout.setContentsMargins(20, 10, 20, 10)

    import_window.footer_file_info = QLabel("No file selected")
    footer_layout.addWidget(import_window.footer_file_info)
    footer_layout.addStretch(1)

    import_window.size_info = QLabel("Size: --")
    footer_layout.addWidget(import_window.size_info)
    import_window.format_info = QLabel("Format: --")
    footer_layout.addWidget(import_window.format_info)

    nav_layout = QHBoxLayout()
    prev_btn = QPushButton("← Previous")
    prev_btn.setObjectName("navButton")
    prev_btn.clicked.connect(import_window.go_back)
    import_window.next_btn = QPushButton("Next →")
    import_window.next_btn.setObjectName("navButton")
    import_window.next_btn.clicked.connect(import_window.go_to_algorithm_screen)
    import_window.next_btn.setEnabled(False)

    for btn in [prev_btn, import_window.next_btn]:
        btn.setMinimumWidth(120)
        btn.setStyleSheet(
            f"""
            #navButton {{
                background-color: {import_window.colors['button_bg']};
                color: {import_window.colors['button_text']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            #navButton:hover {{
                background-color: #444444;
            }}
            #navButton:disabled {{
                background-color: #777777;
                color: #aaaaaa;
            }}
        """
        )
    nav_layout.addWidget(prev_btn)
    nav_layout.addSpacing(10)
    nav_layout.addWidget(import_window.next_btn)
    footer_layout.addLayout(nav_layout)

    import_window.layout().addWidget(footer)
