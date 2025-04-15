import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy, QStyle,
    QGraphicsDropShadowEffect, QSpacerItem, QStackedWidget, QFileDialog,
    QMessageBox, QMenu
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QCursor
from PyQt5.QtCore import Qt, QSize

# --- Imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try: from import_data_window import ImportDataWindow
except ImportError: ImportDataWindow = None; print("Warning: import_data_window.py not found.")

try: from MU_analysis import MotorUnitAnalysisWidget
except ImportError as e: MotorUnitAnalysisWidget = None; print(f"Warning: MU_analysis.py failed import: {e}.")

try:
    from export_results import ExportResultsWindow
except ImportError:
    ExportResultsWindow = None
    print("Warning: export_results.py not found.")

# Import our recent datasets manager
try:
    # Try to import from the current directory first
    from recent_datasets_manager import RecentDatasetsManager
except ImportError:
    try:
        # Try alternative import path
        from gui.recent_datasets_manager import RecentDatasetsManager
    except ImportError:
        print("Warning: recent_datasets_manager.py not found.")
        # Create a simple placeholder if the module is not found
        class RecentDatasetsManager:
            def __init__(self, max_entries=10):
                self.recent_datasets = []
            def get_recent_datasets(self, count=None):
                return self.recent_datasets
            def add_dataset(self, filepath, dataset_type="", filesize=None, row_count=None):
                pass
            def remove_dataset(self, filepath):
                pass


class HDEMGDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create recent datasets manager
        self.recent_datasets_manager = RecentDatasetsManager()

        # Instance variables for external windows/widgets
        self.import_window = None
        self.export_results_window = None

        # Define colors
        self.colors = {
            "bg_main": "#f5f5f5", "bg_sidebar": "#f0f0f0", "bg_card": "#e8e8e8",
            "bg_card_hdemg": "#1a73e8", "bg_card_neuro": "#7cb342", "bg_card_emg": "#e91e63",
            "bg_card_eeg": "#9c27b0", "bg_card_default": "#607d8b", "border": "#d0d0d0",
            "text_primary": "#333333", "text_secondary": "#777777", "accent": "#000000",
            "sidebar_selected_bg": "#e6e6e6",
        }
        
        # Recent visualizations data (only categories, not sample data)
        self.recent_visualizations = []
        
        # Setup main window
        self.setWindowTitle("HDEMG App")
        self.resize(1400, 700)
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")
        
        # Main layout setup
        main_widget = QWidget()
        self.main_h_layout = QHBoxLayout(main_widget)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)
        self.setCentralWidget(main_widget)
        
        # Setup sidebar
        self.sidebar_buttons = {}
        self.main_h_layout.addWidget(self._create_left_sidebar())
        
        # Setup central stacked widget
        self.central_stacked_widget = QStackedWidget()
        self.central_stacked_widget.setStyleSheet("background-color: transparent;")
        
        # Add dashboard page
        self.dashboard_page = self._create_dashboard_page()
        self.central_stacked_widget.addWidget(self.dashboard_page)
        
        # Add MU analysis page if available
        if MotorUnitAnalysisWidget:
            self.mu_analysis_page = MotorUnitAnalysisWidget()
            self.mu_analysis_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
            # Connect the MU Analysis widget's request to the export window opener
            if hasattr(self.mu_analysis_page, 'set_export_window_opener'):
                 self.mu_analysis_page.set_export_window_opener(self.open_export_results_window)
            else:
                 print("WARNING: MotorUnitAnalysisWidget does not have 'set_export_window_opener' method.")
            self.central_stacked_widget.addWidget(self.mu_analysis_page)
        else: 
            print("MU Analysis page cannot be added.")
            
        self.main_h_layout.addWidget(self.central_stacked_widget, 1)
        self.show_dashboard_view()

    def open_export_results_window(self):
        """Opens the Export Results window, ensuring the instance persists."""
        if ExportResultsWindow is None:
            print("ExportResultsWindow is not available (export_results.py missing or failed import?).")
            return

        print(">>> Reached open_export_results_window in main_window (Persistent Ref Attempt + ProcessEvents)")

        # Check if the window exists and hasn't been closed/deleted
        window_valid_and_visible = False
        if self.export_results_window:
            try:
                self.export_results_window.isActiveWindow()
                window_valid_and_visible = self.export_results_window.isVisible()
                print(f">>> Existing window valid. Visible: {window_valid_and_visible}")
            except RuntimeError:
                print(">>> Existing window reference found, but C++ object deleted.")
                self.export_results_window = None

        if self.export_results_window is None:
            print(">>> Attempting to create NEW ExportResultsWindow instance.")
            try:
                self.export_results_window = ExportResultsWindow(parent=self)
                print(f">>> Created and stored NEW instance: {self.export_results_window}")
            except Exception as e:
                print(f"!!!!! ERROR during ExportResultsWindow creation: {e}")
                import traceback
                traceback.print_exc()
                self.export_results_window = None
                return

        if self.export_results_window:
            try:
                print(f">>> Showing/Activating instance: {self.export_results_window}")
                self.export_results_window.show()
                self.export_results_window.raise_()
                self.export_results_window.activateWindow()
                QApplication.processEvents()
                print(">>> Called show(), raise_(), activateWindow(), processEvents()")
            except Exception as e:
                 print(f"!!!!! ERROR during ExportResultsWindow show/raise/activate: {e}")
                 import traceback
                 traceback.print_exc()
        else:
             print(">>> ERROR: self.export_results_window is unexpectedly None after creation attempt.")
             
    def _create_dashboard_page(self):
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
        
        # Header with title and new visualization button
        header_layout = QHBoxLayout()
        dashboard_title = QLabel("Dashboard")
        dashboard_title.setFont(QFont("Arial", 18, QFont.Bold))
        dashboard_title.setStyleSheet(f"color: {self.colors['text_primary']};")
        
        new_viz_btn = QPushButton("+ New Visualization")
        new_viz_btn.setFont(QFont("Arial", 9, QFont.Bold))
        new_viz_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        new_viz_btn.setIconSize(QSize(14,14))
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
            new_viz_btn.clicked.connect(self.open_import_data_window)
        else:
            new_viz_btn.setEnabled(False)
            
        header_layout.addWidget(dashboard_title)
        header_layout.addStretch()
        header_layout.addWidget(new_viz_btn)
        content_layout.addLayout(header_layout)
        
        # Main content grid
        content_grid = QVBoxLayout()
        content_grid.setSpacing(20)
        
        # Top row with visualizations and actions
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        viz_section_frame = self._create_viz_section_frame()
        actions_frame = self._create_actions_frame()
        top_row.addWidget(viz_section_frame, 3)
        top_row.addWidget(actions_frame, 1)
        content_grid.addLayout(top_row)
        
        # Bottom row with datasets
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        datasets_frame = self._create_datasets_frame()
        empty_spacer = QFrame()
        empty_spacer.setStyleSheet("background: transparent; border: none;")
        bottom_row.addWidget(datasets_frame, 3)
        bottom_row.addWidget(empty_spacer, 1)
        content_grid.addLayout(bottom_row)
        
        content_layout.addLayout(content_grid)
        
        return dashboard_scroll_area
        
    def _refresh_recent_datasets(self):
        """Refresh the recent datasets display with current data"""
        # First locate and remove the old datasets frame
        try:
            for i in range(self.dashboard_page.findChild(QWidget, "dashboardContentArea").layout().count()):
                item = self.dashboard_page.findChild(QWidget, "dashboardContentArea").layout().itemAt(i)
                if item and isinstance(item, QVBoxLayout):
                    content_grid = item
                    # Find the bottom row in the content grid
                    for j in range(content_grid.count()):
                        sub_item = content_grid.itemAt(j)
                        if sub_item and isinstance(sub_item, QHBoxLayout):
                            bottom_row = sub_item
                            # Remove old datasets frame and create a new one
                            old_frame = bottom_row.itemAt(0).widget()
                            if old_frame and old_frame.objectName() == "datasetsFrame_Original":
                                old_frame.setParent(None)
                                old_frame.deleteLater()
                                # Create and add new frame
                                new_frame = self._create_datasets_frame()
                                bottom_row.insertWidget(0, new_frame, 3)
                                return
        except Exception as e:
            print(f"Error refreshing datasets: {e}")
        
        # If we couldn't find the datasets frame, just recreate the whole dashboard page
        try:
            self.dashboard_page = self._create_dashboard_page()
            self.central_stacked_widget.removeWidget(self.central_stacked_widget.widget(0))
            self.central_stacked_widget.insertWidget(0, self.dashboard_page)
        except Exception as e:
            print(f"Error recreating dashboard page: {e}")
    
    def _create_viz_section_frame(self):
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
            #vizSectionFrame_Original > QScrollArea, 
            #vizSectionFrame_Original > QLabel { 
                border: none; 
                background-color: transparent; 
            }
        """)
        
        viz_layout = QVBoxLayout(viz_section_frame)
        viz_layout.setSpacing(10)
        
        viz_title = QLabel("Recent Visualizations")
        viz_title.setFont(QFont("Arial", 12, QFont.Bold))
        viz_title.setStyleSheet("background: transparent; border: none;")
        
        viz_scroll_area = QScrollArea()
        viz_scroll_area.setObjectName("vizScrollArea_Original")
        viz_scroll_area.setWidgetResizable(True)
        viz_scroll_area.setFrameShape(QFrame.NoFrame)
        viz_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        viz_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viz_scroll_area.setFixedHeight(220)
        viz_scroll_area.setStyleSheet("""
            #vizScrollArea_Original { 
                background-color: transparent; 
                border: none; 
            }
        """)
        
        viz_container = QWidget()
        viz_container.setObjectName("vizContainer_Original")
        viz_container.setStyleSheet("background-color: transparent; border: none;")
        
        viz_container_layout = QHBoxLayout(viz_container)
        viz_container_layout.setSpacing(15)
        viz_container_layout.setContentsMargins(0, 5, 0, 5)
        
        if not self.recent_visualizations:
            no_viz_label = QLabel("No recent visualizations found.")
            no_viz_label.setAlignment(Qt.AlignCenter)
            no_viz_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
            viz_container_layout.addWidget(no_viz_label)
        else:
            for idx, viz_data in enumerate(self.recent_visualizations):
                viz_card = self.create_viz_card(
                    viz_data["title"], 
                    viz_data["date"], 
                    viz_data["type"], 
                    viz_data["icon"], 
                    idx
                )
                viz_container_layout.addWidget(viz_card)
        
        viz_scroll_area.setWidget(viz_container)
        viz_layout.addWidget(viz_title)
        viz_layout.addWidget(viz_scroll_area)
        
        return viz_section_frame
        
    def _create_actions_frame(self):
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame_Original")
        actions_frame.setFrameShape(QFrame.StyledPanel)
        actions_frame.setStyleSheet("""
            #actionsFrame_Original { 
                background-color: white; 
                border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                padding: 15px; 
            } 
            #actionsFrame_Original > QPushButton, 
            #actionsFrame_Original > QLabel { 
                border: none; 
                background-color: transparent; 
            }
        """)
        
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setSpacing(10)
        
        actions_title = QLabel("Quick Actions")
        actions_title.setFont(QFont("Arial", 12, QFont.Bold))
        actions_title.setStyleSheet("background: transparent; border: none;")
        
        import_dataset_btn = self.create_action_button("Import New Dataset", self.style().standardIcon(QStyle.SP_DialogOpenButton))
        if ImportDataWindow:
            import_dataset_btn.clicked.connect(self.open_import_data_window)
        else:
            import_dataset_btn.setEnabled(False)
        
        create_chart_btn = self.create_action_button("Create Chart", self.style().standardIcon(QStyle.SP_DialogHelpButton))
        view_data_btn = self.create_action_button("View Data Table", self.style().standardIcon(QStyle.SP_FileDialogListView))
        
        # Add a refresh button for datasets
        refresh_datasets_btn = self.create_action_button("Refresh Datasets", self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_datasets_btn.clicked.connect(self._refresh_recent_datasets)
        
        # Add open dataset button
        open_dataset_btn = self.create_action_button("Open Dataset File", self.style().standardIcon(QStyle.SP_DirOpenIcon))
        open_dataset_btn.clicked.connect(self.open_dataset_file)
        
        actions_layout.addWidget(actions_title)
        actions_layout.addWidget(import_dataset_btn)
        actions_layout.addWidget(open_dataset_btn)
        actions_layout.addWidget(refresh_datasets_btn)
        actions_layout.addWidget(create_chart_btn)
        actions_layout.addWidget(view_data_btn)
        actions_layout.addStretch()
        
        return actions_frame
    
    def _create_datasets_frame(self):
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
            #datasetsFrame_Original QFrame {}
        """)
        
        datasets_layout = QVBoxLayout(datasets_frame)
        datasets_layout.setSpacing(10)
        
        datasets_title = QLabel("Recent Datasets")
        datasets_title.setFont(QFont("Arial", 12, QFont.Bold))
        datasets_title.setStyleSheet("background: transparent; border: none;")
        datasets_layout.addWidget(datasets_title)
        
        # Get real recent datasets from the manager
        try:
            self.recent_datasets = self.recent_datasets_manager.get_recent_datasets()
        except Exception as e:
            print(f"Error getting recent datasets: {e}")
            self.recent_datasets = []
        
        if not self.recent_datasets:
            no_data_label = QLabel("No recent datasets found.")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet(f"color: {self.colors['text_secondary']};")
            datasets_layout.addWidget(no_data_label)
        else:
            for idx, dataset in enumerate(self.recent_datasets):
                dataset_entry = self.create_dataset_entry(
                    dataset["filename"], 
                    dataset.get("metadata", ""),
                    idx,
                    dataset.get("filepath", "")
                )
                datasets_layout.addWidget(dataset_entry)
        
        datasets_layout.addStretch()
        return datasets_frame

    # --- Sidebar Creation and Button Styling ---
    def _create_left_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFrameShape(QFrame.NoFrame)
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            #sidebar { 
                background-color: #fdfdfd; 
                border: none; 
                border-right: 1px solid #e0e0e0; 
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 15, 0, 15)
        sidebar_layout.setSpacing(5)
        
        app_title_layout = QHBoxLayout()
        app_title_layout.setContentsMargins(15, 0, 15, 0)
        
        app_icon_label = QLabel()
        app_icon_label.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(QSize(24,24)))
        
        app_title_label = QLabel("HDEMG App")
        app_title_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        app_title_layout.addWidget(app_icon_label)
        app_title_layout.addWidget(app_title_label)
        app_title_layout.addStretch()
        
        sidebar_layout.addLayout(app_title_layout)
        sidebar_layout.addSpacerItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Create sidebar buttons
        self.sidebar_buttons['dashboard'] = self._create_sidebar_button_widget("Dashboard", self.style().standardIcon(QStyle.SP_DesktopIcon))
        self.sidebar_buttons['import'] = self._create_sidebar_button_widget("Import Data", self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.sidebar_buttons['mu_analysis'] = self._create_sidebar_button_widget("MU Analysis", self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.sidebar_buttons['dataview'] = self._create_sidebar_button_widget("Data View", self.style().standardIcon(QStyle.SP_FileDialogListView))
        self.sidebar_buttons['viz'] = self._create_sidebar_button_widget("Visualizations", self.style().standardIcon(QStyle.SP_DialogHelpButton))
        self.sidebar_buttons['history'] = self._create_sidebar_button_widget("History", self.style().standardIcon(QStyle.SP_BrowserReload))
        
        # Connect button signals
        self.sidebar_buttons['dashboard'].clicked.connect(self.show_dashboard_view)
        self.sidebar_buttons['mu_analysis'].clicked.connect(self.show_mu_analysis_view)
        
        if ImportDataWindow:
            self.sidebar_buttons['import'].clicked.connect(self.open_import_data_window)
        else:
            self.sidebar_buttons['import'].setEnabled(False)
            
        if not MotorUnitAnalysisWidget:
            self.sidebar_buttons['mu_analysis'].setEnabled(False)
            
        # Add buttons to sidebar
        for btn_key in self.sidebar_buttons:
            sidebar_layout.addWidget(self.sidebar_buttons[btn_key])
            
        sidebar_layout.addStretch()
        
        return sidebar

    def _create_sidebar_button_widget(self, text, icon):
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
        selected_bg = self.colors.get('sidebar_selected_bg', '#e6e6e6')
        hover_bg = selected_bg
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
                QPushButton {{ 
                    {base_layout} {base_font} 
                    background-color: {current_bg}; 
                    color: {current_text}; 
                }} 
                QPushButton:hover {{ 
                    background-color: {hover_bg}; 
                    color: {default_text_color}; 
                }} 
                QPushButton:disabled {{ 
                    color: {disabled_text_color}; 
                    background-color: transparent; 
                }}
            """
            button.setStyleSheet(style)

    # --- Widget Creation Methods with dataset functionality ---
    def create_viz_card(self, title, date, card_type="default", icon_style=None, idx=0):
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
        chart_icon.setStyleSheet(f"""
            #{chart_icon.objectName()} {{ 
                color: {text_color}; 
                background-color: transparent; 
                border: none; 
            }}
        """)
        
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
        title_label.setStyleSheet(f"""
            #{title_label.objectName()} {{ 
                color: {text_color}; 
                background-color: transparent; 
                border: none; 
            }}
        """)
        
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
        date_label.setStyleSheet(f"""
            #{date_label.objectName()} {{ 
                color: {text_color}; 
                font-size: 10px; 
                background-color: transparent; 
                border: none; 
            }}
        """)
        
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
        card.mousePressEvent = lambda event, t=title: self.open_visualization(t)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(2, 2)
        card.setGraphicsEffect(shadow)
        
        return card
    
    def create_action_button(self, text, icon):
        """Create an action button for the Quick Actions panel"""
        btn = QPushButton(text)
        btn.setObjectName(f"actionBtn_{text.replace(' ', '_')}")
        btn.setIcon(icon)
        btn.setIconSize(QSize(16, 16))
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            #{btn.objectName()} {{
                text-align: left;
                padding-left: 15px;
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }}
            #{btn.objectName()}:hover {{
                background-color: #e6e6e6;
            }}
        """)
        return btn
    
    def create_dataset_entry(self, filename, metadata, idx=0, filepath=""):
        """Create a dataset entry for the Recent Datasets panel"""
        sanitized_name = filename.replace(" ", "_").replace(".", "_").lower()
        entry = QFrame()
        entry.setObjectName(f"datasetEntry_{sanitized_name}_{idx}")
        entry.setProperty("filepath", filepath)  # Store filepath for later use
        
        entry.setStyleSheet(f"""
            #{entry.objectName()} {{
                background-color: #f2f2f2;
                border-radius: 4px;
                margin-bottom: 5px;
            }}
            #{entry.objectName()} QLabel,
            #{entry.objectName()} QPushButton {{
                background-color: transparent;
                border: none;
            }}
            #{entry.objectName()}:hover {{
                background-color: #e0e0e0;
            }}
        """)
        
        entry_layout = QHBoxLayout(entry)
        entry_layout.setContentsMargins(12, 12, 12, 12)
        
        # File icon based on extension
        file_icon = QLabel()
        file_icon.setObjectName(f"fileIcon_{sanitized_name}_{idx}")
        
        # Select icon based on file extension
        icon_style = QStyle.SP_FileIcon
        if filename.lower().endswith(('.csv', '.txt')):
            icon_style = QStyle.SP_FileDialogDetailedView
        elif filename.lower().endswith(('.mat')):
            icon_style = QStyle.SP_FileDialogListView
        elif filename.lower().endswith(('.xls', '.xlsx')):
            icon_style = QStyle.SP_FileDialogInfoView
            
        file_icon.setPixmap(self.style().standardIcon(icon_style).pixmap(QSize(16, 16)))
        
        # File info
        file_info = QVBoxLayout()
        name_label = QLabel(filename)
        name_label.setObjectName(f"nameLabel_{sanitized_name}_{idx}")
        name_label.setFont(QFont("Arial", 10))
        
        meta_label = QLabel(metadata)
        meta_label.setObjectName(f"metaLabel_{sanitized_name}_{idx}")
        meta_label.setStyleSheet(f"""
            #{meta_label.objectName()} {{
                color: #777777;
                font-size: 10px;
                background-color: transparent;
                border: none;
            }}
        """)
        
        file_info.addWidget(name_label)
        file_info.addWidget(meta_label)
        
        # Options button
        options_btn = QPushButton("⋮")
        options_btn.setObjectName(f"optionsBtn_{sanitized_name}_{idx}")
        options_btn.setFixedSize(40, 40)
        options_btn.setFont(QFont("Arial", 20))
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
        
        # Connect options button to show context menu
        options_btn.clicked.connect(lambda: self.show_dataset_options_menu(entry, options_btn))
        
        # Make entire entry clickable
        entry.setCursor(Qt.PointingHandCursor)
        entry.mousePressEvent = lambda event: self.open_dataset(filepath)
        
        entry_layout.addWidget(file_icon)
        entry_layout.addLayout(file_info, 1)
        entry_layout.addWidget(options_btn)
        
        return entry
    
    def show_dataset_options_menu(self, entry, button):
        """Show context menu for dataset options"""
        filepath = entry.property("filepath")
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 25px 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #f0f0f0;
            }
        """)
        
        # Add menu actions
        open_action = menu.addAction("Open")
        open_action.triggered.connect(lambda: self.open_dataset(filepath))
        
        import_action = menu.addAction("Import")
        import_action.triggered.connect(lambda: self.import_dataset(filepath))
        
        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self.view_dataset_details(filepath))
        
        menu.addSeparator()
        
        remove_action = menu.addAction("Remove from Recent")
        remove_action.triggered.connect(lambda: self.remove_dataset_from_recent(filepath, entry))
        
        # Show menu at button position
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))
    
    def open_dataset(self, filepath):
        """Open a dataset file"""
        if not filepath:
            QMessageBox.warning(self, "Warning", "No file path available for this dataset.")
            return
            
        try:
            # Try to open the file using the system's default application
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', filepath))
            else:  # Linux
                subprocess.call(('xdg-open', filepath))
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
    
    def import_dataset(self, filepath):
        """Import a dataset via the ImportDataWindow"""
        if not ImportDataWindow:
            QMessageBox.warning(self, "Not Available", "Import functionality is not available.")
            return
            
        if not filepath:
            QMessageBox.warning(self, "Warning", "No file path available for this dataset.")
            return
            
        # Open the import window
        self.open_import_data_window()
        
        # Set the filepath if the window is open
        if self.import_window:
            # Notify user - we can't directly set the file because ImportDataWindow 
            # has its own file selection logic
            QMessageBox.information(
                self, 
                "Select File", 
                f"Please select the file:\n{filepath}\nin the Import Data window."
            )
    
    def view_dataset_details(self, filepath):
        """Show details about a dataset"""
        if not filepath:
            QMessageBox.warning(self, "Warning", "No file path available for this dataset.")
            return
            
        try:
            # Get file info
            file_info = os.stat(filepath)
            file_size = file_info.st_size
            modify_time = file_info.st_mtime
            
            # Format size
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.1f} KB"
            else:
                size_str = f"{file_size/(1024*1024):.1f} MB"
                
            # Format time
            import datetime
            modify_date = datetime.datetime.fromtimestamp(modify_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # Show info
            QMessageBox.information(
                self,
                "File Details",
                f"Filename: {os.path.basename(filepath)}\n"
                f"Path: {os.path.dirname(filepath)}\n"
                f"Size: {size_str}\n"
                f"Last Modified: {modify_date}\n"
                f"Type: {os.path.splitext(filepath)[1]}"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not get file details: {str(e)}")
    
    def remove_dataset_from_recent(self, filepath, entry):
        """Remove a dataset from recent files"""
        try:
            # Remove from manager
            if hasattr(self.recent_datasets_manager, 'remove_dataset'):
                self.recent_datasets_manager.remove_dataset(filepath)
                
            # Remove widget from UI
            entry.setParent(None)
            entry.deleteLater()
            
            # Refresh the view
            self._refresh_recent_datasets()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not remove dataset: {str(e)}")
    
    def open_dataset_file(self):
        """Open a file dialog to select a dataset file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Open Dataset File",
            "",
            "All Files (*);;CSV Files (*.csv);;MAT Files (*.mat);;Excel Files (*.xlsx)"
        )
        
        if file_path:
            # Add to recent datasets
            try:
                if hasattr(self.recent_datasets_manager, 'add_dataset'):
                    # Get file size
                    file_size = os.path.getsize(file_path)
                    
                    # Add to manager
                    self.recent_datasets_manager.add_dataset(
                        file_path,
                        os.path.splitext(file_path)[1],
                        file_size,
                        None  # No row count information
                    )
                    
                    # Refresh the view
                    self._refresh_recent_datasets()
            except Exception as e:
                print(f"Error adding dataset to recent files: {e}")
            
            # Try to open the file
            self.open_dataset(file_path)

    def open_import_data_window(self):
        """Open the import data window (separate window)."""
        if ImportDataWindow is None: 
            print("ImportDataWindow not available.")
            return
            
        print("Opening import data window")
        # Use self.import_window to track instance
        if self.import_window is None or not self.import_window.isVisible():
            self.import_window = ImportDataWindow(parent=self)
            self.import_window.show()
        else:
            self.import_window.raise_()
            self.import_window.activateWindow()

    def open_visualization(self, title):
        """Open a visualization based on its title."""
        print(f"Clicked visualization: {title}")
        if "HDEMG Analysis" in title:
            self.show_mu_analysis_view()
        else:
            print(f"Placeholder: Action for visualization '{title}'")
    
    def show_dashboard_view(self):
        """Switches the central widget to the dashboard page."""
        print("Switching to Dashboard View")
        self.central_stacked_widget.setCurrentWidget(self.dashboard_page)
        self._update_sidebar_selection('dashboard')

    def show_mu_analysis_view(self):
        """Switches the central widget to the MU Analysis page."""
        if hasattr(self, 'mu_analysis_page'):
            print("Switching to MU Analysis View")
            self.central_stacked_widget.setCurrentWidget(self.mu_analysis_page)
            self._update_sidebar_selection('mu_analysis')
        else:
            print("MU Analysis view is not available.")
    
    def darken_color(self, hex_color, amount=20):
        """Darken a color by the specified amount."""
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HDEMGDashboard()
    window.show()
    sys.exit(app.exec_())