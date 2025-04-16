import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy, QStyle,
    QGraphicsDropShadowEffect, QSpacerItem, QStackedWidget
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize
import traceback  # Added for error handling

# Adjust path to include modules in the same directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from import_data_window import ImportDataWindow
except ImportError:
    ImportDataWindow = None
    print("Warning: import_data_window.py not found.")

try:
    from MU_analysis import MotorUnitAnalysisWidget
except ImportError as e:
    MotorUnitAnalysisWidget = None
    print(f"Warning: MU_analysis.py failed import: {e}.")

# --- ADD Import for ExportResultsWindow here ---
try:
    from export_results import ExportResultsWindow
except ImportError:
    ExportResultsWindow = None
    print("Warning: export_results.py not found.")
# --- END ADD Import ---

# --- ADD Placeholders for new page widgets (if they exist) ---
# try:
#     from manual_editing_widget import ManualEditingWidget # Example
# except ImportError:
#     ManualEditingWidget = None
#     print("Warning: manual_editing_widget.py not found (needed for 'Manual Editing').")
#
# try:
#     from decomposition_widget import DecompositionWidget # Example
# except ImportError:
#     DecompositionWidget = None
#     print("Warning: decomposition_widget.py not found (needed for 'Decomposition').")
# --- END Placeholder Imports ---


class HDEMGDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Instance variables for external windows/widgets
        self.import_data_page = None
        self.export_results_window = None  # <-- Instance variable in main window
        # Add instance variables for new pages if needed
        # self.manual_editing_page = None
        # self.decomposition_page = None

        # Colors and recent items for demonstration
        self.colors = {
            "bg_main": "#f5f5f5", "bg_sidebar": "#f0f0f0", "bg_card": "#e8e8e8",
            "bg_card_hdemg": "#1a73e8", "bg_card_neuro": "#7cb342", "bg_card_emg": "#e91e63",
            "bg_card_eeg": "#9c27b0", "bg_card_default": "#607d8b", "border": "#d0d0d0",
            "text_primary": "#333333", "text_secondary": "#777777", "accent": "#000000",
            "sidebar_selected_bg": "#e6e6e6",
        }
        self.recent_visualizations = [
            {"title": "HDEMG Analysis", "date": "Last modified: Jan 15, 2025", "type": "hdemg", "icon": QStyle.SP_ToolBarHorizontalExtensionButton},
            {"title": "Neuro Analysis", "date": "Last modified: Jan 14, 2025", "type": "neuro", "icon": QStyle.SP_DialogApplyButton},
            {"title": "EMG Recording 23", "date": "Last modified: Jan 13, 2025", "type": "emg", "icon": QStyle.SP_FileDialogInfoView},
            {"title": "EEG Study Results", "date": "Last modified: Jan 10, 2025", "type": "eeg", "icon": QStyle.SP_DialogHelpButton},
        ]
        self.recent_datasets = [
            {"filename": "HDEMG_Analysis2025.csv", "metadata": "2.5MB • 1,000 rows"},
            {"filename": "NeuroSignal_Analysis.xlsx", "metadata": "1.8MB • 750 rows"},
            {"filename": "EMG_Recording23.dat", "metadata": "3.2MB • 1,500 rows"},
            {"filename": "EEG_Study_Jan2025.csv", "metadata": "5.1MB • 2,200 rows"},
        ]

        # Main window settings
        self.setWindowTitle("HDEMG App")
        self.resize(1400, 700)
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

        # Create main widget and layout
        main_widget = QWidget()
        self.main_h_layout = QHBoxLayout(main_widget)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # Create Sidebar and add to layout
        self.sidebar_buttons = {}
        self.main_h_layout.addWidget(self._create_left_sidebar())

        # Create the central stacked widget
        self.central_stacked_widget = QStackedWidget()
        self.central_stacked_widget.setStyleSheet("background-color: transparent;")

        # Dashboard page
        self.dashboard_page = self._create_dashboard_page()
        self.central_stacked_widget.addWidget(self.dashboard_page)

        # MU Analysis page
        if MotorUnitAnalysisWidget:
            self.mu_analysis_page = MotorUnitAnalysisWidget()
            self.mu_analysis_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
            if hasattr(self.mu_analysis_page, 'set_export_window_opener'):
                self.mu_analysis_page.set_export_window_opener(self.open_export_results_window)
            else:
                print("WARNING: MotorUnitAnalysisWidget does not have 'set_export_window_opener' method.")
            self.central_stacked_widget.addWidget(self.mu_analysis_page)
        else:
            print("MU Analysis page cannot be added.")

        # Import Data page (embedded view)
        if ImportDataWindow:
            # Create an instance of ImportDataWindow as a child widget.
            self.import_data_page = ImportDataWindow(parent=self)
            # Change window flags so it behaves as a widget.
            self.import_data_page.setWindowFlags(Qt.Widget)
            # Optionally connect a signal to return to dashboard:
            if hasattr(self.import_data_page, "return_to_dashboard_requested"):
                self.import_data_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
            self.central_stacked_widget.addWidget(self.import_data_page)
        else:
            print("Warning: ImportDataWindow not available.")

        # --- ADD Placeholder pages to StackedWidget ---
        # Manual Editing Page (Placeholder)
        self.manual_editing_page = QWidget() # Replace with actual widget if available
        manual_layout = QVBoxLayout(self.manual_editing_page)
        manual_label = QLabel("Manual Editing Page (Placeholder)")
        manual_label.setAlignment(Qt.AlignCenter)
        manual_label.setFont(QFont("Arial", 16))
        back_button_manual = QPushButton("Back to Dashboard")
        back_button_manual.clicked.connect(self.show_dashboard_view)
        manual_layout.addWidget(manual_label)
        manual_layout.addWidget(back_button_manual)
        manual_layout.addStretch()
        self.central_stacked_widget.addWidget(self.manual_editing_page)

        # Decomposition Page (Placeholder)
        self.decomposition_page = QWidget() # Replace with actual widget if available
        decomp_layout = QVBoxLayout(self.decomposition_page)
        decomp_label = QLabel("Decomposition Page (Placeholder)")
        decomp_label.setAlignment(Qt.AlignCenter)
        decomp_label.setFont(QFont("Arial", 16))
        back_button_decomp = QPushButton("Back to Dashboard")
        back_button_decomp.clicked.connect(self.show_dashboard_view)
        decomp_layout.addWidget(decomp_label)
        decomp_layout.addWidget(back_button_decomp)
        decomp_layout.addStretch()
        self.central_stacked_widget.addWidget(self.decomposition_page)
        # --- END Placeholder Pages ---


        self.main_h_layout.addWidget(self.central_stacked_widget, 1)
        self.show_dashboard_view() # Start on dashboard


    # --- Dashboard and layout creation methods ---
    def _create_dashboard_page(self):
        # ... (rest of the dashboard creation code remains the same) ...
        dashboard_scroll_area = QScrollArea()
        dashboard_scroll_area.setWidgetResizable(True)
        dashboard_scroll_area.setFrameShape(QFrame.NoFrame)
        dashboard_scroll_area.setStyleSheet("background-color: transparent; border: none;")
        content_area = QWidget()
        content_area.setObjectName("dashboardContentArea")
        content_area.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)
        dashboard_scroll_area.setWidget(content_area)

        # Header
        header_layout = QHBoxLayout()
        dashboard_title = QLabel("Dashboard")
        dashboard_title.setFont(QFont("Arial", 18, QFont.Bold))
        dashboard_title.setStyleSheet(f"color: {self.colors['text_primary']};")
        new_viz_btn = QPushButton("+ New Analysis") # Changed text slightly
        new_viz_btn.setFont(QFont("Arial", 9, QFont.Bold))
        new_viz_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        new_viz_btn.setIconSize(QSize(14, 14))
        new_viz_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['accent']};
                color: white;
                border-radius: 4px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
        """)
        if ImportDataWindow:
             # Connect to Import Data, as it's the first step
            new_viz_btn.clicked.connect(self.show_import_data_view)
        else:
            new_viz_btn.setEnabled(False)
        header_layout.addWidget(dashboard_title)
        header_layout.addStretch()
        header_layout.addWidget(new_viz_btn)
        content_layout.addLayout(header_layout)

        # Content Grid: Only Visualizations and Datasets Frames
        content_grid = QVBoxLayout()
        content_grid.setSpacing(20)

        # Top Row: Visualizations
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        viz_section_frame = self._create_viz_section_frame()
        top_row.addWidget(viz_section_frame)
        content_grid.addLayout(top_row)

        # Bottom Row: Datasets
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        datasets_frame = self._create_datasets_frame()
        bottom_row.addWidget(datasets_frame)
        content_grid.addLayout(bottom_row)

        content_layout.addLayout(content_grid)
        content_layout.addStretch(1)
        return dashboard_scroll_area

    def _create_viz_section_frame(self):
        # ... (rest of the viz section creation code remains the same) ...
        viz_section_frame = QFrame()
        viz_section_frame.setObjectName("vizSectionFrame_Original")
        viz_section_frame.setFrameShape(QFrame.StyledPanel)
        viz_section_frame.setStyleSheet("""
            #vizSectionFrame_Original {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            #vizSectionFrame_Original > QScrollArea, #vizSectionFrame_Original > QLabel {
                border: none;
                background-color: transparent;
            }
        """)
        viz_layout = QVBoxLayout(viz_section_frame)
        viz_layout.setSpacing(10)
        viz_title = QLabel("Recent Analyses") # Renamed for context
        viz_title.setFont(QFont("Arial", 12, QFont.Bold))
        viz_title.setStyleSheet("background: transparent; border: none;")
        viz_scroll_area = QScrollArea()
        viz_scroll_area.setObjectName("vizScrollArea_Original")
        viz_scroll_area.setWidgetResizable(True)
        viz_scroll_area.setFrameShape(QFrame.NoFrame)
        viz_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        viz_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viz_scroll_area.setFixedHeight(220)
        viz_scroll_area.setStyleSheet("#vizScrollArea_Original { background-color: transparent; border: none; }")
        viz_container = QWidget()
        viz_container.setObjectName("vizContainer_Original")
        viz_container.setStyleSheet("background-color: transparent; border: none;")
        viz_container_layout = QHBoxLayout(viz_container)
        viz_container_layout.setSpacing(15)
        viz_container_layout.setContentsMargins(0, 5, 0, 5)
        if not self.recent_visualizations:
            no_viz_label = QLabel("No recent analyses found.")
            no_viz_label.setAlignment(Qt.AlignCenter)
            no_viz_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
            viz_container_layout.addWidget(no_viz_label)
        else:
            for idx, viz_data in enumerate(self.recent_visualizations):
                viz_card = self.create_viz_card(viz_data["title"], viz_data["date"], viz_data["type"], viz_data["icon"], idx)
                viz_container_layout.addWidget(viz_card)
        viz_scroll_area.setWidget(viz_container)
        viz_layout.addWidget(viz_title)
        viz_layout.addWidget(viz_scroll_area)
        return viz_section_frame

    def _create_datasets_frame(self):
        # ... (rest of the datasets frame creation code remains the same) ...
        datasets_frame = QFrame()
        datasets_frame.setObjectName("datasetsFrame_Original")
        datasets_frame.setFrameShape(QFrame.NoFrame)
        datasets_frame.setStyleSheet("""
            #datasetsFrame_Original {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            #datasetsFrame_Original > QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        datasets_layout = QVBoxLayout(datasets_frame)
        datasets_layout.setSpacing(10)
        datasets_title = QLabel("Recent Datasets")
        datasets_title.setFont(QFont("Arial", 12, QFont.Bold))
        datasets_title.setStyleSheet("background: transparent; border: none;")
        datasets_layout.addWidget(datasets_title)
        if not self.recent_datasets:
            no_data_label = QLabel("No recent datasets found.")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
            datasets_layout.addWidget(no_data_label)
        else:
            for idx, dataset in enumerate(self.recent_datasets):
                dataset_entry = self.create_dataset_entry(dataset["filename"], dataset["metadata"], idx)
                datasets_layout.addWidget(dataset_entry)
        datasets_layout.addStretch()
        return datasets_frame

    def _create_left_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFrameShape(QFrame.NoFrame)
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("#sidebar { background-color: #fdfdfd; border: none; border-right: 1px solid #e0e0e0; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 15, 0, 15)
        sidebar_layout.setSpacing(5)
        app_title_layout = QHBoxLayout()
        app_title_layout.setContentsMargins(15, 0, 15, 0)
        app_icon_label = QLabel()
        app_icon_label.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(QSize(24, 24)))
        app_title_label = QLabel("HDEMG App")
        app_title_label.setFont(QFont("Arial", 12, QFont.Bold))
        app_title_layout.addWidget(app_icon_label)
        app_title_layout.addWidget(app_title_label)
        app_title_layout.addStretch()
        sidebar_layout.addLayout(app_title_layout)
        sidebar_layout.addSpacerItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # --- Define Sidebar Buttons (Updated) ---
        self.sidebar_buttons['dashboard'] = self._create_sidebar_button_widget("Dashboard", self.style().standardIcon(QStyle.SP_DesktopIcon))
        self.sidebar_buttons['import'] = self._create_sidebar_button_widget("Import Data", self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.sidebar_buttons['mu_analysis'] = self._create_sidebar_button_widget("MU Analysis", self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        # --- ADD NEW BUTTONS ---
        self.sidebar_buttons['decomposition'] = self._create_sidebar_button_widget("Decomposition", self.style().standardIcon(QStyle.SP_ArrowRight)) # Example Icon
        self.sidebar_buttons['manual_edit'] = self._create_sidebar_button_widget("Manual Editing", self.style().standardIcon(QStyle.SP_DialogYesButton)) # Example Icon
        # --- REMOVE OLD BUTTONS (by not creating them) ---
        # self.sidebar_buttons['dataview'] = self._create_sidebar_button_widget("Data View", self.style().standardIcon(QStyle.SP_FileDialogListView))
        # self.sidebar_buttons['viz'] = self._create_sidebar_button_widget("Visualizations", self.style().standardIcon(QStyle.SP_DialogHelpButton))
        # self.sidebar_buttons['history'] = self._create_sidebar_button_widget("History", self.style().standardIcon(QStyle.SP_BrowserReload))
        # --- END Button Definition ---

        # --- Connect Button Signals ---
        self.sidebar_buttons['dashboard'].clicked.connect(self.show_dashboard_view)
        self.sidebar_buttons['mu_analysis'].clicked.connect(self.show_mu_analysis_view)
        self.sidebar_buttons['decomposition'].clicked.connect(self.show_decomposition_view) # Connect new button
        self.sidebar_buttons['manual_edit'].clicked.connect(self.show_manual_editing_view) # Connect new button

        if ImportDataWindow:
            self.sidebar_buttons['import'].clicked.connect(self.show_import_data_view) # Use show_import_data_view
        else:
            self.sidebar_buttons['import'].setEnabled(False)
        if not MotorUnitAnalysisWidget:
            self.sidebar_buttons['mu_analysis'].setEnabled(False)
        # Add enable/disable logic for new buttons if their widgets might be missing
        # if not DecompositionWidget:
        #     self.sidebar_buttons['decomposition'].setEnabled(False)
        # if not ManualEditingWidget:
        #     self.sidebar_buttons['manual_edit'].setEnabled(False)
        # --- END Signal Connections ---

        # --- Add Buttons to Layout ---
        for btn in self.sidebar_buttons.values():
            sidebar_layout.addWidget(btn)
        # --- END Adding Buttons ---

        sidebar_layout.addStretch()
        return sidebar

    def _create_sidebar_button_widget(self, text, icon):
        # ... (this function remains the same) ...
        btn = QPushButton(text)
        btn.setObjectName(f"sidebarBtn_{text.replace(' ', '_')}")
        btn.setIcon(icon)
        btn.setIconSize(QSize(18, 18))
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 15px;
                border: none;
                border-radius: 0;
                font-weight: bold;
                font-size: 9pt;
                color: {self.colors['text_primary']};
                background-color: transparent;
            }}
            QPushButton:hover {{
                background-color: {self.colors['sidebar_selected_bg']};
            }}
            QPushButton:disabled {{
                color: #aaa;
                background-color: transparent;
            }}
        """)
        return btn

    def _update_sidebar_selection(self, selected_key):
        # ... (this function remains the same) ...
        selected_bg = self.colors.get('sidebar_selected_bg', '#e6e6e6')
        default_text_color = self.colors.get('text_primary', '#333333')
        disabled_text_color = '#aaa'
        for key, button in self.sidebar_buttons.items():
            base_layout = "text-align: left; padding-left: 15px; border: none; border-radius: 0;"
            base_font = "font-weight: bold; font-size: 9pt;"
            current_bg = "transparent"
            current_text = default_text_color
            if not button.isEnabled():
                current_text = disabled_text_color
            elif key == selected_key:
                current_bg = selected_bg
            style = f"""
                QPushButton {{ {base_layout} {base_font} background-color: {current_bg}; color: {current_text}; }}
                QPushButton:hover {{ background-color: {selected_bg}; color: {default_text_color}; }}
                QPushButton:disabled {{ color: {disabled_text_color}; background-color: transparent; }}
            """
            button.setStyleSheet(style)

    def create_viz_card(self, title, date, card_type="default", icon_style=None, idx=0):
        # ... (this function remains the same) ...
        card = QFrame()
        sanitized_title = title.replace(" ", "_").replace(":", "").lower()
        card.setObjectName(f"vizCard_{sanitized_title}_{idx}")
        card.setFrameShape(QFrame.StyledPanel)
        card.setFixedSize(250, 180)
        card.setProperty("title", title)
        if card_type in self.colors:
            bg_color = self.colors.get(f"bg_card_{card_type}", self.colors["bg_card_default"])
        else:
            bg_color = self.colors["bg_card_default"]
        text_color = "white"
        border_color = self.darken_color(bg_color, 20)
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        icon_section = QFrame(card)
        icon_section.setObjectName(f"iconSection_{sanitized_title}_{idx}")
        icon_section.setStyleSheet(f"""
            #{icon_section.objectName()} {{
                background-color: {self.darken_color(bg_color, 10)};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            #{icon_section.objectName()} QLabel {{
                color: {text_color};
                background-color: transparent;
                border: none;
            }}
        """)
        icon_layout = QVBoxLayout(icon_section)
        icon_layout.setContentsMargins(5, 5, 5, 5)
        chart_icon = QLabel()
        chart_icon.setObjectName(f"chartIcon_{sanitized_title}_{idx}")
        icon_to_use = icon_style if icon_style is not None else QStyle.SP_FileDialogDetailedView
        chart_icon.setPixmap(self.style().standardIcon(icon_to_use).pixmap(QSize(24, 24)))
        chart_icon.setAlignment(Qt.AlignCenter)
        chart_icon.setStyleSheet(f"#{chart_icon.objectName()} {{ color: {text_color}; background-color: transparent; border: none; }}")
        icon_layout.addWidget(chart_icon)
        title_section = QFrame(card)
        title_section.setObjectName(f"titleSection_{sanitized_title}_{idx}")
        title_section.setStyleSheet(f"""
            #{title_section.objectName()} {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            #{title_section.objectName()} QLabel {{
                color: {text_color};
                background-color: transparent;
                border: none;
            }}
        """)
        title_layout = QVBoxLayout(title_section)
        title_layout.setContentsMargins(5, 5, 5, 5)
        title_label = QLabel(title)
        title_label.setObjectName(f"titleLabel_{sanitized_title}_{idx}")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"#{title_label.objectName()} {{ color: {text_color}; background-color: transparent; border: none; }}")
        title_layout.addWidget(title_label)
        date_section = QFrame(card)
        date_section.setObjectName(f"dateSection_{sanitized_title}_{idx}")
        date_section.setStyleSheet(f"""
            #{date_section.objectName()} {{
                background-color: {self.darken_color(bg_color, 15)};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            #{date_section.objectName()} QLabel {{
                color: {text_color};
                background-color: transparent;
                border: none;
            }}
        """)
        date_layout = QVBoxLayout(date_section)
        date_layout.setContentsMargins(5, 5, 5, 5)
        date_label = QLabel(date)
        date_label.setObjectName(f"dateLabel_{sanitized_title}_{idx}")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet(f"#{date_label.objectName()} {{ color: {text_color}; font-size: 10px; background-color: transparent; border: none; }}")
        date_layout.addWidget(date_label)
        main_layout.addWidget(icon_section)
        main_layout.addWidget(title_section)
        main_layout.addWidget(date_section)
        card.setStyleSheet(f"""
            #{card.objectName()} {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            #{card.objectName()} > QLabel {{
                color: {text_color};
                background-color: transparent;
                border: none;
            }}
            #{card.objectName()} > QFrame {{
                border: none;
            }}
        """)
        card.setCursor(Qt.PointingHandCursor)
        # Adjusted lambda to pass the correct view name if needed
        card.mousePressEvent = lambda event, t=title: self.open_visualization(t)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(2, 2)
        card.setGraphicsEffect(shadow)
        return card

    def create_dataset_entry(self, filename, metadata, idx=0):
        # ... (this function remains the same) ...
        sanitized_name = filename.replace(" ", "_").replace(".", "_").lower()
        entry = QFrame()
        entry.setObjectName(f"datasetEntry_{sanitized_name}_{idx}")
        entry.setStyleSheet(f"""
            #{entry.objectName()} {{
                background-color: #f2f2f2;
                border-radius: 4px;
                margin-bottom: 5px;
            }}
            #{entry.objectName()} QLabel, #{entry.objectName()} QPushButton {{
                background-color: transparent;
                border: none;
            }}
        """)
        entry_layout = QHBoxLayout(entry)
        entry_layout.setContentsMargins(12, 12, 12, 12)
        file_icon = QLabel()
        file_icon.setObjectName(f"fileIcon_{sanitized_name}_{idx}")
        file_icon.setPixmap(self.style().standardIcon(QStyle.SP_FileIcon).pixmap(QSize(16, 16)))
        file_info = QVBoxLayout()
        name_label = QLabel(filename)
        name_label.setObjectName(f"nameLabel_{sanitized_name}_{idx}")
        name_label.setFont(QFont("Arial", 10))
        meta_label = QLabel(metadata)
        meta_label.setObjectName(f"metaLabel_{sanitized_name}_{idx}")
        meta_label.setStyleSheet(f"#{meta_label.objectName()} {{ color: #777777; font-size: 10px; background-color: transparent; border: none; }}")
        file_info.addWidget(name_label)
        file_info.addWidget(meta_label)
        options_btn = QPushButton("⋮")
        options_btn.setObjectName(f"optionsBtn_{sanitized_name}_{idx}")
        options_btn.setFixedSize(40, 40)
        options_btn.setFont(QFont("Arial", 30))
        options_btn.setCursor(Qt.PointingHandCursor)
        options_btn.setStyleSheet(f"""
            #{options_btn.objectName()} {{
                background: transparent;
                border: none;
            }}
            #{options_btn.objectName()}:hover {{
                background-color: #e0e0e0;
                border-radius: 20px;
            }}
        """)
        entry_layout.addWidget(file_icon)
        entry_layout.addLayout(file_info, 1)
        entry_layout.addWidget(options_btn)
        return entry

    def darken_color(self, hex_color, amount=20):
        # ... (this function remains the same) ...
        try:
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = max(0, r - amount)
            g = max(0, g - amount)
            b = max(0, b - amount)
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#aaaaaa"

    # --- Slots / Event Handlers ---
    def show_dashboard_view(self):
        """Switches the central widget to the dashboard page."""
        print("Switching to Dashboard View")
        self.central_stacked_widget.setCurrentWidget(self.dashboard_page)
        self._update_sidebar_selection('dashboard')

    def show_mu_analysis_view(self):
        """Switches the central widget to the MU Analysis page."""
        if hasattr(self, 'mu_analysis_page') and self.mu_analysis_page:
            print("Switching to MU Analysis View")
            self.central_stacked_widget.setCurrentWidget(self.mu_analysis_page)
            self._update_sidebar_selection('mu_analysis')
        else:
            print("MU Analysis view is not available.")

    def show_import_data_view(self): # Renamed from open_import_data_window
        """Switches the central widget to the Import Data page."""
        if ImportDataWindow is None or self.import_data_page is None:
            print("ImportDataWindow not available.")
            return
        print("Switching to Import Data view")
        self.central_stacked_widget.setCurrentWidget(self.import_data_page)
        self._update_sidebar_selection('import')

    def show_manual_editing_view(self):
        """Placeholder: Switches to Manual Editing view."""
        print("Switching to Manual Editing View")
        if hasattr(self, 'manual_editing_page') and self.manual_editing_page:
             self.central_stacked_widget.setCurrentWidget(self.manual_editing_page)
             self._update_sidebar_selection('manual_edit')
        else:
            print("Manual Editing view widget not found.")
            # Optionally, switch back to dashboard or show an error message
            # self.show_dashboard_view()

    def show_decomposition_view(self):
        """Placeholder: Switches to Decomposition view."""
        print("Switching to Decomposition View")
        if hasattr(self, 'decomposition_page') and self.decomposition_page:
            self.central_stacked_widget.setCurrentWidget(self.decomposition_page)
            self._update_sidebar_selection('decomposition')
        else:
            print("Decomposition view widget not found.")
            # Optionally, switch back to dashboard or show an error message
            # self.show_dashboard_view()

    def open_visualization(self, title):
        """Handles clicks on visualization cards."""
        print(f"Clicked visualization/analysis card: {title}")
        # Updated logic to potentially map titles to views
        if "HDEMG Analysis" in title and hasattr(self, 'mu_analysis_page') and self.mu_analysis_page:
            self.show_mu_analysis_view()
        # Add other mappings here if needed, e.g., based on title or type
        # elif "Decomposition" in title:
        #    self.show_decomposition_view()
        else:
            print(f"No specific action defined for card '{title}'. Staying on Dashboard.")
            # Or maybe default to showing the dashboard if clicked from another view
            # self.show_dashboard_view()


    def open_export_results_window(self):
        """Opens the Export Results window, creating it if necessary."""
        print(">>> Main Window: Request received to open Export Results window.")
        if ExportResultsWindow is None:
            print("ERROR: ExportResultsWindow class is not available (check import).")
            return

        window_exists = False
        if self.export_results_window:
            try:
                # Check if the window still exists and hasn't been closed/deleted
                if self.export_results_window.isVisible() or not self.export_results_window.isHidden():
                     window_exists = True
                     print(">>> Main Window: Existing ExportResultsWindow instance seems valid.")
                else:
                     print(">>> Main Window: Existing window reference present but window is hidden/closed; will create new.")
                     self.export_results_window = None # Force recreation
                     window_exists = False
            except RuntimeError: # Window was likely deleted
                print(">>> Main Window: Existing window reference invalid (RuntimeError); will create new.")
                self.export_results_window = None
                window_exists = False
            except Exception as e: # Catch other potential issues
                 print(f">>> Main Window: Error checking existing window ({type(e).__name__}); will create new.")
                 self.export_results_window = None
                 window_exists = False


        if not window_exists:
            try:
                print(">>> Main Window: Creating NEW ExportResultsWindow instance.")
                # Ensure it's created as a top-level window (parent=None)
                self.export_results_window = ExportResultsWindow(parent=None)
                # Position it relative to the main window for convenience
                main_geo = self.geometry()
                new_x = main_geo.x() + 100
                new_y = main_geo.y() + 100
                width = 600  # Define desired size
                height = 550
                self.export_results_window.setGeometry(new_x, new_y, width, height)
                print(f">>> Set geometry for new window to ({new_x}, {new_y}, {width}, {height})")
            except Exception as e:
                print(f"FATAL ERROR during ExportResultsWindow creation: {e}")
                traceback.print_exc()
                self.export_results_window = None # Ensure it's None if creation failed
                return # Stop execution here

        # After potentially creating or confirming existence, try to show/activate
        if self.export_results_window:
            try:
                print(">>> Main Window: Attempting to show and activate ExportResultsWindow.")
                self.export_results_window.show()
                self.export_results_window.raise_() # Bring to front
                self.export_results_window.activateWindow() # Give focus
                QApplication.processEvents() # Ensure UI updates
                print(">>> ExportResultsWindow shown and activated.")
            except RuntimeError: # Catch if window was deleted between check and show
                print(">>> Error: ExportResultsWindow was deleted before it could be shown.")
                self.export_results_window = None
                # Maybe try creating it again? Or just log the error.
            except Exception as e:
                print(f"Error displaying/activating ExportResultsWindow: {e}")
                traceback.print_exc()
                # Consider setting self.export_results_window = None here too
        else:
            print("ERROR - self.export_results_window is None even after creation attempt.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HDEMGDashboard()
    window.show()
    sys.exit(app.exec_())