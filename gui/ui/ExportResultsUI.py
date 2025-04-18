import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QStyle,
    QStackedWidget,
)
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtCore import Qt, QSize


def get_icon(standard_icon):
    """Helper function to get standard icons."""
    return QApplication.style().standardIcon(getattr(QStyle, standard_icon))  # type:ignore


def setup_ui(window):
    """Set up the UI for the export results window."""
    # Define color scheme
    window.colors = {
        "bg_main": "#fdfdfd",
        "text_secondary": "#777777",
    }
    window.setStyleSheet(f"background-color: {window.colors['bg_main']};")

    # Create main layout
    main_layout = QVBoxLayout(window)
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(15)

    # Add title section
    add_title_section(window, main_layout)

    # Create stacked widget for different views
    window.stacked_widget = QStackedWidget(window)
    main_layout.addWidget(window.stacked_widget, 1)

    # Add footer with last export info
    window.footer_label = QLabel("Last export: January 15, 2025 at 14:30")
    window.footer_label.setFont(QFont("Arial", 9))
    window.footer_label.setStyleSheet(f"color: {window.colors['text_secondary']}; border: none; padding-top: 10px;")
    window.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(window.footer_label)


def add_title_section(window, main_layout):
    """Add the title and subtitle to the main layout."""
    title_layout = QVBoxLayout()
    title_layout.setSpacing(4)

    window.main_title_label = QLabel("Export Results")
    window.main_title_label.setFont(QFont("Arial", 16, QFont.Bold))
    window.main_title_label.setStyleSheet("color: #333333; border: none;")

    window.main_subtitle_label = QLabel("Export your motor unit firing patterns data")
    window.main_subtitle_label.setFont(QFont("Arial", 10))
    window.main_subtitle_label.setStyleSheet("color: #777777; border: none; margin-bottom: 5px;")

    title_layout.addWidget(window.main_title_label)
    title_layout.addWidget(window.main_subtitle_label)
    main_layout.addLayout(title_layout)


def create_export_setup_widget(parent):
    """Create the initial setup widget for selecting export options."""
    setup_widget = QWidget(parent)

    # Define colors for this widget
    colors = {
        "bg_main": "#fdfdfd",
        "bg_card": "#ffffff",
        "border_light": "#e0e0e0",
        "text_primary": "#333333",
        "text_secondary": "#777777",
        "button_dark_bg": "#212529",
        "button_dark_text": "#ffffff",
        "button_dark_hover": "#343a40",
        "item_bg_hover": "#f0f0f0",
    }

    # Set up layout
    setup_layout = QVBoxLayout(setup_widget)
    setup_layout.setContentsMargins(0, 0, 0, 0)
    setup_layout.setSpacing(20)

    # Add sections to the layout
    setup_card = create_export_setup_section(setup_widget, colors)
    setup_layout.addWidget(setup_card)
    setup_layout.addWidget(create_recent_exports_section(setup_widget, colors))
    setup_layout.addStretch(1)

    # Store references to key UI elements that parent window will need
    setup_widget.format_combo = setup_card.findChild(QComboBox)
    setup_widget.export_button = setup_card.findChild(QPushButton)

    return setup_widget


