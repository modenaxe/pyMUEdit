import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,  # Using QMainWindow for potential menu/toolbars later
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout, # Using grid for the central plot area
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
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize

# Helper function to get standard icons
def get_icon(standard_icon):
    """Gets a standard Qt icon."""
    return QApplication.style().standardIcon(standard_icon)

class MotorUnitAnalysisWindow(QMainWindow):
    """
    A QMainWindow providing a dashboard interface for motor unit analysis,
    featuring unit selection, various plots, and statistical summaries.
    """
    def __init__(self, parent=None):
        """
        Initializes the MotorUnitAnalysisWindow.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Motor Unit Analysis")
        self.setMinimumSize(1200, 800) # Set a reasonable minimum size

        # Define color scheme
        self.colors = {
            "bg_main": "#f8f9fa",
            "bg_card": "#ffffff",
            "bg_sidebar": "#f8f9fa", # Same as main bg for this design
            "bg_topbar": "#ffffff",
            "border_light": "#e9ecef",
            "border_medium": "#dee2e6",
            "shadow": QColor(0, 0, 0, 25),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_title": "#343a40",
            "placeholder_bg": "#e9ecef",
            "button_dark_bg": "#343a40", # Slightly lighter dark
            "button_dark_text": "#ffffff",
            "button_dark_hover": "#495057",
            "button_grey_bg": "#e9ecef",
            "button_grey_text": "#495057",
            "button_grey_border": "#ced4da",
            "button_grey_hover": "#dee2e6",
            "checkbox_bg": "#f1f3f5",
        }

        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

        # --- Central Widget and Main Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # No margin for the main layout
        self.main_layout.setSpacing(0)

        # --- Top Bar ---
        self.main_layout.addWidget(self._create_top_bar())

        # --- Main Content Area (Sidebars + Center) ---
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(15, 15, 15, 15) # Padding around the content area
        self.content_layout.setSpacing(20) # Space between sidebars and center

        self.content_layout.addWidget(self._create_left_sidebar(), stretch=1) # Left sidebar, smaller stretch factor
        self.content_layout.addWidget(self._create_center_area(), stretch=5) # Center area, larger stretch
        self.content_layout.addWidget(self._create_right_sidebar(), stretch=2) # Right sidebar

        self.main_layout.addLayout(self.content_layout)

    # --- UI Creation Methods ---

    def _create_top_bar(self):
        """Creates the top navigation/title bar."""
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(55)
        top_bar.setStyleSheet(f"""
            #topBar {{
                background-color: {self.colors['bg_topbar']};
                border-bottom: 1px solid {self.colors['border_light']};
            }}
            #topBar > QPushButton {{ /* Style for buttons in top bar */
                background-color: transparent;
                border: none;
                color: {self.colors['text_secondary']};
                font-size: 9pt;
                padding: 5px 10px;
            }}
             #topBar > QPushButton:hover {{
                 color: {self.colors['text_primary']};
             }}
        """)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(15, 0, 15, 0)
        top_bar_layout.setSpacing(10)

        # Left side: Icon + Title
        icon_label = QLabel()
        # Placeholder 'brain' icon - replace with actual QPixmap if available
        icon_pixmap = get_icon(QStyle.SP_ComputerIcon).pixmap(QSize(24, 24)) # Example icon
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(28, 28))
        icon_label.setStyleSheet("border: none; /* Add background/border if needed */")

        title_label = QLabel("Motor Unit Analysis")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.colors['text_title']}; border: none;")

        top_bar_layout.addWidget(icon_label)
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch(1) # Push right-side items

        # Right side: Links + User Icon
        dashboard_btn = QPushButton("Dashboard")
        projects_btn = QPushButton("Projects")
        settings_btn = QPushButton("Settings")
        # User/logout button - using standard icon
        user_button = QPushButton()
        user_button.setIcon(get_icon(QStyle.SP_DialogOkButton)) # Example icon
        user_button.setIconSize(QSize(18, 18))
        user_button.setFixedSize(30, 30)
        user_button.setStyleSheet(f"""
             QPushButton {{
                 background-color: {self.colors['button_dark_bg']};
                 border-radius: 15px; /* Circular */
                 padding: 0px;
             }}
             QPushButton:hover {{
                  background-color: {self.colors['button_dark_hover']};
             }}
        """)
        user_button.setToolTip("User Profile / Logout")

        top_bar_layout.addWidget(dashboard_btn)
        top_bar_layout.addWidget(projects_btn)
        top_bar_layout.addWidget(settings_btn)
        top_bar_layout.addWidget(user_button)

        # Connect signals (placeholders)
        dashboard_btn.clicked.connect(self.handle_dashboard_nav)
        projects_btn.clicked.connect(self.handle_projects_nav)
        settings_btn.clicked.connect(self.handle_settings_nav)
        user_button.clicked.connect(self.handle_user_action)

        return top_bar

    def _create_left_sidebar(self):
        """Creates the left sidebar for motor unit selection."""
        sidebar = QFrame()
        sidebar.setObjectName("leftSidebar")
        # sidebar.setFixedWidth(200) # Optional: Fix width
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0) # No margin for the frame layout
        sidebar_layout.setSpacing(10)
        sidebar.setStyleSheet(f"""
            #leftSidebar QLabel {{ color: {self.colors['text_primary']}; font-size: 10pt; font-weight: bold; border: none; }}
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
        """)

        title_label = QLabel("Motor Units")
        sidebar_layout.addWidget(title_label)

        # Add Checkboxes
        self.unit_checkboxes = [] # Store checkboxes if needed
        for i in range(1, 4): # Example: 3 units
            checkbox = QCheckBox(f"Motor Unit #{i}")
            sidebar_layout.addWidget(checkbox)
            self.unit_checkboxes.append(checkbox)
            checkbox.stateChanged.connect(self.handle_unit_selection_change)

        sidebar_layout.addSpacerItem(QSpacerItem(10, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Compare Button
        compare_button = QPushButton("Compare Selected Units")
        compare_button.setFont(QFont("Arial", 9))
        compare_button.setMinimumHeight(32)
        compare_button.setCursor(Qt.PointingHandCursor)
        compare_button.setStyleSheet(f"""
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
        """)
        compare_button.clicked.connect(self.handle_compare_units)
        sidebar_layout.addWidget(compare_button)

        sidebar_layout.addStretch(1) # Push content upwards
        return sidebar

    def _create_center_area(self):
        """Creates the central scrollable area for plots."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame) # No border for the scroll area itself
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Hide horizontal scrollbar
        scroll_area.setStyleSheet("background-color: transparent; border: none;")

        # Content widget and layout for the scroll area
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        # Using QGridLayout for flexible plot arrangement
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(20) # Spacing between plot panels

        # Add plot panels to the grid
        # Row 0
        grid_layout.addWidget(self._create_plot_panel("Firing Rates", "Firing Rates Graph"), 0, 0)
        grid_layout.addWidget(self._create_plot_panel("Inter-spike Intervals", "Intervals Graph"), 0, 1)

        # Row 1
        grid_layout.addWidget(self._create_plot_panel("Correlation Plot", "Correlation Plot"), 1, 0)
        grid_layout.addWidget(self._create_property_comparison_panel(), 1, 1, 2, 1) # Spans 2 rows

        # Row 2
        grid_layout.addWidget(self._create_plot_panel("Motor Unit Distribution", "Interactive\nHistogram Plot"), 2, 0)

        # Row 3 (Spans both columns)
        grid_layout.addWidget(self._create_time_series_panel(), 3, 0, 1, 2) # Spans 2 columns

        # Set column stretch factors (optional, adjust as needed)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        # grid_layout.setRowStretch(3, 1) # Allow time series to potentially grow

        scroll_area.setWidget(scroll_content)
        return scroll_area

    def _create_plot_panel(self, title, placeholder_text):
        """Helper to create a standard plot panel card."""
        panel = QFrame()
        panel.setObjectName("plotCard")
        panel.setStyleSheet(f"""
            #plotCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border_light']};
                border-radius: 6px;
            }}
            #plotCard > QLabel {{ /* Title label style */
                 color: {self.colors['text_primary']};
                 font-size: 10pt;
                 font-weight: bold;
                 padding: 10px 15px 5px 15px; /* Padding around title */
                 border: none;
                 background: transparent;
            }}
        """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0) # Margins handled by padding/card style
        panel_layout.setSpacing(0) # No space between title and placeholder

        title_label = QLabel(title)
        panel_layout.addWidget(title_label)

        # Placeholder for the graph
        placeholder = QFrame() # Using QFrame for background styling
        placeholder.setObjectName("graphPlaceholder")
        placeholder.setMinimumHeight(180) # Ensure minimum size
        placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        placeholder.setStyleSheet(f"""
            #graphPlaceholder {{
                background-color: {self.colors['placeholder_bg']};
                border-bottom-left-radius: 6px; /* Match card rounding */
                border-bottom-right-radius: 6px;
                margin: 0px 15px 15px 15px; /* Margin around placeholder */
            }}
        """)
        # Optional: Add centered text to placeholder
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel(placeholder_text)
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 10pt; background: transparent;")
        placeholder_layout.addWidget(placeholder_label)

        panel_layout.addWidget(placeholder, stretch=1) # Allow placeholder to expand

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(self.colors['shadow'])
        shadow.setOffset(0, 2)
        panel.setGraphicsEffect(shadow)

        return panel

    def _create_property_comparison_panel(self):
        """Creates the specific panel for Property Comparison with dropdowns."""
        panel = QFrame()
        panel.setObjectName("plotCard") # Reuse plot card style
        panel.setStyleSheet(f"""
            #plotCard {{
                background-color: {self.colors['bg_card']};
                border: 1px solid {self.colors['border_light']};
                border-radius: 6px;
            }}
             #plotCard > QLabel#plotTitle {{ /* Style specifically for the title */
                 color: {self.colors['text_primary']};
                 font-size: 10pt;
                 font-weight: bold;
                 padding: 10px 15px 5px 15px;
                 border: none;
                 background: transparent;
            }}
            QComboBox {{ /* Style for comboboxes in this panel */
                border: 1px solid {self.colors['border_medium']};
                border-radius: 4px;
                padding: 5px 8px;
                background-color: {self.colors['bg_card']};
                color: {self.colors['text_primary']};
                font-size: 9pt;
                min-height: 20px;
            }}
             QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 18px; border-left: 1px solid {self.colors['border_medium']};}}
             QComboBox::down-arrow {{ image: url(:/qt-project.org/styles/commonstyle/images/down_arrow-16.png); width: 10px; height: 10px;}}
        """)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        title_label = QLabel("Property Comparison")
        title_label.setObjectName("plotTitle") # Use object name for specific styling
        panel_layout.addWidget(title_label)

        # Placeholder - make it larger
        placeholder = QFrame()
        placeholder.setObjectName("graphPlaceholder")
        placeholder.setMinimumHeight(250) # Taller placeholder
        placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        placeholder.setStyleSheet(f"""
            #graphPlaceholder {{
                background-color: {self.colors['placeholder_bg']};
                margin: 0px 15px 10px 15px; /* Adjusted margin */
            }}
        """)
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel("Scatter Plot")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 10pt; background: transparent;")
        placeholder_layout.addWidget(placeholder_label)
        panel_layout.addWidget(placeholder, stretch=1)

        # Dropdown controls
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(15, 0, 15, 10) # Margins for controls
        control_layout.setSpacing(10)

        combo_x = QComboBox()
        combo_x.addItems(["X-Axis Property", "Firing Rate", "Amplitude", "Duration"])
        combo_y = QComboBox()
        combo_y.addItems(["Y-Axis Property", "Firing Rate", "Amplitude", "Duration"])

        control_layout.addWidget(combo_x)
        control_layout.addWidget(combo_y)
        control_layout.addStretch(1) # Push dropdowns left

        panel_layout.addLayout(control_layout)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10); shadow.setColor(self.colors['shadow']); shadow.setOffset(0, 2)
        panel.setGraphicsEffect(shadow)
        return panel

    def _create_time_series_panel(self):
        """Creates the specific panel for Time Series Analysis with controls."""
        panel = QFrame()
        panel.setObjectName("plotCard") # Reuse plot card style
        panel.setStyleSheet(f"""
             #plotCard {{ background-color: {self.colors['bg_card']}; border: 1px solid {self.colors['border_light']}; border-radius: 6px; }}
             #plotCard > QLabel#plotTitle {{ color: {self.colors['text_primary']}; font-size: 10pt; font-weight: bold; padding: 10px 15px 5px 15px; border: none; background: transparent;}}
             QPushButton#controlButton {{ /* Style for zoom/pan buttons */
                 background-color: {self.colors['button_grey_bg']};
                 color: {self.colors['button_grey_text']};
                 border: 1px solid {self.colors['button_grey_border']};
                 border-radius: 4px;
                 padding: 4px 8px;
                 font-size: 8pt;
             }}
             QPushButton#controlButton:hover {{ background-color: {self.colors['button_grey_hover']}; }}
         """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0); panel_layout.setSpacing(0)

        title_label = QLabel("Time series Analysis"); title_label.setObjectName("plotTitle")
        panel_layout.addWidget(title_label)

        placeholder = QFrame(); placeholder.setObjectName("graphPlaceholder")
        placeholder.setMinimumHeight(220); placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        placeholder.setStyleSheet(f"#graphPlaceholder {{ background-color: {self.colors['placeholder_bg']}; margin: 0px 15px 10px 15px; }}")
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel("Time Series Visualization"); placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 10pt; background: transparent;")
        placeholder_layout.addWidget(placeholder_label)
        panel_layout.addWidget(placeholder, stretch=1)

        control_layout = QHBoxLayout(); control_layout.setContentsMargins(15, 0, 15, 10); control_layout.setSpacing(8)
        zoom_btn = QPushButton("Zoom"); zoom_btn.setObjectName("controlButton"); zoom_btn.setIcon(get_icon(QStyle.SP_FileDialogContentsView)) # Example icon
        pan_btn = QPushButton("Pan"); pan_btn.setObjectName("controlButton"); pan_btn.setIcon(get_icon(QStyle.SP_DirOpenIcon)) # Example icon
        zoom_btn.setIconSize(QSize(12,12)); pan_btn.setIconSize(QSize(12,12))
        control_layout.addWidget(zoom_btn); control_layout.addWidget(pan_btn); control_layout.addStretch(1)
        panel_layout.addLayout(control_layout)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10); shadow.setColor(self.colors['shadow']); shadow.setOffset(0, 2)
        panel.setGraphicsEffect(shadow)
        return panel

    def _create_right_sidebar(self):
        """Creates the right sidebar for statistical summary and actions."""
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        # sidebar.setFixedWidth(250) # Optional: Fix width
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(15)
        sidebar.setStyleSheet(f"""
            #rightSidebar > QLabel#sidebarTitle {{ color: {self.colors['text_primary']}; font-size: 10pt; font-weight: bold; border: none; background: transparent; }}
            QFrame#summaryItem {{
                background-color: {self.colors['checkbox_bg']}; /* Using checkbox bg color */
                border-radius: 4px;
                border: 1px solid {self.colors['border_light']};
                padding: 8px 10px;
            }}
            QLabel#summaryLabel {{ color: {self.colors['text_secondary']}; font-size: 8pt; border: none; background: transparent; }}
            QLabel#summaryValue {{ color: {self.colors['text_primary']}; font-size: 10pt; font-weight: bold; border: none; background: transparent; }}
        """)

        title_label = QLabel("Statistical Summary")
        title_label.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(title_label)

        # Add Summary Items
        summary_data = {
            "Mean Firing Rate": "24.5 Hz",
            "Variance": "3.2",
            "Standard Deviation": "1.8",
            "Coherence": "1.6", # Example data point
        }
        for label, value in summary_data.items():
            sidebar_layout.addWidget(self._create_summary_item(label, value))

        sidebar_layout.addStretch(1) # Push buttons down

        # Action Buttons
        refine_button = QPushButton("Refine Data")
        refine_button.setMinimumHeight(36)
        refine_button.setFont(QFont("Arial", 9, QFont.Bold))
        refine_button.setCursor(Qt.PointingHandCursor)
        refine_button.setStyleSheet(f"""
             QPushButton {{ background-color: {self.colors['button_dark_bg']}; color: {self.colors['button_dark_text']}; border: none; border-radius: 4px; padding: 8px 10px; }}
             QPushButton:hover {{ background-color: {self.colors['button_dark_hover']}; }}
        """)
        refine_button.clicked.connect(self.handle_refine_data)

        export_button = QPushButton("Export Analysis Report")
        export_button.setMinimumHeight(36)
        export_button.setFont(QFont("Arial", 9, QFont.Bold))
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet(f"""
             QPushButton {{ background-color: {self.colors['button_dark_bg']}; color: {self.colors['button_dark_text']}; border: none; border-radius: 4px; padding: 8px 10px; }}
             QPushButton:hover {{ background-color: {self.colors['button_dark_hover']}; }}
        """)
        export_button.clicked.connect(self.handle_export_report)

        sidebar_layout.addWidget(refine_button)
        sidebar_layout.addWidget(export_button)

        return sidebar

    def _create_summary_item(self, label_text, value_text):
        """Helper to create a statistical summary item."""
        item_frame = QFrame()
        item_frame.setObjectName("summaryItem")
        item_layout = QVBoxLayout(item_frame)
        item_layout.setContentsMargins(0,0,0,0) # Padding handled by frame style
        item_layout.setSpacing(1)

        label = QLabel(label_text)
        label.setObjectName("summaryLabel")
        value = QLabel(value_text)
        value.setObjectName("summaryValue")

        item_layout.addWidget(label)
        item_layout.addWidget(value)
        return item_frame

    # --- Placeholder Slots ---
    def handle_dashboard_nav(self): print("Navigate to Dashboard")
    def handle_projects_nav(self): print("Navigate to Projects")
    def handle_settings_nav(self): print("Navigate to Settings")
    def handle_user_action(self): print("User profile/logout action")
    def handle_unit_selection_change(self): print("Unit selection changed") # Could update plots
    def handle_compare_units(self): print("Compare selected units")
    def handle_refine_data(self): print("Refine data action")
    def handle_export_report(self): print("Export analysis report action")

# --- Main execution block (for testing the window independently) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle("Fusion") # Optional

    analysis_window = MotorUnitAnalysisWindow()
    analysis_window.show()

    sys.exit(app.exec_())