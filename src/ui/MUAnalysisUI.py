import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QStyle,
    QMainWindow,
    QComboBox,
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from app.MUAnalysisFunc import MUAnalysisFunc
from app.ExportResults import ExportResultsWindow
from ui.muanalysis.AdvancedTools import AdvancedTools

# legacy code
def get_icon(standard_icon):
    """Helper function to get standard icons safely."""
    return QApplication.style().standardIcon(getattr(QStyle, standard_icon))  # type:ignore


class MUAnalysis(QWidget):
    return_to_dashboard_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # setting instance of function class from src/app/MUAnalysisFunc
        self.mu = MUAnalysisFunc()

        self.colors = {
            "bg_main": "#f8f9fa",
            "bg_card": "#ffffff",
            "bg_sidebar": "#f8f9fa",
            "bg_topbar": "#ffffff",
            "border_light": "#e9ecef",
            "shadow": QColor(0, 0, 0, 25),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_title": "#343a40",
            "button_dark_bg": "#343a40",
            "button_dark_hover": "#495057",
            "button_grey_bg": "#e9ecee",
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
        self.center = None
        self.content_layout.addWidget(self._create_left_sidebar(), stretch=1)
        self.content_layout.addWidget(self._create_center_area(), stretch=5)
        self.content_layout.addWidget(self._create_right_sidebar(), stretch=2)
        self.widget_layout.addLayout(self.content_layout)  # Add main content below top bar

    # legacy code
    def request_return_to_dashboard(self):
        """Emits a signal to tell the main window to switch views."""
        print("Widget: Requesting return to dashboard")
        self.return_to_dashboard_requested.emit()

    # --- UI Creation Methods ---

    # legacy code
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

    # dropdown order for matrix code
    # the border on the right sidebar 
    # the dropdown names 
    # global styling
    def _create_left_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("leftSidebar")
        sidebar.setStyleSheet(
            f"""
            #leftSidebar {{
                background-color: {self.colors['button_dark_bg']};
            }}
        """
        )
        sidebar_layout = QVBoxLayout(sidebar)

        # title
        title_label = QLabel("Analysis")
        title_label.setObjectName("analysisTitle")
        title_label.setStyleSheet(f"color: {self.colors['button_grey_bg']}")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        sidebar_layout.addWidget(title_label)

        # advanced tools
        advanced_tools = AdvancedTools(parent=self)
        sidebar_layout.addWidget(advanced_tools)

        sidebar_layout.addStretch(1)
        return sidebar

    # center area where graph is initally loaded
    # starts with a message widget stating file needs to be loaded
    # this prop is passed to mu class as it needs the reference to remove it
    def _create_center_area(self):
        center = QFrame()
        center.setObjectName("centerContent")
        center_layout = QVBoxLayout(center)
        load = QLabel("Press Load File to View Data")
        load.setFont(QFont("Arial", 32, QFont.Bold))
        load.setStyleSheet(f"color: red; margin-right: 100%;")
        center_layout.addWidget(load)
        self.mu.set_canvas(load)
        self.center = center_layout
        return center

    # side bar with load file button
    # has style sheet of button: feel free to change
    # when button is clicked it calls mu class method, passing instance of the center layout as it needs
    # the reference to make changes to it (see line 203)
    def _create_right_sidebar(self):
        print("--- DEBUG: _create_right_sidebar called ---")
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        sidebar.setStyleSheet(
            f"""
            #rightSidebar {{
                background-color: {self.colors['button_dark_bg']};
            }}

        """
        )
        sidebar_layout = QVBoxLayout(sidebar)
        title_label = QLabel("File")
        title_label.setStyleSheet(f"color: {self.colors['button_grey_bg']}; border: none")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(title_label)
        browse_btn = QPushButton("Load File")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['button_dark_hover']};
                color: {self.colors['button_grey_bg']};
                border: none;
                height: 40%;
                max-width: 100%;
                border-radius: 4px;
                margin-right: 50%;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_grey_bg']};
                color: {self.colors['button_dark_hover']};
            }}
        """
        )
        browse_btn.clicked.connect(lambda: self.mu.select_file_button_pushed(self.center))
        sidebar_layout.addWidget(browse_btn)
        sidebar_layout.addStretch(1)
        return sidebar

# --- Main execution block (for testing) ---
# legacy code
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