def create_export_setup_section(widget, colors):
    """Create the export setup section with format selection."""
    setup_card = QFrame()
    setup_card.setObjectName("setupCard")
    setup_card.setFrameShape(QFrame.StyledPanel)
    setup_card.setStyleSheet(
        f""" #setupCard {{ background-color: {colors['bg_card']}; border: 1px solid {colors['border_light']}; border-radius: 8px; padding: 15px; }} QLabel {{ border: none; background: transparent; }} QComboBox {{ border: 1px solid {colors['border_light']}; border-radius: 4px; padding: 6px 10px; background-color: {colors['bg_card']}; color: {colors['text_primary']}; font-size: 9pt; min-height: 20px; }} QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left: 1px solid {colors['border_light']}; }} QComboBox::down-arrow {{ image: url(:/qt-project.org/styles/commonstyle/images/down_arrow-16.png); width: 12px; height: 12px; }} """
    )
    card_layout = QVBoxLayout(setup_card)
    card_layout.setContentsMargins(0, 0, 0, 0)
    card_layout.setSpacing(15)

    # Add format selection dropdown
    format_label = QLabel("Select File Format")
    format_label.setFont(QFont("Arial", 9, QFont.Bold))
    format_label.setStyleSheet(f"color: {colors['text_primary']}; margin-bottom: -5px;")
    card_layout.addWidget(format_label)

    format_combo = QComboBox()
    format_combo.setObjectName("formatCombo")
    format_combo.addItems(
        [".csv (Comma Separated Values)", ".mat (MATLAB)", ".xlsx (Excel Spreadsheet)", ".txt (Text File)"]
    )
    format_combo.setPlaceholderText("Choose an export format...")
    format_combo.setCurrentIndex(-1)
    card_layout.addWidget(format_combo)

    # Add data details section
    data_details_frame = QFrame()
    data_details_layout = QVBoxLayout(data_details_frame)
    data_details_layout.setContentsMargins(0, 5, 0, 5)
    data_details_layout.setSpacing(8)

    data_title_label = QLabel("Selected Data")
    data_title_label.setFont(QFont("Arial", 9, QFont.Bold))
    data_title_label.setStyleSheet(f"color: {colors['text_primary']};")
    data_details_layout.addWidget(data_title_label)

    data_details_layout.addWidget(
        create_info_item(widget, get_icon("SP_FileIcon"), "Motor Unit Firing Patterns", colors)
    )
    data_details_layout.addWidget(
        create_info_item(widget, get_icon("SP_DialogApplyButton"), "Recording Duration: 120s", colors)
    )
    data_details_layout.addWidget(create_info_item(widget, get_icon("SP_ComputerIcon"), "Units Detected: 12", colors))
    card_layout.addWidget(data_details_frame)

    # Add export button
    export_button = QPushButton("Export Data")
    export_button.setObjectName("exportButton")
    export_button.setFont(QFont("Arial", 10, QFont.Bold))
    export_button.setIcon(get_icon("SP_ArrowDown"))
    export_button.setIconSize(QSize(16, 16))
    export_button.setMinimumHeight(40)
    export_button.setCursor(Qt.CursorShape.PointingHandCursor)
    export_button.setStyleSheet(
        f""" QPushButton {{ background-color: {colors['button_dark_bg']}; color: {colors['button_dark_text']}; border: none; border-radius: 4px; padding: 8px 15px; }} QPushButton:hover {{ background-color: {colors['button_dark_hover']}; }} """
    )
    # We'll connect the button later in the main class
    card_layout.addWidget(export_button)

    return setup_card


def create_info_item(widget, icon, text, colors):
    """Create an information item with icon and text."""
    item_widget = QWidget()
    item_layout = QHBoxLayout(item_widget)
    item_layout.setContentsMargins(0, 0, 0, 0)
    item_layout.setSpacing(8)

    icon_label = QLabel()
    icon_label.setPixmap(icon.pixmap(QSize(16, 16)))
    icon_label.setFixedSize(QSize(18, 18))
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    text_label = QLabel(text)
    text_label.setFont(QFont("Arial", 9))
    text_label.setStyleSheet(f"color: {colors['text_secondary']};")

    item_layout.addWidget(icon_label)
    item_layout.addWidget(text_label)
    item_layout.addStretch(1)

    return item_widget


def create_recent_exports_section(widget, colors):
    """Create the recent exports section."""
    recent_card = QFrame()
    recent_card.setObjectName("recentCardSetup")
    recent_card.setFrameShape(QFrame.StyledPanel)
    recent_card.setStyleSheet(
        f""" #recentCardSetup {{ background-color: {colors['bg_card']}; border: 1px solid {colors['border_light']}; border-radius: 8px; padding: 15px; }} #recentCardSetup > QLabel {{ color: {colors['text_primary']}; font-size: 11pt; font-weight: bold; border: none; background: transparent; margin-bottom: 5px; }} """
    )
    card_layout = QVBoxLayout(recent_card)
    card_layout.setContentsMargins(0, 0, 0, 0)
    card_layout.setSpacing(5)

    title_label = QLabel("Recent Exports")
    card_layout.addWidget(title_label)

    recent_exports_data = [
        {
            "icon": get_icon("SP_DialogHelpButton"),
            "filename": "firing_patterns_2025.01.15.csv",
            "metadata": "2.4 MB • Completed",
        },
        {
            "icon": get_icon("SP_DriveHDIcon"),
            "filename": "firing_patterns_2025.01.14.mat",
            "metadata": "3.1 MB • Completed",
        },
    ]

    if not recent_exports_data:
        no_exports_label = QLabel("No recent exports found.")
        no_exports_label.setStyleSheet(f"color: {colors['text_secondary']}; font-style: italic; padding: 10px;")
        no_exports_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(no_exports_label)
    else:
        for export_data in recent_exports_data:
            card_layout.addWidget(
                create_recent_export_item(
                    widget, export_data["icon"], export_data["filename"], export_data["metadata"], colors
                )
            )

    return recent_card


