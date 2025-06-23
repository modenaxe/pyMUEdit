import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFrame,
    QCheckBox,
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QStyle,
    QGraphicsDropShadowEffect,
    QScrollArea,
    QMainWindow,
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal
import traceback
from app.MUAnalysisFunc import MUAnalysisFunc
from app.ExportResults import ExportResultsWindow


def get_icon(standard_icon):
    """Helper function to get standard icons safely."""
    return QApplication.style().standardIcon(getattr(QStyle, standard_icon))  # type:ignore


class MUAnalysis(QWidget):
    return_to_dashboard_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mu = MUAnalysisFunc()

        self.colors = {
            "bg_main": "#f8f9fa",
            "bg_card": "#ffffff",
            "bg_sidebar": "#f8f9fa",
            "bg_topbar": "#ffffff",
            "border_light": "#e9ecef",
            "border_medium": "#dee2e6",
            "shadow": QColor(0, 0, 0, 25),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_title": "#343a40",
            "placeholder_bg": "#e9ecef",
            "button_dark_bg": "#343a40",
            "button_dark_text": "#ffffff",
            "button_dark_hover": "#495057",
            "button_grey_bg": "#e9ecee",
            "button_grey_text": "#495057",
            "button_grey_border": "#ced4da",
            "button_grey_hover": "#dee2e6",
            "checkbox_bg": "#f1f3f5",
        }

        # --- Main Layout ---
        self.widget_layout = QVBoxLayout(self)
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(0)
        self.widget_layout.addWidget(self._create_top_bar())  # Top bar added first

        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(20)
        self.content_layout.addWidget(self._create_left_sidebar(), stretch=1)
        self.content_layout.addWidget(self._create_center_area(), stretch=5)
        self.content_layout.addWidget(self._create_right_sidebar(), stretch=2)
        self.widget_layout.addLayout(self.content_layout)  # Add main content below top bar

    def request_return_to_dashboard(self):
        """Emits a signal to tell the main window to switch views."""
        print("Widget: Requesting return to dashboard")
        self.return_to_dashboard_requested.emit()

    # --- UI Creation Methods ---

    def _create_top_bar(self):
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(55)
        top_bar.setStyleSheet(
            f"""
            #topBar {{
                background-color: {self.colors['bg_topbar']};
                border-bottom: 1px solid {self.colors['border_light']};
            }}
            #topBar > QPushButton {{
                background-color: transparent;
                border: none;
                color: {self.colors['text_secondary']};
                font-size: 9pt;
                padding: 5px 10px;
            }}
            #topBar > QPushButton:hover {{
                color: {self.colors['text_primary']};
            }}
        """
        )
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(15, 0, 15, 0)
        top_bar_layout.setSpacing(10)
        icon_label = QLabel()
        icon_pixmap = get_icon("SP_ComputerIcon").pixmap(QSize(24, 24))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(28, 28))
        title_label = QLabel("Motor Unit Analysis")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_title']}; border: none;")
        top_bar_layout.addWidget(icon_label)
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch(1)
        dashboard_btn = QPushButton("Dashboard")
        projects_btn = QPushButton("Projects")
        settings_btn = QPushButton("Settings")
        user_button = QPushButton()
        user_button.setIcon(get_icon("SP_DialogOkButton"))
        user_button.setIconSize(QSize(18, 18))
        user_button.setFixedSize(30, 30)
        user_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['button_dark_bg']};
                border-radius: 15px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_dark_hover']};
            }}
        """
        )
        top_bar_layout.addWidget(dashboard_btn)
        top_bar_layout.addWidget(projects_btn)
        top_bar_layout.addWidget(settings_btn)
        top_bar_layout.addWidget(user_button)
        if hasattr(self, "request_return_to_dashboard"):
            dashboard_btn.clicked.connect(self.request_return_to_dashboard)
        else:
            print("ERROR: request_return_to_dashboard method missing!")
        return top_bar

    def _create_left_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("leftSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)
        sidebar.setStyleSheet(
            f"""
            #leftSidebar QLabel {{
                color: {self.colors['text_primary']};
                font-size: 10pt;
                font-weight: bold;
                border: none;
            }}
            #leftSidebar QCheckBox {{
                background-color: {self.colors['checkbox_bg']};
                color: {self.colors['text_primary']};
                padding: 8px 12px;
                border-radius: 4px;
                border: 1px solid {self.colors['border_light']};
                font-size: 9pt;
            }}
            #leftSidebar QCheckBox::indicator {{
                width: 13px;
                height: 13px;
            }}
            #leftSidebar QCheckBox:hover {{
                background-color: {self.colors['border_light']};
            }}
        """
        )
        return sidebar

    def _create_center_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        scroll_area.setWidget(scroll_content)
        return scroll_area

    def _create_plot_panel(self, title, placeholder_text):
        panel = QFrame()
        panel.setObjectName("plotCard")
        panel.setStyleSheet(
            f"""
            #plotCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border_light']};
                border-radius: 6px;
            }}
            #plotCard > QLabel {{
                color: {self.colors['text_primary']};
                font-size: 10pt;
                font-weight: bold;
                padding: 10px 15px 5px 15px;
                border: none;
                background: transparent;
            }}
        """
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        title_label = QLabel(title)
        panel_layout.addWidget(title_label)
        placeholder = QFrame()
        placeholder.setObjectName("graphPlaceholder")
        placeholder.setMinimumHeight(180)
        placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        placeholder.setStyleSheet(
            f"""
            #graphPlaceholder {{
                background-color: {self.colors['placeholder_bg']};
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                margin: 0px 15px 15px 15px;
            }}
        """
        )
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel(placeholder_text)
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 10pt; background: transparent;"
        )
        placeholder_layout.addWidget(placeholder_label)
        panel_layout.addWidget(placeholder, stretch=1)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(self.colors["shadow"])
        shadow.setOffset(0, 2)
        panel.setGraphicsEffect(shadow)
        return panel

    def _create_right_sidebar(self):
        print("--- DEBUG: _create_right_sidebar called ---")
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(15)
        sidebar.setStyleSheet(
            f"""
            #rightSidebar > QLabel#sidebarTitle {{
                color: {self.colors['text_primary']};
                font-size: 10pt;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
            QFrame#summaryItem {{
                background-color: {self.colors['checkbox_bg']};
                border-radius: 4px;
                border: 1px solid {self.colors['border_light']};
                padding: 8px 10px;
            }}
            QLabel#summaryLabel {{
                color: {self.colors['text_secondary']};
                font-size: 8pt;
                border: none;
                background: transparent;
            }}
            QLabel#summaryValue {{
                color: {self.colors['text_primary']};
                font-size: 10pt;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
        """
        )
        title_label = QLabel("File Details")
        title_label.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(title_label)

        sidebar_layout.addStretch(1)
        browse_btn = QPushButton("Load File")
        browse_btn.setMinimumHeight(36)
        browse_btn.setFont(QFont("Arial", 9, QFont.Bold))
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['button_dark_bg']};
                color: {self.colors['button_dark_text']};
                border: none;
                border-radius: 4px;
                padding: 8px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_dark_hover']};
            }}
        """
        )
        browse_btn.clicked.connect(self.mu.select_file_button_pushed)
        sidebar_layout.addWidget(browse_btn)
        # --- Create Export Button ---

        return sidebar

# --- Main execution block (for testing) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    analysis_widget = MUAnalysis()
    test_window = QMainWindow()
    test_window.setCentralWidget(analysis_widget)
    test_window.setWindowTitle("Motor Unit Analysis Widget Test")
    test_window.setGeometry(100, 100, 1200, 800)
    # Do not set a custom export window opener so that the default fallback runs.
    test_window.show()
    sys.exit(app.exec_())
