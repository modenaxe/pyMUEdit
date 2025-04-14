# main_window.py

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy, QStyle,
    QGraphicsDropShadowEffect, QSpacerItem, QStackedWidget
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize

# --- Imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try: from import_data_window import ImportDataWindow
except ImportError: ImportDataWindow = None; print("Warning: import_data_window.py not found.")

try: from MU_analysis import MotorUnitAnalysisWidget
except ImportError as e: MotorUnitAnalysisWidget = None; print(f"Warning: MU_analysis.py failed import: {e}.")

# --- ADD Import for ExportResultsWindow here ---
try:
    from export_results import ExportResultsWindow
except ImportError:
    ExportResultsWindow = None
    print("Warning: export_results.py not found.")
# --- END ADD Import ---


class HDEMGDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Instance variables for external windows/widgets
        self.import_window = None
        self.export_results_window = None # <-- Instance variable in main window

        # ... (rest of __init__ remains the same up to adding stacked widget) ...
        self.colors = { # Shortened for brevity
            "bg_main": "#f5f5f5", "bg_sidebar": "#f0f0f0", "bg_card": "#e8e8e8",
            "bg_card_hdemg": "#1a73e8", "bg_card_neuro": "#7cb342", "bg_card_emg": "#e91e63",
            "bg_card_eeg": "#9c27b0", "bg_card_default": "#607d8b", "border": "#d0d0d0",
            "text_primary": "#333333", "text_secondary": "#777777", "accent": "#000000",
            "sidebar_selected_bg": "#e6e6e6",
        }
        self.recent_visualizations = [ {"title": "HDEMG Analysis", "date": "Last modified: Jan 15, 2025", "type": "hdemg", "icon": QStyle.SP_ToolBarHorizontalExtensionButton,}, {"title": "Neuro Analysis", "date": "Last modified: Jan 14, 2025", "type": "neuro", "icon": QStyle.SP_DialogApplyButton,}, {"title": "EMG Recording 23", "date": "Last modified: Jan 13, 2025", "type": "emg", "icon": QStyle.SP_FileDialogInfoView,}, {"title": "EEG Study Results", "date": "Last modified: Jan 10, 2025", "type": "eeg", "icon": QStyle.SP_DialogHelpButton,}, ]
        self.recent_datasets = [ {"filename": "HDEMG_Analysis2025.csv", "metadata": "2.5MB • 1,000 rows"}, {"filename": "NeuroSignal_Analysis.xlsx", "metadata": "1.8MB • 750 rows"}, {"filename": "EMG_Recording23.dat", "metadata": "3.2MB • 1,500 rows"}, {"filename": "EEG_Study_Jan2025.csv", "metadata": "5.1MB • 2,200 rows"}, ]
        self.setWindowTitle("HDEMG App"); self.resize(1400, 700); self.setMinimumSize(1000, 600); self.setStyleSheet(f"background-color: {self.colors['bg_main']};")
        main_widget = QWidget(); self.main_h_layout = QHBoxLayout(main_widget); self.main_h_layout.setContentsMargins(0, 0, 0, 0); self.main_h_layout.setSpacing(0); self.setCentralWidget(main_widget)
        self.sidebar_buttons = {}; self.main_h_layout.addWidget(self._create_left_sidebar())
        self.central_stacked_widget = QStackedWidget(); self.central_stacked_widget.setStyleSheet("background-color: transparent;")
        self.dashboard_page = self._create_dashboard_page(); self.central_stacked_widget.addWidget(self.dashboard_page)
        if MotorUnitAnalysisWidget:
            self.mu_analysis_page = MotorUnitAnalysisWidget()
            self.mu_analysis_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
            # --- Connect the MU Analysis widget's request to the new main window method ---
            # We need a way for the MU Analysis widget to trigger the export window.
            # Option 1: Pass a reference of the main window method (simpler here)
            # Option 2: Define a new signal in MU Analysis and connect it here (more decoupled)
            # Going with Option 1 for simplicity:
            if hasattr(self.mu_analysis_page, 'set_export_window_opener'):
                 self.mu_analysis_page.set_export_window_opener(self.open_export_results_window)
            else:
                 print("WARNING: MotorUnitAnalysisWidget does not have 'set_export_window_opener' method.")
            # --- End connection ---
            self.central_stacked_widget.addWidget(self.mu_analysis_page)
        else: print("MU Analysis page cannot be added.")
        self.main_h_layout.addWidget(self.central_stacked_widget, 1)
        self.show_dashboard_view()
        # --- End __init__ changes ---

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
                # --- ADD THIS LINE ---
                QApplication.processEvents()
                # --- END ADD ---
                print(">>> Called show(), raise_(), activateWindow(), processEvents()")
            except Exception as e:
                 print(f"!!!!! ERROR during ExportResultsWindow show/raise/activate: {e}")
                 import traceback
                 traceback.print_exc()
        else:
             print(">>> ERROR: self.export_results_window is unexpectedly None after creation attempt.")
    def _create_dashboard_page(self):
        dashboard_scroll_area = QScrollArea(); dashboard_scroll_area.setWidgetResizable(True); dashboard_scroll_area.setFrameShape(QFrame.NoFrame); dashboard_scroll_area.setStyleSheet("background-color: transparent; border: none;")
        content_area = QWidget(); content_area.setObjectName("dashboardContentArea"); content_area.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_area); content_layout.setContentsMargins(25, 25, 25, 25); content_layout.setSpacing(20); dashboard_scroll_area.setWidget(content_area)
        header_layout = QHBoxLayout(); dashboard_title = QLabel("Dashboard"); dashboard_title.setFont(QFont("Arial", 18, QFont.Bold)); dashboard_title.setStyleSheet(f"color: {self.colors['text_primary']};")
        new_viz_btn = QPushButton("+ New Visualization"); new_viz_btn.setFont(QFont("Arial", 9, QFont.Bold)); new_viz_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder)); new_viz_btn.setIconSize(QSize(14,14)); new_viz_btn.setStyleSheet(f"""QPushButton {{ background-color: {self.colors['accent']}; color: white; border-radius: 4px; padding: 8px 15px; }} QPushButton:hover {{ background-color: #333333; }}""")
        if ImportDataWindow: new_viz_btn.clicked.connect(self.open_import_data_window)
        else: new_viz_btn.setEnabled(False)
        header_layout.addWidget(dashboard_title); header_layout.addStretch(); header_layout.addWidget(new_viz_btn); content_layout.addLayout(header_layout)
        content_grid = QVBoxLayout(); content_grid.setSpacing(20)
        top_row = QHBoxLayout(); top_row.setSpacing(20); viz_section_frame = self._create_viz_section_frame(); actions_frame = self._create_actions_frame(); top_row.addWidget(viz_section_frame, 3); top_row.addWidget(actions_frame, 1); content_grid.addLayout(top_row)
        bottom_row = QHBoxLayout(); bottom_row.setSpacing(20); datasets_frame = self._create_datasets_frame(); empty_spacer = QFrame(); empty_spacer.setStyleSheet("background: transparent; border: none;"); bottom_row.addWidget(datasets_frame, 3); bottom_row.addWidget(empty_spacer, 1); content_grid.addLayout(bottom_row)
        content_layout.addLayout(content_grid); return dashboard_scroll_area
    def _create_viz_section_frame(self):
        viz_section_frame = QFrame(); viz_section_frame.setObjectName("vizSectionFrame_Original"); viz_section_frame.setFrameShape(QFrame.StyledPanel); viz_section_frame.setStyleSheet("""#vizSectionFrame_Original { background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; } #vizSectionFrame_Original > QScrollArea, #vizSectionFrame_Original > QLabel { border: none; background-color: transparent; }""")
        viz_layout = QVBoxLayout(viz_section_frame); viz_layout.setSpacing(10); viz_title = QLabel("Recent Visualizations"); viz_title.setFont(QFont("Arial", 12, QFont.Bold)); viz_title.setStyleSheet("background: transparent; border: none;")
        viz_scroll_area = QScrollArea(); viz_scroll_area.setObjectName("vizScrollArea_Original"); viz_scroll_area.setWidgetResizable(True); viz_scroll_area.setFrameShape(QFrame.NoFrame); viz_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); viz_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); viz_scroll_area.setFixedHeight(220); viz_scroll_area.setStyleSheet("#vizScrollArea_Original { background-color: transparent; border: none; }")
        viz_container = QWidget(); viz_container.setObjectName("vizContainer_Original"); viz_container.setStyleSheet("background-color: transparent; border: none;")
        viz_container_layout = QHBoxLayout(viz_container); viz_container_layout.setSpacing(15); viz_container_layout.setContentsMargins(0, 5, 0, 5)
        if not self.recent_visualizations: no_viz_label = QLabel("No recent visualizations found."); no_viz_label.setAlignment(Qt.AlignCenter); no_viz_label.setStyleSheet(f"color: {self.colors['text_secondary']};"); viz_container_layout.addWidget(no_viz_label)
        else:
            for idx, viz_data in enumerate(self.recent_visualizations): viz_card = self.create_viz_card(viz_data["title"], viz_data["date"], viz_data["type"], viz_data["icon"], idx); viz_container_layout.addWidget(viz_card)
        viz_scroll_area.setWidget(viz_container); viz_layout.addWidget(viz_title); viz_layout.addWidget(viz_scroll_area); return viz_section_frame
    def _create_actions_frame(self):
        actions_frame = QFrame(); actions_frame.setObjectName("actionsFrame_Original"); actions_frame.setFrameShape(QFrame.StyledPanel); actions_frame.setStyleSheet("""#actionsFrame_Original { background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; } #actionsFrame_Original > QPushButton, #actionsFrame_Original > QLabel { border: none; background-color: transparent; }""")
        actions_layout = QVBoxLayout(actions_frame); actions_layout.setSpacing(10); actions_title = QLabel("Quick Actions"); actions_title.setFont(QFont("Arial", 12, QFont.Bold)); actions_title.setStyleSheet("background: transparent; border: none;")
        import_dataset_btn = self.create_action_button("Import New Dataset", self.style().standardIcon(QStyle.SP_DialogOpenButton));
        if ImportDataWindow: import_dataset_btn.clicked.connect(self.open_import_data_window)
        else: import_dataset_btn.setEnabled(False)
        create_chart_btn = self.create_action_button("Create Chart", self.style().standardIcon(QStyle.SP_DialogHelpButton)); view_data_btn = self.create_action_button("View Data Table", self.style().standardIcon(QStyle.SP_FileDialogListView))
        actions_layout.addWidget(actions_title); actions_layout.addWidget(import_dataset_btn); actions_layout.addWidget(create_chart_btn); actions_layout.addWidget(view_data_btn); actions_layout.addStretch(); return actions_frame
    def _create_datasets_frame(self):
        datasets_frame = QFrame(); datasets_frame.setObjectName("datasetsFrame_Original"); datasets_frame.setFrameShape(QFrame.NoFrame); datasets_frame.setStyleSheet("""#datasetsFrame_Original { background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; } #datasetsFrame_Original > QLabel { background-color: transparent; border: none; } #datasetsFrame_Original QFrame {}""")
        datasets_layout = QVBoxLayout(datasets_frame); datasets_layout.setSpacing(10); datasets_title = QLabel("Recent Datasets"); datasets_title.setFont(QFont("Arial", 12, QFont.Bold)); datasets_title.setStyleSheet("background: transparent; border: none;")
        datasets_layout.addWidget(datasets_title)
        if not self.recent_datasets: no_data_label = QLabel("No recent datasets found."); no_data_label.setAlignment(Qt.AlignCenter); no_data_label.setStyleSheet(f"color: {self.colors['text_secondary']};"); datasets_layout.addWidget(no_data_label)
        else:
             for idx, dataset in enumerate(self.recent_datasets): dataset_entry = self.create_dataset_entry(dataset["filename"], dataset["metadata"], idx); datasets_layout.addWidget(dataset_entry)
        datasets_layout.addStretch(); return datasets_frame


    # --- Sidebar Creation and Button Styling ---
    def _create_left_sidebar(self):
        # (Implementation is the same as the previous version)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFrameShape(QFrame.NoFrame); sidebar.setFixedWidth(200); sidebar.setStyleSheet("#sidebar { background-color: #fdfdfd; border: none; border-right: 1px solid #e0e0e0; }")
        sidebar_layout = QVBoxLayout(sidebar); sidebar_layout.setContentsMargins(0, 15, 0, 15); sidebar_layout.setSpacing(5); app_title_layout = QHBoxLayout(); app_title_layout.setContentsMargins(15, 0, 15, 0); app_icon_label = QLabel(); app_icon_label.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(QSize(24,24))); app_title_label = QLabel("HDEMG App"); app_title_label.setFont(QFont("Arial", 12, QFont.Bold)); app_title_layout.addWidget(app_icon_label); app_title_layout.addWidget(app_title_label); app_title_layout.addStretch(); sidebar_layout.addLayout(app_title_layout); sidebar_layout.addSpacerItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        self.sidebar_buttons['dashboard'] = self._create_sidebar_button_widget("Dashboard", self.style().standardIcon(QStyle.SP_DesktopIcon)); self.sidebar_buttons['import'] = self._create_sidebar_button_widget("Import Data", self.style().standardIcon(QStyle.SP_DialogOpenButton)); self.sidebar_buttons['mu_analysis'] = self._create_sidebar_button_widget("MU Analysis", self.style().standardIcon(QStyle.SP_FileDialogDetailedView)); self.sidebar_buttons['dataview'] = self._create_sidebar_button_widget("Data View", self.style().standardIcon(QStyle.SP_FileDialogListView)); self.sidebar_buttons['viz'] = self._create_sidebar_button_widget("Visualizations", self.style().standardIcon(QStyle.SP_DialogHelpButton)); self.sidebar_buttons['history'] = self._create_sidebar_button_widget("History", self.style().standardIcon(QStyle.SP_BrowserReload))
        self.sidebar_buttons['dashboard'].clicked.connect(self.show_dashboard_view); self.sidebar_buttons['mu_analysis'].clicked.connect(self.show_mu_analysis_view)
        if ImportDataWindow: self.sidebar_buttons['import'].clicked.connect(self.open_import_data_window)
        else: self.sidebar_buttons['import'].setEnabled(False)
        if not MotorUnitAnalysisWidget: self.sidebar_buttons['mu_analysis'].setEnabled(False)
        for btn_key in self.sidebar_buttons: sidebar_layout.addWidget(self.sidebar_buttons[btn_key])
        sidebar_layout.addStretch(); return sidebar

    def _create_sidebar_button_widget(self, text, icon):
        # (Implementation uses original style - same as previous version)
        btn = QPushButton(text); btn.setObjectName(f"sidebarBtn_{text.replace(' ', '_')}"); btn.setIcon(icon); btn.setIconSize(QSize(18, 18)); btn.setMinimumHeight(40); btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""QPushButton {{ text-align: left; padding-left: 15px; border: none; border-radius: 0; font-weight: bold; font-size: 9pt; color: {self.colors['text_primary']}; background-color: transparent; }} QPushButton:hover {{ background-color: {self.colors['sidebar_selected_bg']}; }} QPushButton:disabled {{ color: #aaa; background-color: transparent; }}""")
        return btn

    def _update_sidebar_selection(self, selected_key):
        # (Implementation is the same as the previous version)
        selected_bg = self.colors.get('sidebar_selected_bg', '#e6e6e6'); hover_bg = selected_bg; default_text_color = self.colors.get('text_primary', '#333333'); disabled_text_color = '#aaa'
        for key, button in self.sidebar_buttons.items():
            base_layout = "text-align: left; padding-left: 15px; border: none; border-radius: 0;"; base_font = "font-weight: bold; font-size: 9pt;"
            current_bg = "transparent"; current_text = default_text_color
            if not button.isEnabled(): current_text = disabled_text_color
            elif key == selected_key: current_bg = selected_bg
            style = f"""QPushButton {{ {base_layout} {base_font} background-color: {current_bg}; color: {current_text}; }} QPushButton:hover {{ background-color: {hover_bg}; color: {default_text_color}; }} QPushButton:disabled {{ color: {disabled_text_color}; background-color: transparent; }}"""
            button.setStyleSheet(style)


    # --- Widget Creation Methods (Original versions for dashboard content) ---
    # (create_viz_card, create_action_button, create_dataset_entry - unchanged)
    def create_viz_card(self, title, date, card_type="default", icon_style=None, idx=0):
        card = QFrame(); sanitized_title = title.replace(" ", "_").replace(":", "").lower(); card.setObjectName(f"vizCard_{sanitized_title}_{idx}"); card.setFrameShape(QFrame.StyledPanel); card.setFixedSize(250, 180); card.setProperty("title", title)
        if card_type in self.colors: bg_color = self.colors.get(f"bg_card_{card_type}", self.colors["bg_card_default"])
        else: bg_color = self.colors["bg_card_default"]
        text_color = "white"; border_color = self.darken_color(bg_color, 20)
        main_layout = QVBoxLayout(card); main_layout.setContentsMargins(10, 10, 10, 10); main_layout.setSpacing(10)
        icon_section = QFrame(card); icon_section.setObjectName(f"iconSection_{sanitized_title}_{idx}"); icon_section.setStyleSheet(f"""#{icon_section.objectName()} {{ background-color: {self.darken_color(bg_color, 10)}; border: 1px solid {border_color}; border-radius: 4px; }} #{icon_section.objectName()} QLabel {{ color: {text_color}; background-color: transparent; border: none; }}""")
        icon_layout = QVBoxLayout(icon_section); icon_layout.setContentsMargins(5, 5, 5, 5); chart_icon = QLabel(); chart_icon.setObjectName(f"chartIcon_{sanitized_title}_{idx}"); icon_to_use = icon_style if icon_style is not None else QStyle.SP_FileDialogDetailedView; chart_icon.setPixmap(self.style().standardIcon(icon_to_use).pixmap(QSize(24, 24))); chart_icon.setAlignment(Qt.AlignCenter); chart_icon.setStyleSheet(f"#{chart_icon.objectName()} {{ color: {text_color}; background-color: transparent; border: none; }}"); icon_layout.addWidget(chart_icon)
        title_section = QFrame(card); title_section.setObjectName(f"titleSection_{sanitized_title}_{idx}"); title_section.setStyleSheet(f"""#{title_section.objectName()} {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 4px; }} #{title_section.objectName()} QLabel {{ color: {text_color}; background-color: transparent; border: none; }}""")
        title_layout = QVBoxLayout(title_section); title_layout.setContentsMargins(5, 5, 5, 5); title_label = QLabel(title); title_label.setObjectName(f"titleLabel_{sanitized_title}_{idx}"); title_label.setFont(QFont("Arial", 11, QFont.Bold)); title_label.setAlignment(Qt.AlignCenter); title_label.setStyleSheet(f"#{title_label.objectName()} {{ color: {text_color}; background-color: transparent; border: none; }}"); title_layout.addWidget(title_label)
        date_section = QFrame(card); date_section.setObjectName(f"dateSection_{sanitized_title}_{idx}"); date_section.setStyleSheet(f"""#{date_section.objectName()} {{ background-color: {self.darken_color(bg_color, 15)}; border: 1px solid {border_color}; border-radius: 4px; }} #{date_section.objectName()} QLabel {{ color: {text_color}; background-color: transparent; border: none; }}""")
        date_layout = QVBoxLayout(date_section); date_layout.setContentsMargins(5, 5, 5, 5); date_label = QLabel(date); date_label.setObjectName(f"dateLabel_{sanitized_title}_{idx}"); date_label.setAlignment(Qt.AlignCenter); date_label.setStyleSheet(f"#{date_label.objectName()} {{ color: {text_color}; font-size: 10px; background-color: transparent; border: none; }}"); date_layout.addWidget(date_label)
        main_layout.addWidget(icon_section); main_layout.addWidget(title_section); main_layout.addWidget(date_section)
        card.setStyleSheet(f"""#{card.objectName()} {{ background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 8px; }} #{card.objectName()} > QLabel {{ color: {text_color}; background-color: transparent; border: none; }} #{card.objectName()} > QFrame {{ border: none; }}""")
        card.setCursor(Qt.PointingHandCursor); card.mousePressEvent = lambda event, t=title: self.open_visualization(t)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(10); shadow.setColor(QColor(0, 0, 0, 60)); shadow.setOffset(2, 2); card.setGraphicsEffect(shadow)
        return card
    def create_action_button(self, text, icon):
        btn = QPushButton(text); btn.setObjectName(f"actionBtn_{text.replace(' ', '_')}"); btn.setIcon(icon); btn.setIconSize(QSize(16, 16)); btn.setMinimumHeight(40); btn.setCursor(Qt.PointingHandCursor); btn.setStyleSheet(f"""#{btn.objectName()} {{ text-align: left; padding-left: 15px; background-color: #f5f5f5; border: 1px solid #e0e0e0; border-radius: 4px; }} #{btn.objectName()}:hover {{ background-color: #e6e6e6; }}""")
        return btn
    def create_dataset_entry(self, filename, metadata, idx=0):
        sanitized_name = filename.replace(" ", "_").replace(".", "_").lower(); entry = QFrame(); entry.setObjectName(f"datasetEntry_{sanitized_name}_{idx}"); entry.setStyleSheet(f"""#{entry.objectName()} {{ background-color: #f2f2f2; border-radius: 4px; margin-bottom: 5px; }} #{entry.objectName()} QLabel, #{entry.objectName()} QPushButton {{ background-color: transparent; border: none; }}""")
        entry_layout = QHBoxLayout(entry); entry_layout.setContentsMargins(12, 12, 12, 12); file_icon = QLabel(); file_icon.setObjectName(f"fileIcon_{sanitized_name}_{idx}"); file_icon.setPixmap(self.style().standardIcon(QStyle.SP_FileIcon).pixmap(QSize(16, 16)))
        file_info = QVBoxLayout(); name_label = QLabel(filename); name_label.setObjectName(f"nameLabel_{sanitized_name}_{idx}"); name_label.setFont(QFont("Arial", 10)); meta_label = QLabel(metadata); meta_label.setObjectName(f"metaLabel_{sanitized_name}_{idx}"); meta_label.setStyleSheet(f"#{meta_label.objectName()} {{ color: #777777; font-size: 10px; background-color: transparent; border: none; }}"); file_info.addWidget(name_label); file_info.addWidget(meta_label)
        options_btn = QPushButton("⋮"); options_btn.setObjectName(f"optionsBtn_{sanitized_name}_{idx}"); options_btn.setFixedSize(40, 40); options_btn.setFont(QFont("Arial", 30)); options_btn.setCursor(Qt.PointingHandCursor); options_btn.setStyleSheet(f"""#{options_btn.objectName()} {{ background: transparent; border: none; }} #{options_btn.objectName()}:hover {{ background-color: #e0e0e0; border-radius: 20px; }}""")
        entry_layout.addWidget(file_icon); entry_layout.addLayout(file_info, 1); entry_layout.addWidget(options_btn); return entry
    def darken_color(self, hex_color, amount=20):
        try: hex_color = hex_color.lstrip("#"); r = int(hex_color[0:2], 16); g = int(hex_color[2:4], 16); b = int(hex_color[4:6], 16); r = max(0, r - amount); g = max(0, g - amount); b = max(0, b - amount); return f"#{r:02x}{g:02x}{b:02x}"
        except: return "#aaaaaa"

    # --- Slots / Event Handlers ---

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

    def open_visualization(self, title):
        print(f"Clicked visualization: {title}")
        if "HDEMG Analysis" in title:
             self.show_mu_analysis_view()
        else:
             print(f"Placeholder: Action for visualization '{title}'")

    def open_import_data_window(self):
        """Open the import data window (separate window)."""
        if ImportDataWindow is None: print("ImportDataWindow not available."); return
        print("Opening import data window")
        # Use self.import_window to track instance
        if self.import_window is None or not self.import_window.isVisible():
            self.import_window = ImportDataWindow(parent=self)
            self.import_window.show()
        else:
            self.import_window.raise_(); self.import_window.activateWindow()

    def open_export_results_window(self):
        """Opens the Export Results window, creating it if necessary."""
        print(">>> Main Window: Request received to open Export Results window.") # Debug
        if ExportResultsWindow is None:
            print("ERROR: ExportResultsWindow class is not available (check import).")
            return

        window_exists = False
        if self.export_results_window:
            try:
                self.export_results_window.isActiveWindow() # Check validity
                window_exists = True
                print(">>> Main Window: Existing ExportResultsWindow instance found.")
            except RuntimeError:
                print(">>> Main Window: Existing window reference found, but C++ object was deleted. Will create new.")
                self.export_results_window = None
                window_exists = False

        if not window_exists:
            try:
                print(">>> Main Window: Creating NEW ExportResultsWindow instance.")
                # --- CHANGE THIS LINE ---
                self.export_results_window = ExportResultsWindow(parent=None) # Create with NO parent
                # --- END CHANGE ---
                print(f">>> Main Window: NEW instance created: {self.export_results_window}")

                # Keep the geometry setting (important now it has no parent reference)
                try:
                    # Get main window geometry to position relative to it
                    main_geo = self.geometry()
                    new_x = main_geo.x() + 100
                    new_y = main_geo.y() + 100

                    # Use a default size or the window's preferred size
                    # Using fixed size initially might be safer
                    width = 600
                    height = 550
                    self.export_results_window.setGeometry(new_x, new_y, width, height)
                    print(f">>> Main Window: Set geometry for new window to ({new_x}, {new_y}, {width}, {height})")
                except Exception as e_geo:
                    print(f"!!!!! WARNING: Could not set geometry: {e_geo}")

            except Exception as e:
                print(f"!!!!! FATAL ERROR during ExportResultsWindow creation: {e}")
                traceback.print_exc()
                self.export_results_window = None
                return

        if self.export_results_window:
            try:
                print(f">>> Main Window: Showing/Activating instance: {self.export_results_window}")

                # --- Optional: Ensure geometry is set even for existing windows ---
                if not self.export_results_window.isVisible(): # Only reposition if hidden
                    try:
                        main_geo = self.geometry()
                        new_x = main_geo.x() + 100
                        new_y = main_geo.y() + 100
                        # Check if the stored window's geometry seems unreasonable (e.g., off-screen)
                        current_geo = self.export_results_window.geometry()
                        if current_geo.x() < -100 or current_geo.y() < -100: # Simple check for off-screen
                            print(f">>> Main Window: Repositioning existing hidden window from {current_geo}")
                            self.export_results_window.setGeometry(new_x, new_y, 600, 550)
                        else:
                            # If geometry looks okay, maybe just move it slightly to ensure visibility
                            self.export_results_window.move(new_x, new_y)

                    except Exception as e_geo_existing:
                        print(f"!!!!! WARNING: Could not set geometry for existing window: {e_geo_existing}")
                # --- End Optional ---

                if not self.export_results_window.isVisible():
                    self.export_results_window.show()
                self.export_results_window.raise_()
                self.export_results_window.activateWindow()
                QApplication.processEvents() # Process events AFTER trying to show/raise
                print(">>> Main Window: Called show()/raise_()/activateWindow()/processEvents()")
            except Exception as e:
                print(f"!!!!! ERROR during ExportResultsWindow show/raise/activate: {e}")
                traceback.print_exc()
        else:
            print(">>> Main Window: ERROR - self.export_results_window is None even after creation attempt.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle("Fusion")
    window = HDEMGDashboard()
    window.show()
    sys.exit(app.exec_())