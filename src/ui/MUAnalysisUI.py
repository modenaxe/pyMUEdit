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

from app.ExportResults import ExportResultsWindow


def get_icon(standard_icon):
    """Helper function to get standard icons safely."""
    return QApplication.style().standardIcon(getattr(QStyle, standard_icon))  # type:ignore


class MUAnalysis(QWidget):
    return_to_dashboard_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Variable to store the custom opener function (if any)
        self._open_export_window_func = None

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

    def _trigger_export_window_open(self):
        """Opens the export results window.
        If a custom opener function is set, it calls that.
        Otherwise, it creates an instance of ExportResultsWindow and shows it.
        """
        print(">>> Widget: Reached _trigger_export_window_open <<<")
        if self._open_export_window_func:
            print(">>> Calling stored opener function...")
            try:
                self._open_export_window_func()
                print(">>> Called stored opener function successfully.")
            except Exception as e:
                print(f"!!!!! ERROR calling stored opener function: {e}")
                traceback.print_exc()
        else:
            print(">>> No custom export window opener function set. Using default implementation.")
            if ExportResultsWindow:
                self.export_window = ExportResultsWindow()  # Store in instance attribute to keep it alive
                self.export_window.show()
                print(">>> ExportResultsWindow shown successfully.")
            else:
                print("!!!!! ERROR: ExportResultsWindow class not available.")

    def set_export_window_opener(self, opener_func):
        """Stores the custom function used to open the export window."""
        print(f"DEBUG: Setting export window opener function: {opener_func}")
        self._open_export_window_func = opener_func

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
        title_label = QLabel("Motor Units")
        sidebar_layout.addWidget(title_label)
        self.unit_checkboxes = []
        for i in range(1, 4):
            checkbox = QCheckBox(f"Motor Unit #{i}")
            sidebar_layout.addWidget(checkbox)
            self.unit_checkboxes.append(checkbox)
            checkbox.stateChanged.connect(self.handle_unit_selection_change)
        sidebar_layout.addSpacerItem(QSpacerItem(10, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))
        compare_button = QPushButton("Compare Selected Units")
        compare_button.setFont(QFont("Arial", 9))
        compare_button.setMinimumHeight(32)
        compare_button.setCursor(Qt.CursorShape.PointingHandCursor)
        compare_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['button_grey_bg']};
                color: {self.colors['button_grey_text']};
                border: 1px solid {self.colors['button_grey_border']};
                border-radius: 4px;
                padding: 8px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_grey_hover']};
            }}
        """
        )
        compare_button.clicked.connect(self.handle_compare_units)
        sidebar_layout.addWidget(compare_button)
        sidebar_layout.addStretch(1)
        return sidebar

    def _create_center_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(20)
        grid_layout.addWidget(self._create_plot_panel("Firing Rates", "Firing Rates Graph"), 0, 0)
        grid_layout.addWidget(self._create_plot_panel("Inter-spike Intervals", "Intervals Graph"), 0, 1)
        grid_layout.addWidget(self._create_plot_panel("Correlation Plot", "Correlation Plot"), 1, 0)
        grid_layout.addWidget(self._create_property_comparison_panel(), 1, 1, 2, 1)
        grid_layout.addWidget(self._create_plot_panel("Motor Unit Distribution", "Interactive\nHistogram Plot"), 2, 0)
        grid_layout.addWidget(self._create_time_series_panel(), 3, 0, 1, 2)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
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

    def _create_property_comparison_panel(self):
        panel = QFrame()
        panel.setObjectName("plotCard")
        panel.setStyleSheet(
            f"""
            #plotCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border_light']};
                border-radius: 6px;
            }}
            #plotCard > QLabel#plotTitle {{
                color: {self.colors['text_primary']};
                font-size: 10pt;
                font-weight: bold;
                padding: 10px 15px 5px 15px;
                border: none;
                background: transparent;
            }}
            QComboBox {{
                border: 1px solid {self.colors['border_medium']};
                border-radius: 4px;
                padding: 5px 8px;
                background-color: {self.colors['bg_card']};
                color: {self.colors['text_primary']};
                font-size: 9pt;
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid {self.colors['border_medium']};
            }}
            QComboBox::down-arrow {{
                image: url(:/qt-project.org/styles/commonstyle/images/down_arrow-16.png);
                width: 10px;
                height: 10px;
            }}
        """
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        title_label = QLabel("Property Comparison")
        title_label.setObjectName("plotTitle")
        panel_layout.addWidget(title_label)
        placeholder = QFrame()
        placeholder.setObjectName("graphPlaceholder")
        placeholder.setMinimumHeight(250)
        placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        placeholder.setStyleSheet(
            f"""
            #graphPlaceholder {{
                background-color: {self.colors['placeholder_bg']};
                margin: 0px 15px 10px 15px;
            }}
        """
        )
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel("Scatter Plot")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 10pt; background: transparent;"
        )
        placeholder_layout.addWidget(placeholder_label)
        panel_layout.addWidget(placeholder, stretch=1)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(15, 0, 15, 10)
        control_layout.setSpacing(10)
        combo_x = QComboBox()
        combo_x.addItems(["X-Axis Property", "Firing Rate", "Amplitude", "Duration"])
        combo_y = QComboBox()
        combo_y.addItems(["Y-Axis Property", "Firing Rate", "Amplitude", "Duration"])
        control_layout.addWidget(combo_x)
        control_layout.addWidget(combo_y)
        control_layout.addStretch(1)
        panel_layout.addLayout(control_layout)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(self.colors["shadow"])
        shadow.setOffset(0, 2)
        panel.setGraphicsEffect(shadow)
        return panel

    def _create_time_series_panel(self):
        panel = QFrame()
        panel.setObjectName("plotCard")
        panel.setStyleSheet(
            f"""
            #plotCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border_light']};
                border-radius: 6px;
            }}
            #plotCard > QLabel#plotTitle {{
                color: {self.colors['text_primary']};
                font-size: 10pt;
                font-weight: bold;
                padding: 10px 15px 5px 15px;
                border: none;
                background: transparent;
            }}
            QPushButton#controlButton {{
                background-color: {self.colors['button_grey_bg']};
                color: {self.colors['button_grey_text']};
                border: 1px solid {self.colors['button_grey_border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 8pt;
            }}
            QPushButton#controlButton:hover {{
                background-color: {self.colors['button_grey_hover']};
            }}
        """
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        title_label = QLabel("Time series Analysis")
        title_label.setObjectName("plotTitle")
        panel_layout.addWidget(title_label)
        placeholder = QFrame()
        placeholder.setObjectName("graphPlaceholder")
        placeholder.setMinimumHeight(220)
        placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        placeholder.setStyleSheet(
            f"""
            #graphPlaceholder {{
                background-color: {self.colors['placeholder_bg']};
                margin: 0px 15px 10px 15px;
            }}
        """
        )
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel("Time Series Visualization")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 10pt; background: transparent;"
        )
        placeholder_layout.addWidget(placeholder_label)
        panel_layout.addWidget(placeholder, stretch=1)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(15, 0, 15, 10)
        control_layout.setSpacing(8)
        zoom_btn = QPushButton("Zoom")
        zoom_btn.setObjectName("controlButton")
        zoom_btn.setIcon(get_icon("SP_FileDialogContentsView"))
        pan_btn = QPushButton("Pan")
        pan_btn.setObjectName("controlButton")
        pan_btn.setIcon(get_icon("SP_DirOpenIcon"))
        zoom_btn.setIconSize(QSize(12, 12))
        pan_btn.setIconSize(QSize(12, 12))
        control_layout.addWidget(zoom_btn)
        control_layout.addWidget(pan_btn)
        control_layout.addStretch(1)
        panel_layout.addLayout(control_layout)
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
        title_label = QLabel("Statistical Summary")
        title_label.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(title_label)
        summary_data = {
            "Mean Firing Rate": "24.5 Hz",
            "Variance": "3.2",
            "Standard Deviation": "1.8",
            "Coherence": "1.6",
        }
        for label, value in summary_data.items():
            sidebar_layout.addWidget(self._create_summary_item(label, value))
        sidebar_layout.addStretch(1)
        refine_button = QPushButton("Refine Data")
        refine_button.setMinimumHeight(36)
        refine_button.setFont(QFont("Arial", 9, QFont.Bold))
        refine_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refine_button.setStyleSheet(
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
        refine_button.clicked.connect(self.handle_refine_data)
        sidebar_layout.addWidget(refine_button)
        # --- Create Export Button ---
        export_button = QPushButton("Export Analysis Report")
        export_button.setMinimumHeight(36)
        export_button.setFont(QFont("Arial", 9, QFont.Bold))
        export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_button.setStyleSheet(
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
        # Connect the export button to the trigger method
        if hasattr(self, "_trigger_export_window_open"):
            print(f"--- DEBUG: Connecting export_button to {self._trigger_export_window_open} ---")
            export_button.clicked.connect(self._trigger_export_window_open)
            print("--- DEBUG: Connection attempted ---")
        else:
            print("--- ERROR: _trigger_export_window_open method not found! Cannot connect export button. ---")
            export_button.setEnabled(False)
        sidebar_layout.addWidget(export_button)
        return sidebar

    def _create_summary_item(self, label_text, value_text):
        item_frame = QFrame()
        item_frame.setObjectName("summaryItem")
        item_layout = QVBoxLayout(item_frame)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(1)
        label = QLabel(label_text)
        label.setObjectName("summaryLabel")
        value = QLabel(value_text)
        value.setObjectName("summaryValue")
        item_layout.addWidget(label)
        item_layout.addWidget(value)
        return item_frame

    # --- Internal Slot Placeholders or Signal Emitters ---
    def handle_unit_selection_change(self):
        print("Widget: Unit selection changed")

    def handle_compare_units(self):
        print("Widget: Compare selected units")

    def handle_refine_data(self):
        print("Widget: Refine data action")


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
