import sys
import time
import random
import pandas as pd
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
from core.muAnalysisCore.AnalysisResultsHist import store
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.MUPropertiesFun import MUPropertiesFunc
from app.muAnalysisFunctions.ResizeFunc import Resize
from app.ExportResults import ExportResultsWindow
from ui.muanalysis.AdvancedTools import AdvancedTools
from ui.muanalysis.MotorUnitProperties import MotorUnitPropertiesButton
from ui.muanalysis.PlotEMG import PlotEMGButton
from ui.muanalysis.SignalEditing import SignalEditing
from ui.components.muAnalysisComponents.AnalysisPlot import AnalysisPlot
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.MajorHeading import MajorHeading
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.muanalysis.FileSection import FileSection
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.muanalysis.SortMUs import SortMUs
from ui.muanalysis.RemoveMUSection import RemoveMUSection

from ui.muanalysis.ResultsPanel import ResultsPanel

from core.muAnalysisCore.AnalysisResultsHist import store
from core.muAnalysisCore.ResultsTable import ResultsTable
from ui.components.muAnalysisComponents.ResultSelection import ResultSelection


# legacy code
def get_icon(standard_icon):
    """Helper function to get standard icons safely."""
    return QApplication.style().standardIcon(
        getattr(QStyle, standard_icon)
    )  # type:ignore


class MUAnalysis(QWidget):
    return_to_dashboard_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.data = store
        self.results_table = ResultsTable()
        self.result_combo = ResultSelection(self.results_table)
        # setting instance of function class from src/app.muAnalysisFunctions.FileUploadFunc
        self.mu = FileUploadFunc()
        self.analysis_plot = AnalysisPlot()
        self.prop = MUPropertiesFunc()
        print(self.analysis_plot)

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

        self.content_layout.addWidget(self._create_left_sidebar(), stretch=1)
        self.content_layout.addWidget(self._create_center_area(), stretch=5)
        self.content_layout.addWidget(self._create_right_sidebar(), stretch=3)
        self.widget_layout.addLayout(
            self.content_layout
        )  # Add main content below top bar

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
                background-color: {self.colors['bg_sidebar']};
            }}

        """
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 5, 10, 5)
        sidebar_layout.setSpacing(0)

        # title
        title_label = MajorHeading("Analysis")
        sidebar_layout.addWidget(title_label)
    
        # signal editing 
        # remove mu section
        remove_mu_section = RemoveMUSection(
            self.mu, self.analysis_plot, self.colors, parent=sidebar
        )
        sidebar_layout.addWidget(remove_mu_section)
        # sort MUs
        sort_MUs = SortMUs(self.mu, self.analysis_plot, parent=sidebar)
        sidebar_layout.addWidget(sort_MUs)

        # signal editing
        signal_editing = SignalEditing(self.mu, self.analysis_plot, parent=sidebar)
        sidebar_layout.addWidget(signal_editing)

        # motor unit properties
        motor_unit_properties = MotorUnitPropertiesButton(
            self.analysis_plot, parent=self
        )
        motor_unit_properties.mvc_updated.connect(self.prop.set_mvc)
        sidebar_layout.addWidget(motor_unit_properties)
        self.motor_unit_properties = motor_unit_properties

        # plot emg button
        plot_emg_tools = PlotEMGButton(self.analysis_plot, parent=self)
        sidebar_layout.addWidget(plot_emg_tools)
        self.plot_emg_tools = plot_emg_tools

        # advanced tools
        advanced_tools = AdvancedTools(parent=sidebar)
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

        # # code to test the result table
        # # can be refered to when implimenting real data
        # dummy_button = QPushButton("Dummy")
        # dummy_button.setStyleSheet(
        #     f"""
        #     QPushButton {{
        #         background-color: {self.colors['button_grey_bg']};
        #         border-radius: 15px;
        #         padding: 0px;
        #         height: 40%;

        #     }}
        #     QPushButton:hover {{
        #         background-color: {self.colors['button_dark_hover']};
        #     }}
        # """
        # )

        # # result need to be an list of dictionaries with consistent keys
        # # refer to the code below to append the results
        # table = {
        #     "col": 42,
        #     "timestamp": time.time()
        # }
        # title = "table "
        # dummy_button.clicked.connect(lambda: self.calc_result(title, [table]))
        # center_layout.addWidget(dummy_button)

        resize_file = Resize(self.mu, self.analysis_plot)
        resize_btn = GeneralButton("Resize", lambda: resize_file.resize(resize_btn))
        center_layout.addWidget(resize_btn)
        self.analysis_plot.set_reseize(resize_btn)
        center_layout.addWidget(self.analysis_plot)

        return center

    # side bar with load file button
    # loaded from FileSection class
    def _create_right_sidebar(self):
        print("--- DEBUG: _create_right_sidebar called ---")
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        sidebar.setStyleSheet(
            f"""
            #rightSidebar {{
                background-color: {self.colors['bg_sidebar']};
            }}

        """
        )
        file_section = FileSection(sidebar, self.mu, self.analysis_plot)
        # Connect the reset button's signal to the MUAnalysisFunc method
        file_section.reset_btn.reset_requested.connect(
            lambda: self.mu.handle_reset_workflow(self.analysis_plot)
        )
        results_section = ResultsPanel(sidebar, self.result_combo, self.results_table)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(file_section, stretch=1)
        sidebar_layout.addWidget(results_section, stretch=4)
        return sidebar

    def calc_result(self, title="title", data=[{}]):
        self.data.append_analysis_hist(title, data)


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
