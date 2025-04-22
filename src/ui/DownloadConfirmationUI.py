import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QStyle,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize


def get_icon(standard_icon_enum):
    """Gets a standard Qt icon."""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app.style().standardIcon(getattr(QStyle, standard_icon_enum))  # type:ignore


def setup_ui(widget):
    """Set up the UI for the export completion widget."""
    # Define color scheme (can be inherited or defined here)
    widget.colors = {
        "bg_main": "#f8f9fa",  # Likely overridden by container
        "bg_card": "#ffffff",
        "border": "#e0e0e0",
        "shadow": QColor(0, 0, 0, 30),
        "text_primary": "#212529",
        "text_secondary": "#6c757d",
        "text_success": "#198754",
        "button_dark_bg": "#212529",
        "button_dark_text": "#ffffff",
        "button_dark_hover": "#343a40",
        "download_row_bg": "#f8f9fa",
        "download_row_border": "#eeeeee",
        "download_btn_hover": "#dee2e6",
        "download_btn_pressed": "#ced4da",
    }

    # --- Main Layout for widget ---
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(10)

    # --- Top: Return Button ---
    main_layout.addWidget(create_return_button(widget), alignment=Qt.AlignmentFlag.AlignLeft)
    main_layout.addSpacerItem(QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # --- Center: Content Area (Cards) ---
    content_layout = QVBoxLayout()
    content_layout.setSpacing(20)
    content_layout.addWidget(create_confirmation_card(widget))
    content_layout.addWidget(create_recent_exports_section(widget))
    main_layout.addLayout(content_layout)
    main_layout.addStretch(1)

    # Store references to labels that will be updated
    widget._download_filename_label = None
    widget._download_filesize_label = None
    widget._main_download_filename = None  # Store filename for download button


def create_styled_card(widget):
    """Creates a styled card container with shadow effect."""
    card = QFrame()
    card.setFrameShape(QFrame.StyledPanel)
    card.setObjectName("styledCardComplete")
    card.setStyleSheet(
        f"""
        #styledCardComplete {{
            background-color: {widget.colors['bg_card']};
            border: 1px solid {widget.colors['border']};
            border-radius: 8px;
        }}
        #styledCardComplete > * {{
            background-color: transparent;
            border: none;
        }}
    """
    )

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(15)
    shadow.setColor(widget.colors["shadow"])
    shadow.setOffset(0, 2)
    card.setGraphicsEffect(shadow)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(20, 20, 20, 20)
    card_layout.setSpacing(15)

    return card, card_layout


def create_return_button(widget):
    """Creates the return button at the top of the widget."""
    return_button = QPushButton(" 🡸 Return to Export Setup")
    return_button.setCursor(Qt.CursorShape.PointingHandCursor)
    return_button.setFont(QFont("Arial", 9))
    return_button.setStyleSheet(
        f"""
        QPushButton {{
            color: {widget.colors['text_secondary']};
            background-color: transparent;
            border: none;
            text-align: left;
            padding: 5px 0px;
        }}
        QPushButton:hover {{
            color: {widget.colors['text_primary']};
            text-decoration: underline;
        }}
    """
    )
    return_button.clicked.connect(widget.handle_return)
    return return_button


def create_confirmation_card(widget):
    """Creates the main confirmation card with success icon and download button."""
    confirm_card, confirm_layout = create_styled_card(widget)
    confirm_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Success icon
    icon_label = QLabel()
    icon_size = 40
    # Get icon pixmap correctly using the helper function
    icon = get_icon("SP_DialogApplyButton")
    icon_label.setPixmap(icon.pixmap(QSize(icon_size // 2, icon_size // 2)))
    icon_label.setFixedSize(icon_size, icon_size)
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setStyleSheet(
        f"""
        QLabel {{
            background-color: {widget.colors['text_success']};
            border-radius: {icon_size // 2}px;
            border: 2px solid {widget.colors['bg_card']};
            padding: 5px;
        }}
    """
    )

    # Title and subtitle
    title_label = QLabel("Export Complete!")
    title_label.setFont(QFont("Arial", 16, QFont.Bold))
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet(f"color: {widget.colors['text_primary']}; border: none;")

    subtitle_label = QLabel("File has been exported.")
    subtitle_label.setFont(QFont("Arial", 9))
    subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle_label.setStyleSheet(f"color: {widget.colors['text_secondary']}; border: none;")
    subtitle_label.setWordWrap(True)

    # Add elements to layout
    confirm_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
    confirm_layout.addSpacerItem(QSpacerItem(10, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))
    confirm_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
    confirm_layout.addWidget(subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)
    confirm_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # Add download row with placeholders
    confirm_layout.addWidget(create_download_row(widget, "Initializing...", "..."))

    return confirm_card


def create_download_row(widget, filename, filesize):
    """Creates the download information row with filename and download button."""
    download_frame = QFrame()
    download_frame.setObjectName("downloadRowComplete")
    download_frame.setStyleSheet(
        f"""
        #downloadRowComplete {{
            background-color: {widget.colors['download_row_bg']};
            border: 1px solid {widget.colors['download_row_border']};
            border-radius: 5px;
            padding: 10px 12px;
        }}
        #downloadRowComplete > * {{
            background-color: transparent;
            border: none;
        }}
    """
    )

    row_layout = QHBoxLayout(download_frame)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(10)

    # File icon
    icon_label = QLabel()
    # Get icon pixmap correctly
    icon = get_icon("SP_FileIcon")
    icon_label.setPixmap(icon.pixmap(QSize(18, 18)))
    icon_label.setFixedSize(QSize(18, 18))
    icon_label.setStyleSheet("margin-top: 2px;")

    # File info section
    info_layout = QVBoxLayout()
    info_layout.setSpacing(1)
    info_layout.setContentsMargins(0, 0, 0, 0)

    widget._download_filename_label = QLabel(filename)
    widget._download_filename_label.setFont(QFont("Arial", 10, QFont.Bold))
    widget._download_filename_label.setStyleSheet(f"color: {widget.colors['text_primary']};")

    widget._download_filesize_label = QLabel(filesize)
    widget._download_filesize_label.setFont(QFont("Arial", 9))
    widget._download_filesize_label.setStyleSheet(f"color: {widget.colors['text_secondary']};")

    info_layout.addWidget(widget._download_filename_label)
    info_layout.addWidget(widget._download_filesize_label)

    # Download button
    download_button = QPushButton("Download")
    download_button.setIcon(QIcon("public/cloud_download.svg"))
    download_button.setIconSize(QSize(24, 24))
    download_button.setFont(QFont("Arial", 9, QFont.Bold))
    download_button.setMinimumHeight(30)
    download_button.setCursor(Qt.CursorShape.PointingHandCursor)
    download_button.setStyleSheet(
        f"""
        QPushButton {{
            background-color: #3CB371; 
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 15px;
        }}
        QPushButton:hover {{
            background-color: #20c997;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        QPushButton:pressed {{
            background-color: {widget.colors['button_dark_bg']};
            padding-left: 7px;
            padding-top: 7px;
        }}
    """
    )
    download_button.clicked.connect(widget.handle_main_download)

    # Assemble the layout
    row_layout.addWidget(icon_label)
    row_layout.addLayout(info_layout)
    row_layout.addStretch(1)
    row_layout.addWidget(download_button)

    return download_frame


def create_recent_exports_section(widget):
    """Creates the recent exports section showing past export files."""
    recent_card, recent_layout = create_styled_card(widget)

    title_label = QLabel("Recent Exports")
    title_label.setFont(QFont("Arial", 14, QFont.Bold))
    title_label.setStyleSheet(f"color: {widget.colors['text_primary']}; margin-bottom: 5px;")
    recent_layout.addWidget(title_label)

    # Sample recent export data
    recent_exports_data = [
        {"filename": "Export_2025_01_15.csv", "metadata": "15.2 MB • Exported today"},
        {"filename": "Export_2025_01_14.csv", "metadata": "12.8 MB • Exported yesterday"},
        {"filename": "Export_2025_01_13.csv", "metadata": "14.5 MB • Exported 2 days ago"},
    ]

    for item_data in recent_exports_data:
        recent_layout.addWidget(create_recent_export_item(widget, item_data["filename"], item_data["metadata"]))

    recent_layout.addStretch(1)
    return recent_card


def create_recent_export_item(widget, filename, metadata):
    """Creates an item in the recent exports list."""
    item_widget = QFrame()
    item_widget.setObjectName("recentExportItemComplete")
    item_widget.setStyleSheet(
        f"""
        #recentExportItemComplete {{
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 6px 0px;
        }}
        #recentExportItemComplete:hover {{
            background-color: {widget.colors['download_row_bg']};
        }}
        #recentExportItemComplete > * {{
            background-color: transparent;
            border: none;
        }}
    """
    )

    item_layout = QHBoxLayout(item_widget)
    item_layout.setContentsMargins(5, 0, 5, 0)
    item_layout.setSpacing(12)

    # File icon
    icon_label = QLabel()
    # Use a fallback file icon if the svg file is not found
    try:
        pixmap = QPixmap("fileIcon.svg").scaled(
            QSize(17, 17), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
    except:
        # Fallback to standard file icon
        icon = get_icon("SP_FileIcon")
        pixmap = icon.pixmap(QSize(17, 17))

    icon_label.setPixmap(pixmap)
    icon_label.setFixedSize(QSize(18, 18))
    icon_label.setStyleSheet("margin-top: 1px;")
    item_layout.addWidget(icon_label)

    # File info
    info_widget = QWidget()
    info_layout = QVBoxLayout(info_widget)
    info_layout.setContentsMargins(0, 0, 0, 0)
    info_layout.setSpacing(1)

    filename_label = QLabel(filename)
    filename_label.setFont(QFont("Arial", 10))
    filename_label.setStyleSheet(f"color: {widget.colors['text_primary']};")

    metadata_label = QLabel(metadata)
    metadata_label.setFont(QFont("Arial", 9))
    metadata_label.setStyleSheet(f"color: {widget.colors['text_secondary']};")

    info_layout.addWidget(filename_label)
    info_layout.addWidget(metadata_label)
    item_layout.addWidget(info_widget, 1)

    # Download button
    download_button = QPushButton("")
    download_button.setIcon(QIcon("public/cloud_download.svg"))
    download_button.setIconSize(QSize(24, 24))
    download_button.setFont(QFont("Arial", 13))
    download_button.setFixedSize(30, 30)
    download_button.setCursor(Qt.CursorShape.PointingHandCursor)
    download_button.setToolTip(f"Download {filename}")
    download_button.setStyleSheet(
        f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {widget.colors['download_btn_hover']};
        }}
        QPushButton:pressed {{
            background-color: {widget.colors['download_btn_pressed']};
        }}
    """
    )
    download_button.clicked.connect(lambda checked=False, fn=filename: widget.handle_recent_download(fn))
    item_layout.addWidget(download_button)

    return item_widget


# For testing the UI independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_widget = QWidget()

    # Create dummy handlers for testing
    test_widget.handle_return = lambda: print("Return button clicked")
    test_widget.handle_main_download = lambda: print("Main download button clicked")
    test_widget.handle_recent_download = lambda fn: print(f"Recent download clicked: {fn}")

    # Set up the UI
    setup_ui(test_widget)
    test_widget.resize(600, 500)
    test_widget.show()

    sys.exit(app.exec_())
