import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                             QMainWindow, QScrollArea,
                             QSizePolicy, QStyle, QVBoxLayout, QWidget)

from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.MUPropertiesFun import MUPropertiesFunc
from app.muAnalysisFunctions.ResizeFunc import Resize
from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.AnalysisPlot import AnalysisPlot
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CollapsibleSection import \
    CollapsibleSection
from ui.muanalysis.AdvancedTools import AdvancedTools
from ui.muanalysis.FileSection import FileSection
from ui.muanalysis.ForceAnalysisSection import ForceAnalysisSection
from ui.muanalysis.MotorUnitProperties import MotorUnitPropertiesButton
from ui.muanalysis.PlotEMG import PlotEMGButton
from ui.muanalysis.RemoveMUSection import RemoveMUSection
from ui.muanalysis.ResultSelection import ResultSelection
from ui.muanalysis.ResultsPanel import ResultsPanel
from ui.muanalysis.ResultsTable import ResultsTable
from ui.muanalysis.SignalEditing import SignalEditing

from ui.components import CleanTheme as Theme
from ui.components import ActionButton


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
        # setting instance of function class from
        # src/app.muAnalysisFunctions.FileUploadFunc
        self.mu = FileUploadFunc()
        self.analysis_plot = AnalysisPlot()
        self.prop = MUPropertiesFunc()

        self.colors = {
            "bg_main": Theme.BG_MAIN,
            "bg_card": Theme.BG_CARD,
            "bg_sidebar": Theme.BG_CARD,
            "border_light": Theme.BORDER,
            "shadow": QColor(0, 0, 0, 25),
            "text_primary": Theme.TEXT_PRIMARY,
            "text_secondary": Theme.TEXT_SECONDARY,
            "text_title": Theme.TEXT_PRIMARY,
            "button_dark_bg": "#343a40",
            "button_dark_hover": "#495057",
            "button_grey_bg": "#e9ecee",
            "checkbox_bg": "#f1f3f5",
        }

        # --- Main Layout ---
        self.widget_layout = QVBoxLayout(self)
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(0)
        self.widget_layout.addWidget(
            self._create_top_bar())  # Top bar added first

        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(20)

        self.content_layout.addWidget(self._create_left_sidebar(), stretch=1)
        self.content_layout.addWidget(self._create_center_area(), stretch=5)
        self.content_layout.addWidget(self._create_right_sidebar(), stretch=3)
        self.widget_layout.addLayout(
            self.content_layout
        )  # Add main content below top bar

    # --- UI Creation Methods ---

    # heading for the page
    def _create_top_bar(self):
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(55)
        top_bar.setStyleSheet(
            f"""
            #topBar {{
                background-color: {Theme.BG_MAIN};
                border: none;
            }}
            """
        )
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(15, 0, 15, 0)
        top_bar_layout.setSpacing(10)

        # title
        title_label = QLabel("Motor Unit Analysis")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setStyleSheet(
            f"color: {self.colors['text_title']}; border: none;")

        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch(1)

        # load file button
        file_section = FileSection(None, self.mu, self.analysis_plot)
        self.load_file_button = file_section.load_btn
        self.load_file_button.setText("Press here to select file")
        top_bar_layout.addWidget(self.load_file_button)

        # save as button
        self.save_as_btn = ActionButton("Save as")
        self.save_as_btn.clicked.connect(lambda: self.handle_save_as())
        self.save_as_btn.setMinimumHeight(40)
        top_bar_layout.addWidget(self.save_as_btn)

        return top_bar

    def handle_save_as(self):
        if hasattr(self, "results_section"):
            self.results_section.save_results()
        else:
            print("Save as: ResultsPanel not found")

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

        # enables scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(10)

        # title
        title_div = QWidget()  # creating layout for the margin spacing
        title_div_layout = QVBoxLayout(title_div)
        # tells it to keep left, top, right margins
        title_div_layout.setContentsMargins(-1, -1, -1, 0)
        title_label = AnalysisText.create_major_title("Analysis")
        title_div_layout.addWidget(title_label)
        scroll_layout.addWidget(title_div)

        # signal editing + remove mu section
        mu_editing_widget = QWidget()
        mu_editing_layout = QVBoxLayout(mu_editing_widget)
        mu_editing_layout.setContentsMargins(0, 0, 0, 0)
        mu_editing_layout.setSpacing(5)
        remove_mu_section = RemoveMUSection(
            self.mu, self.analysis_plot, self.colors, parent=sidebar)
        signal_editing = SignalEditing(
            self.mu, self.analysis_plot, parent=sidebar)
        mu_editing_layout.addWidget(remove_mu_section)
        mu_editing_layout.addWidget(signal_editing)
        mu_editing_section = CollapsibleSection(
            "MU Editing", mu_editing_widget, expanded=False)
        scroll_layout.addWidget(mu_editing_section)

        # force anaylsis
        force_analysis = ForceAnalysisSection(sidebar, self.analysis_plot)
        force_analysis_section = CollapsibleSection(
            "Force Analysis", force_analysis, expanded=False)
        scroll_layout.addWidget(force_analysis_section)

        # motor unit properties
        motor_unit_properties = MotorUnitPropertiesButton(
            self.analysis_plot, parent=self)
        motor_unit_properties.mvc_updated.connect(self.prop.set_mvc)
        mu_properties_section = CollapsibleSection(
            "Motor Unit Properties", motor_unit_properties, expanded=False)
        scroll_layout.addWidget(mu_properties_section)
        self.motor_unit_properties = motor_unit_properties

        # plot emg button
        plot_emg_tools = PlotEMGButton(self.analysis_plot, parent=self)
        plot_emg_section = CollapsibleSection(
            "Plot EMG", plot_emg_tools, expanded=False)
        scroll_layout.addWidget(plot_emg_section)
        self.plot_emg_tools = plot_emg_tools

        # advanced tools
        advanced_tools = AdvancedTools(parent=sidebar)
        scroll_layout.addWidget(advanced_tools)
        scroll_layout.addStretch(1)
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)

        # width of left sidebar
        sidebar.setFixedWidth(300)
        scroll.setMinimumWidth(280)
        scroll_content.setMinimumWidth(260)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)

        return sidebar

    # center area where graph is initally loaded
    # starts with a message widget stating file needs to be loaded
    # this prop is passed to mu class as it needs the reference to remove it
    def _create_center_area(self):
        center = QFrame()
        center.setObjectName("centerContent")
        center_layout = QVBoxLayout(center)
        center_layout.addWidget(self.analysis_plot)
        return center

    # side bar with load file button
    # loaded from FileSection class
    def _create_right_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        sidebar.setStyleSheet(
            f"""
            #rightSidebar {{
                background-color: {self.colors['bg_sidebar']};
            }}

        """
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)

        file_section = FileSection(None, self.mu, self.analysis_plot)
        file_section.load_btn.setParent(None)

        title_label = file_section.findChild(QLabel, "sidebarTitle")
        if title_label is None:
            title_label = AnalysisText.create_major_title("File")
            title_label.setObjectName("sidebarTitle")

        if hasattr(file_section.reset_btn, "reset_requested"):
            file_section.reset_btn.reset_requested.connect(
                lambda: self.mu.handle_reset_workflow(self.analysis_plot)
            )

        file_section.reset_btn.setFixedWidth(250)
        file_section.reset_btn.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed)

        file_container = QWidget()
        file_layout = QVBoxLayout(file_container)
        file_layout.setContentsMargins(0, 15, 0, 0)
        file_layout.setSpacing(8)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(15, 0, 0, 0)
        title_layout.addWidget(title_label)
        file_layout.addLayout(title_layout)

        file_layout.addSpacing(10)

        reset_row = QHBoxLayout()
        reset_row.addStretch(1)
        reset_row.addWidget(file_section.reset_btn)
        reset_row.addStretch(1)

        file_layout.addLayout(reset_row)
        sidebar_layout.addWidget(file_container)

        # resize button
        resize_file = Resize(self.mu, self.analysis_plot)
        resize_btn = ActionButton(
            "Resize")
        resize_btn.clicked.connect(lambda: resize_file.resize())
        resize_btn.setMinimumHeight(40)
        resize_btn.setFixedWidth(250)
        self.analysis_plot.set_resize(resize_btn)
        resize_btn_row = QHBoxLayout()
        resize_btn_row.addStretch(1)
        resize_btn_row.addWidget(resize_btn)
        resize_btn_row.addStretch(1)
        sidebar_layout.addLayout(resize_btn_row)

        results_section = ResultsPanel(
            sidebar, self.result_combo, self.results_table)
        self.results_section = results_section

        sidebar_layout.addWidget(results_section, stretch=15)
        sidebar_layout.addStretch(1)
        sidebar.setMaximumWidth(300)
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
    # Do not set a custom export window opener so that the default fallback
    # runs.
    test_window.show()
    sys.exit(app.exec_())