def create_recent_export_item(widget, icon, filename, metadata, colors):
    """Create a recent export item with download button."""
    item_frame = QFrame()
    item_frame.setObjectName("recentItemSetup")
    item_frame.setMinimumHeight(50)
    item_frame.setCursor(Qt.CursorShape.PointingHandCursor)
    item_frame.setStyleSheet(
        f""" QFrame#recentItemSetup {{ background-color: transparent; border-radius: 4px; border: 1px solid transparent; padding: 5px 0px; }} QFrame#recentItemSetup:hover {{ background-color: {colors['item_bg_hover']}; border: 1px solid {colors['border_light']}; }} QLabel {{ background-color: transparent; border: none; }} QPushButton#downloadBtnSetup {{ background-color: transparent; border: none; padding: 5px; border-radius: 15px; qproperty-iconSize: 18px 18px; }} QPushButton#downloadBtnSetup:hover {{ background-color: {colors['border_light']}; }} """
    )
    item_layout = QHBoxLayout(item_frame)
    item_layout.setContentsMargins(10, 5, 10, 5)
    item_layout.setSpacing(10)

    icon_label = QLabel()
    icon_label.setPixmap(icon.pixmap(QSize(20, 20)))
    icon_label.setFixedSize(QSize(24, 24))
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    item_layout.addWidget(icon_label)

    text_layout = QVBoxLayout()
    text_layout.setContentsMargins(0, 0, 0, 0)
    text_layout.setSpacing(1)

    filename_label = QLabel(filename)
    filename_label.setFont(QFont("Arial", 9, QFont.Bold))
    filename_label.setStyleSheet(f"color: {colors['text_primary']};")

    metadata_label = QLabel(metadata)
    metadata_label.setFont(QFont("Arial", 8))
    metadata_label.setStyleSheet(f"color: {colors['text_secondary']};")

    text_layout.addWidget(filename_label)
    text_layout.addWidget(metadata_label)
    item_layout.addLayout(text_layout, 1)

    download_button = QPushButton()
    download_button.setObjectName("downloadBtnSetup")
    download_button.setIcon(get_icon("SP_ArrowDown"))
    download_button.setFixedSize(QSize(30, 30))
    download_button.setCursor(Qt.CursorShape.PointingHandCursor)
    download_button.setProperty("filename", filename)
    # We'll connect this in the main class
    download_button.setProperty("filename", filename)
    item_layout.addWidget(download_button)

    return item_frame


# For testing the UI independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_window = QWidget()
    test_window.setWindowTitle("Export Results UI Test")
    test_window.resize(600, 600)

    test_layout = QVBoxLayout(test_window)
    test_layout.setContentsMargins(0, 0, 0, 0)

    # Create a test instance to receive the UI
    class TestWidget(QWidget):
        def __init__(self):
            super().__init__()
            # Add dummy handlers
            self.handle_export_request = lambda: print("Export requested")
            self.handle_download_recent = lambda filename: print(f"Download: {filename}")

    test_widget = TestWidget()
    setup_ui(test_widget)

    # Add setup widget to stacked widget
    test_widget.setup_view = create_export_setup_widget(test_widget)

    # Connect the export button manually
    test_widget.setup_view.export_button.clicked.connect(test_widget.handle_export_request)

    # Connect download buttons
    recent_items = test_widget.setup_view.findChildren(QFrame, "recentItemSetup")
    for item in recent_items:
        download_btn = item.findChild(QPushButton, "downloadBtnSetup")
        if download_btn:
            filename = download_btn.property("filename")
            download_btn.clicked.connect(lambda checked=False, fn=filename: test_widget.handle_download_recent(fn))

    test_widget.stacked_widget.addWidget(test_widget.setup_view)

    test_layout.addWidget(test_widget)
    test_window.show()

    sys.exit(app.exec_())
