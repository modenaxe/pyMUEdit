# export_results.py

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
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize
import traceback  # Import for detailed error printing

def get_icon(standard_icon):
    """Gets a standard Qt icon."""
    app = QApplication.instance()
    if app:
        return app.style().standardIcon(standard_icon)
    else:
        print("Warning: QApplication instance not found for get_icon.")
        return QIcon()

class ExportResultsWindow(QWidget):
    """
    A QWidget window for configuring and viewing data exports.
    Provides options for file format selection and lists recent exports.
    """
    def __init__(self, parent=None):
        print("--- ExportResultsWindow __init__ (Restored Full UI) START ---")
        try:
            super().__init__(parent)
            self.setWindowTitle("Export Results")
            self.setMinimumWidth(600)  # Set a minimum width

            # Define color scheme
            self.colors = {
                "bg_main": "#f8f9fa",
                "bg_card": "#ffffff",
                "border": "#e0e0e0",
                "text_primary": "#212529",
                "text_secondary": "#6c757d",
                "button_dark_bg": "#212529",
                "button_dark_text": "#ffffff",
                "button_dark_hover": "#343a40",
                "icon_box_bg": "#e9ecef",
                "icon_box_border": "#ced4da",
                "icon_box_text": "#495057",
                "item_row_bg": "#f8f9fa",
                "item_row_hover": "#f1f3f5",
                "download_btn_hover": "#dee2e6",
                "download_btn_pressed": "#ced4da",
                "selected_data_bg": "#fdfdfd",
                "selected_data_border": "#eeeeee",
            }
            self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

            # Main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(30, 30, 30, 30)
            main_layout.setSpacing(25)

            # --- Header ---
            header_layout = QVBoxLayout()
            header_layout.setSpacing(5)
            title_label = QLabel("Export Results")
            title_label.setFont(QFont("Arial", 20, QFont.Bold))
            title_label.setStyleSheet(f"color: {self.colors['text_primary']}; border: none;")
            subtitle_label = QLabel("Export your motor unit firing patterns data")
            subtitle_label.setFont(QFont("Arial", 10))
            subtitle_label.setStyleSheet(f"color: {self.colors['text_secondary']}; border: none;")
            header_layout.addWidget(title_label)
            header_layout.addWidget(subtitle_label)
            main_layout.addLayout(header_layout)

            # --- Export Configuration Section ---
            export_config_widget = self._create_export_config_section()
            main_layout.addWidget(export_config_widget)

            # --- Recent Exports Section ---
            recent_exports_widget = self._create_recent_exports_section()
            main_layout.addWidget(recent_exports_widget)

            # --- Footer ---
            footer_label = QLabel("Last export: January 15, 2025 at 14:30")
            footer_label.setAlignment(Qt.AlignCenter)
            footer_label.setFont(QFont("Arial", 9))
            footer_label.setStyleSheet(f"color: {self.colors['text_secondary']}; margin-top: 10px; border: none;")
            main_layout.addWidget(footer_label)
            main_layout.addStretch(1)

        except Exception as e:
            print(f"!!!!! ERROR during ExportResultsWindow __init__: {e}")
            traceback.print_exc()
        print("--- ExportResultsWindow __init__ (Restored Full UI) END ---")

    def _create_styled_card(self):
        """Creates a basic styled QFrame card."""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("cardFrame")
        card.setStyleSheet(f"""
            #cardFrame {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
            }}
            #cardFrame > QWidget, #cardFrame > QLayout::item {{
                background-color: transparent;
                border: none;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        return card, card_layout

    def _create_export_config_section(self):
        """Creates the top section for export configuration."""
        config_card, config_layout = self._create_styled_card()
        format_label = QLabel("Select File Format")
        format_label.setFont(QFont("Arial", 10))
        format_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")
        config_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.setFont(QFont("Arial", 10))
        self.format_combo.addItem("Select format...")
        self.format_combo.addItem(".csv (Comma Separated Values)")
        self.format_combo.addItem(".mat (MATLAB Data File)")
        self.format_combo.addItem(".xlsx (Excel Spreadsheet)")
        self.format_combo.setMinimumHeight(35)
        self.format_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 5px 10px;
                background-color: {self.colors['bg_card']};
                color: {self.colors['text_primary']};
                min-height: 25px;
            }}
            QComboBox:focus {{
                border: 1px solid {self.colors['button_dark_bg']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {self.colors['border']};
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: transparent;
            }}
            QComboBox::down-arrow {{
                image: url(:/qt-project.org/styles/commonstyle/images/down_arrow-16.png);
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['bg_card']};
                selection-background-color: {self.colors['button_dark_hover']};
                selection-color: {self.colors['button_dark_text']};
                color: {self.colors['text_primary']};
                padding: 2px;
            }}
        """)
        config_layout.addWidget(self.format_combo)
        config_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))
        selected_data_frame = QFrame()
        selected_data_frame.setObjectName("selectedDataFrame")
        selected_data_frame.setStyleSheet(f"""
            #selectedDataFrame {{
                background-color: {self.colors['selected_data_bg']};
                border: 1px solid {self.colors['selected_data_border']};
                border-radius: 5px;
                padding: 15px;
            }}
            #selectedDataFrame > QLabel, #selectedDataFrame > QLayout::item {{
                background-color: transparent;
                border: none;
            }}
        """)
        selected_data_layout = QVBoxLayout(selected_data_frame)
        selected_data_layout.setContentsMargins(10, 10, 10, 10)
        selected_data_layout.setSpacing(10)
        data_title_label = QLabel("Selected Data")
        data_title_label.setFont(QFont("Arial", 10, QFont.Bold))
        data_title_label.setStyleSheet(f"color: {self.colors['text_primary']}; margin-bottom: 5px; background: transparent; border: none;")
        selected_data_layout.addWidget(data_title_label)
        selected_data_layout.addLayout(self._create_data_detail_row(QStyle.SP_FileIcon, "Motor Unit Firing Patterns"))
        selected_data_layout.addLayout(self._create_data_detail_row(QStyle.SP_MediaSeekForward, "Recording Duration: 120s"))
        selected_data_layout.addLayout(self._create_data_detail_row(QStyle.SP_ComputerIcon, "Units Detected: 12"))
        config_layout.addWidget(selected_data_frame)
        config_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))
        export_button = QPushButton("Export Data")
        export_button.setFont(QFont("Arial", 10, QFont.Bold))
        export_button.setIcon(get_icon(QStyle.SP_DialogSaveButton))
        export_button.setIconSize(QSize(16, 16))
        export_button.setMinimumHeight(40)
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['button_dark_bg']};
                color: {self.colors['button_dark_text']};
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_dark_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['button_dark_bg']};
            }}
        """)
        export_button.clicked.connect(self.handle_export)
        config_layout.addWidget(export_button)
        return config_card

    def _create_data_detail_row(self, icon_enum, text):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        row_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel()
        icon_pixmap = get_icon(icon_enum).pixmap(QSize(16, 16))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(16, 16))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("margin-top: 2px; background: transparent; border: none;")
        text_label = QLabel(text)
        text_label.setFont(QFont("Arial", 10))
        text_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")
        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_label)
        row_layout.addStretch(1)
        return row_layout

    def _create_recent_exports_section(self):
        recent_card, recent_layout = self._create_styled_card()
        title_label = QLabel("Recent Exports")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_primary']}; margin-bottom: 10px; background: transparent; border: none;")
        recent_layout.addWidget(title_label)
        recent_layout.addWidget(self._create_recent_export_item("csv", "firing_patterns_2025.01.15.csv", "2.4 MB • Completed"))
        recent_layout.addWidget(self._create_recent_export_item("mat", "firing_patterns_2025.01.14.mat", "3.1 MB • Completed"))
        recent_layout.addStretch(1)
        return recent_card

    def _create_recent_export_item(self, icon_type, filename, metadata):
        item_widget = QFrame()
        item_widget.setObjectName("recentItem")
        item_widget.setCursor(Qt.PointingHandCursor)
        item_widget.setStyleSheet(f"""
            #recentItem {{
                background-color: {self.colors['item_row_bg']};
                border: 1px solid {self.colors['item_row_bg']};
                border-radius: 4px;
                padding: 10px 15px;
            }}
            #recentItem:hover {{
                background-color: {self.colors['item_row_hover']};
                border: 1px solid {self.colors['border']};
            }}
            #recentItem > QLabel, #recentItem > QLayoutWidget {{
                background-color: transparent;
                border: none;
            }}
        """)
        item_widget.setToolTip(f"Click to interact with {filename}")
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(12)
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Arial", 7, QFont.Bold))
        icon_label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {self.colors['icon_box_border']};
                border-radius: 4px;
                background-color: {self.colors['icon_box_bg']};
                color: {self.colors['icon_box_text']};
            }}
        """)
        if icon_type.lower() == "csv":
            icon_label.setText("CSV")
        elif icon_type.lower() == "mat":
            icon_label.setText("MAT")
        elif icon_type.lower() == "xlsx":
            icon_label.setText("XLSX")
        else:
            icon_label.setPixmap(get_icon(QStyle.SP_FileIcon).pixmap(QSize(18, 18)))
            icon_label.setText("")
            icon_label.setStyleSheet("border: none; background: transparent;")
        item_layout.addWidget(icon_label)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        filename_label = QLabel(filename)
        filename_label.setFont(QFont("Arial", 10))
        filename_label.setStyleSheet(f"color: {self.colors['text_primary']}; background: transparent; border: none;")
        filename_label.setToolTip(filename)
        metadata_label = QLabel(metadata)
        metadata_label.setFont(QFont("Arial", 9))
        metadata_label.setStyleSheet(f"color: {self.colors['text_secondary']}; background: transparent; border: none;")
        info_layout.addWidget(filename_label)
        info_layout.addWidget(metadata_label)
        item_layout.addWidget(info_widget)
        item_layout.addStretch(1)
        download_button = QPushButton()
        download_button.setIcon(get_icon(QStyle.SP_ArrowDown))
        download_button.setIconSize(QSize(18, 18))
        download_button.setFixedSize(32, 32)
        download_button.setCursor(Qt.PointingHandCursor)
        download_button.setToolTip(f"Download {filename}")
        download_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['download_btn_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['download_btn_pressed']};
            }}
        """)
        download_button.clicked.connect(lambda checked=False, fn=filename: self.handle_download(fn))
        item_layout.addWidget(download_button)
        return item_widget

    def handle_export(self):
        print("--- handle_export called ---")
        selected_index = self.format_combo.currentIndex()
        selected_format_text = self.format_combo.currentText()
        if selected_index == 0:
            print("Please select a file format.")
            return
        print(f"Exporting data in format: {selected_format_text}")
        print("Export process initiated (placeholder).")

    def handle_download(self, filename):
        print(f"--- handle_download called for {filename} ---")
        print(f"Downloading file: {filename}")
        print(f"Download requested for {filename} (placeholder).")

# --- Main execution block (for testing the window independently) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("Running export_results.py directly...")
    export_window = ExportResultsWindow()
    export_window.show()
    print("Called show() on export_results window.")
    sys.exit(app.exec_())
