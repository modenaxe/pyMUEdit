import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QGridLayout,
    QStyle,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize

# Add necessary paths to the system path
current_dir = os.path.dirname(os.path.abspath(__file__))  # gui folder
project_root = os.path.dirname(current_dir)  # project root
sys.path.append(project_root)
sys.path.append(current_dir)

# Import the ImportDataWindow class from the same directory
from import_data_window import ImportDataWindow

# Import MUedit class from the root directory
from MUedit import MUedit


class HDEMGDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Define color scheme
        self.colors = {
            "bg_main": "#f5f5f5",
            "bg_sidebar": "#f0f0f0",
            "bg_card": "#e8e8e8",
            "bg_card_hdemg": "#1a73e8",  # Blue
            "bg_card_neuro": "#7cb342",  # Green
            "bg_card_emg": "#e91e63",  # Pink
            "bg_card_eeg": "#9c27b0",  # Purple
            "bg_card_default": "#607d8b",  # Blue Grey
            "border": "#d0d0d0",
            "text_primary": "#333333",
            "text_secondary": "#777777",
            "accent": "#000000",
        }

        # Sample visualization data - in a real app, this would come from a database or file
        self.recent_visualizations = [
            {
                "title": "HDEMG Analysis",
                "date": "Last modified: Jan 15, 2025",
                "type": "hdemg",
                "icon": QStyle.SP_ToolBarHorizontalExtensionButton,
            },
            {
                "title": "Neuro Analysis",
                "date": "Last modified: Jan 14, 2025",
                "type": "neuro",
                "icon": QStyle.SP_DialogApplyButton,
            },
            {
                "title": "EMG Recording 23",
                "date": "Last modified: Jan 13, 2025",
                "type": "emg",
                "icon": QStyle.SP_FileDialogInfoView,
            },
            {
                "title": "EEG Study Results",
                "date": "Last modified: Jan 10, 2025",
                "type": "eeg",
                "icon": QStyle.SP_DialogHelpButton,
            },
        ]

        # Sample dataset data
        self.recent_datasets = [
            {"filename": "HDEMG_Analysis2025.csv", "metadata": "2.5MB • 1,000 rows"},
            {"filename": "NeuroSignal_Analysis.xlsx", "metadata": "1.8MB • 750 rows"},
            {"filename": "EMG_Recording23.dat", "metadata": "3.2MB • 1,500 rows"},
            {"filename": "EEG_Study_Jan2025.csv", "metadata": "5.1MB • 2,200 rows"},
        ]

        self.setWindowTitle("HDEMG App")
        self.setWindowIcon(QIcon("icons/app_icon.png"))
        self.resize(1400, 600)

        # Enable resizing
        self.setMinimumSize(600, 400)  # Set minimum size
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set main window background color
        self.setStyleSheet(f"background-color: {self.colors['bg_main']};")

        # Main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Left sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(
            """
            #sidebar {
                background-color: #f5f5f5;
                border: none;
                border-right: 1px solid #e0e0e0;
            }
        """
        )
        sidebar_layout = QVBoxLayout(sidebar)

        # App title
        app_title = QLabel("HDEMG App")
        app_title.setFont(QFont("Arial", 14, QFont.Bold))
        app_title.setContentsMargins(10, 10, 10, 20)

        # Sidebar buttons with Qt standard icons
        dashboard_btn = self.create_sidebar_button("Dashboard", self.style().standardIcon(QStyle.SP_DesktopIcon), True)
        import_btn = self.create_sidebar_button("Import Data", self.style().standardIcon(QStyle.SP_DialogOpenButton))
        import_btn.clicked.connect(self.open_import_data_window)  # Connect button to open import window
        dataview_btn = self.create_sidebar_button(
            "Data View", self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        )
        viz_btn = self.create_sidebar_button("Visualizations", self.style().standardIcon(QStyle.SP_DialogHelpButton))
        history_btn = self.create_sidebar_button("History", self.style().standardIcon(QStyle.SP_BrowserReload))

        # Add buttons to sidebar
        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(dashboard_btn)
        sidebar_layout.addWidget(import_btn)
        sidebar_layout.addWidget(dataview_btn)
        sidebar_layout.addWidget(viz_btn)
        sidebar_layout.addWidget(history_btn)
        sidebar_layout.addStretch()

        # Main content area with scrolling capability
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_area = QFrame()
        content_area.setObjectName("contentArea")
        content_area.setFrameShape(QFrame.NoFrame)
        content_area.setStyleSheet(
            """
            #contentArea {
                background-color: transparent;
                border: none;
            }
        """
        )
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)  # Add padding around content

        scroll_area.setWidget(content_area)

        # Dashboard header
        header_layout = QHBoxLayout()
        dashboard_title = QLabel("Dashboard")
        dashboard_title.setFont(QFont("Arial", 18, QFont.Bold))

        new_viz_btn = QPushButton("+ New Visualization")
        new_viz_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #000000;
                color: white;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """
        )

        # Connect the button to the open_import_data_window method instead of MUedit
        new_viz_btn.clicked.connect(self.open_import_data_window)

        header_layout.addWidget(dashboard_title)
        header_layout.addStretch()
        header_layout.addWidget(new_viz_btn)
        content_layout.addLayout(header_layout)

        # Main grid layout for dashboard content - use vertical layout instead of grid for better resizing
        content_grid = QVBoxLayout()
        content_grid.setSpacing(15)

        # Recent Visualizations section
        viz_section_frame = QFrame()
        viz_section_frame.setObjectName("vizSectionFrame")
        viz_section_frame.setFrameShape(QFrame.StyledPanel)
        viz_section_frame.setMinimumHeight(400)  # Set minimum height
        viz_section_frame.setStyleSheet(
            """
            #vizSectionFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            /* Prevent children from inheriting border */
            #vizSectionFrame > QScrollArea, #vizSectionFrame > QLabel {
                border: none;
                background-color: transparent;
            }
        """
        )
        viz_layout = QVBoxLayout(viz_section_frame)

        viz_title = QLabel("Recent Visualizations")
        viz_title.setFont(QFont("Arial", 12, QFont.Bold))

        # Visualization cards layout
        viz_cards_layout = QHBoxLayout()
        viz_cards_layout.setSpacing(15)

        # Create a scrollable area for visualization cards
        viz_scroll_area = QScrollArea()
        viz_scroll_area.setObjectName("vizScrollArea")
        viz_scroll_area.setWidgetResizable(True)
        viz_scroll_area.setFrameShape(QFrame.NoFrame)
        viz_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viz_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viz_scroll_area.setStyleSheet(
            """
            #vizScrollArea {
                background-color: transparent;
                border: none;
            }
        """
        )

        # Container widget for visualization cards
        viz_container = QWidget()
        viz_container.setObjectName("vizContainer")
        viz_container.setStyleSheet(
            """
            #vizContainer {
                background-color: transparent;
                border: none;
            }
        """
        )
        viz_container_layout = QHBoxLayout(viz_container)
        viz_container_layout.setSpacing(15)
        viz_container_layout.setContentsMargins(0, 0, 0, 0)

        # Add visualization cards dynamically from data
        for idx, viz_data in enumerate(self.recent_visualizations[:3]):  # Limit to first 3 for space
            viz_card = self.create_viz_card(
                viz_data["title"],
                viz_data["date"],
                viz_data["type"],
                viz_data["icon"],
                idx,  # Pass index for unique identifiers
            )
            viz_container_layout.addWidget(viz_card)

        # Add "See All" button if there are more than 3 visualizations
        # if len(self.recent_visualizations) > 3:
        #   see_all_btn = self.create_see_all_button("See All Visualizations")
        #  viz_container_layout.addWidget(see_all_btn)

        viz_container_layout.addStretch()  # Push cards to the left
        viz_scroll_area.setWidget(viz_container)

        viz_layout.addWidget(viz_title)
        viz_layout.addWidget(viz_scroll_area)

        # Quick Actions section
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame")
        actions_frame.setFrameShape(QFrame.StyledPanel)
        actions_frame.setStyleSheet(
            """
            #actionsFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            /* Prevent children from inheriting border */
            #actionsFrame > QPushButton, #actionsFrame > QLabel {
                border: none;
                background-color: transparent;
            }
        """
        )
        actions_layout = QVBoxLayout(actions_frame)

        actions_title = QLabel("Quick Actions")
        actions_title.setFont(QFont("Arial", 12, QFont.Bold))

        # Action buttons with Qt standard icons
        import_dataset_btn = self.create_action_button(
            "Import New Dataset", self.style().standardIcon(QStyle.SP_DialogOpenButton)
        )
        import_dataset_btn.clicked.connect(self.open_import_data_window)  # Connect to open import window
        create_chart_btn = self.create_action_button(
            "Create Chart", self.style().standardIcon(QStyle.SP_DialogHelpButton)
        )
        view_data_btn = self.create_action_button(
            "View Data Table", self.style().standardIcon(QStyle.SP_FileDialogListView)
        )

        actions_layout.addWidget(actions_title)
        actions_layout.addWidget(import_dataset_btn)
        actions_layout.addWidget(create_chart_btn)
        actions_layout.addWidget(view_data_btn)
        actions_layout.addStretch()

        # Recent Datasets section
        datasets_frame = QFrame()
        datasets_frame.setObjectName("datasetsFrame")
        datasets_frame.setFrameShape(QFrame.NoFrame)  # Remove frame
        datasets_frame.setStyleSheet(
            """
            #datasetsFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            /* Prevent children from inheriting styles */
            #datasetsFrame > QLabel {
                background-color: transparent;
            }
        """
        )
        datasets_layout = QVBoxLayout(datasets_frame)

        datasets_title = QLabel("Recent Datasets")
        datasets_title.setFont(QFont("Arial", 12, QFont.Bold))

        # Dataset entries - dynamically create from data
        datasets_layout.addWidget(datasets_title)

        for idx, dataset in enumerate(self.recent_datasets):
            dataset_entry = self.create_dataset_entry(
                dataset["filename"], dataset["metadata"], idx  # Pass index for unique identifiers
            )
            datasets_layout.addWidget(dataset_entry)

        datasets_layout.addStretch()

        # Create top row with visualizations and quick actions side by side
        top_row = QHBoxLayout()
        top_row.addWidget(viz_section_frame, 3)  # Visualization takes 3/4 of width
        top_row.addWidget(actions_frame, 1)  # Actions take 1/4 of width

        # Create layout for datasets section with the same width structure as top row
        bottom_row = QHBoxLayout()

        # Create an empty QFrame to serve as a spacer on the right side
        empty_spacer = QFrame()
        empty_spacer.setObjectName("emptySpacer")
        empty_spacer.setStyleSheet(
            """
            #emptySpacer {
                background-color: transparent;
                border: none;
            }
        """
        )
        empty_spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        bottom_row.addWidget(datasets_frame, 3)  # Match visualization width ratio
        bottom_row.addWidget(empty_spacer, 1)  # Invisible container that takes up space

        # Add to main content layout
        content_grid.addLayout(top_row)
        content_grid.addLayout(bottom_row)

        # Add padding between sections
        content_grid.setContentsMargins(0, 10, 0, 10)
        viz_layout.setContentsMargins(0, 5, 0, 5)
        actions_layout.setContentsMargins(0, 5, 0, 5)
        datasets_layout.setContentsMargins(0, 5, 0, 5)

        content_layout.addLayout(content_grid)

        # Add sidebar and content to main layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(scroll_area, 1)

    def create_sidebar_button(self, text, icon, selected=False):
        btn = QPushButton(text)
        # Create unique object name
        btn.setObjectName(f"sidebarBtn_{text.replace(' ', '_')}")
        btn.setIcon(icon)
        btn.setIconSize(QSize(18, 18))
        btn.setMinimumHeight(40)

        # Left-aligned text with icon
        btn.setStyleSheet(
            f"""
            #{btn.objectName()} {{
                text-align: left;
                padding-left: 15px;
                border: none;
                border-radius: 0;
                font-weight: bold;
                background-color: {"#e6e6e6" if selected else "transparent"};
            }}
            #{btn.objectName()}:hover {{
                background-color: #e6e6e6;
            }}
        """
        )
        return btn

    def create_viz_card(self, title, date, card_type="default", icon_style=None, idx=0):
        # Main card container with unique identifier
        card = QFrame()
        sanitized_title = title.replace(" ", "_").replace(":", "").lower()
        card.setObjectName(f"vizCard_{sanitized_title}_{idx}")
        card.setFrameShape(QFrame.StyledPanel)
        card.setFixedSize(250, 180)
        card.setProperty("title", title)

        # Set card appearance based on type
        if card_type in self.colors:
            bg_color = self.colors.get(f"bg_card_{card_type}", self.colors["bg_card_default"])
        else:
            bg_color = self.colors["bg_card_default"]

        text_color = "white"
        border_color = self.darken_color(bg_color, 20)

        # Main layout
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Icon section (top third) with unique identifier
        icon_section = QFrame(card)
        icon_section.setObjectName(f"iconSection_{sanitized_title}_{idx}")
        icon_section.setStyleSheet(
            f"""
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
        """
        )
        icon_layout = QVBoxLayout(icon_section)
        icon_layout.setContentsMargins(5, 5, 5, 5)

        # Chart icon
        chart_icon = QLabel()
        chart_icon.setObjectName(f"chartIcon_{sanitized_title}_{idx}")
        icon_to_use = icon_style if icon_style is not None else QStyle.SP_FileDialogDetailedView
        chart_icon.setPixmap(self.style().standardIcon(icon_to_use).pixmap(QSize(24, 24)))
        chart_icon.setAlignment(Qt.AlignCenter)
        chart_icon.setStyleSheet(
            f"""
            #{chart_icon.objectName()} {{
                color: {text_color}; 
                background-color: transparent;
                border: none;
            }}
        """
        )
        icon_layout.addWidget(chart_icon)

        # Title section (middle third) with unique identifier
        title_section = QFrame(card)
        title_section.setObjectName(f"titleSection_{sanitized_title}_{idx}")
        title_section.setStyleSheet(
            f"""
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
        """
        )
        title_layout = QVBoxLayout(title_section)
        title_layout.setContentsMargins(5, 5, 5, 5)

        # Title label
        title_label = QLabel(title)
        title_label.setObjectName(f"titleLabel_{sanitized_title}_{idx}")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            f"""
            #{title_label.objectName()} {{
                color: {text_color}; 
                background-color: transparent;
                border: none;
            }}
        """
        )
        title_layout.addWidget(title_label)

        # Date section (bottom third) with unique identifier
        date_section = QFrame(card)
        date_section.setObjectName(f"dateSection_{sanitized_title}_{idx}")
        date_section.setStyleSheet(
            f"""
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
        """
        )
        date_layout = QVBoxLayout(date_section)
        date_layout.setContentsMargins(5, 5, 5, 5)

        # Date label
        date_label = QLabel(date)
        date_label.setObjectName(f"dateLabel_{sanitized_title}_{idx}")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet(
            f"""
            #{date_label.objectName()} {{
                color: {text_color}; 
                font-size: 10px; 
                background-color: transparent;
                border: none;
            }}
        """
        )
        date_layout.addWidget(date_label)

        # Add sections to main layout
        main_layout.addWidget(icon_section)
        main_layout.addWidget(title_section)
        main_layout.addWidget(date_section)

        # Card styling
        card.setStyleSheet(
            f"""
            #{card.objectName()} {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            /* Don't let these styles cascade to children */
            #{card.objectName()} > QLabel {{
                color: {text_color};
                background-color: transparent; 
                border: none;
            }}
            /* Ensure no border inheritance for inner frames */
            #{card.objectName()} > QFrame {{
                border: none; /* Override any inherited border - children must set their own */
            }}
        """
        )

        # Make cards clickable
        card.setCursor(Qt.PointingHandCursor)
        card.mousePressEvent = lambda event: self.open_visualization(title)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(2, 2)
        card.setGraphicsEffect(shadow)

        return card

    def create_action_button(self, text, icon):
        btn = QPushButton(text)
        btn.setObjectName(f"actionBtn_{text.replace(' ', '_')}")
        btn.setIcon(icon)
        btn.setIconSize(QSize(16, 16))
        btn.setMinimumHeight(40)
        btn.setStyleSheet(
            f"""
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
        """
        )
        return btn

    def create_dataset_entry(self, filename, metadata, idx=0):
        sanitized_name = filename.replace(" ", "_").replace(".", "_").lower()
        entry = QFrame()
        entry.setObjectName(f"datasetEntry_{sanitized_name}_{idx}")
        entry.setStyleSheet(
            f"""
            #{entry.objectName()} {{
                background-color: #f2f2f2;
                border-radius: 4px;
                margin-bottom: 5px;
            }}
            /* Prevent style inheritance */
            #{entry.objectName()} QLabel, #{entry.objectName()} QPushButton {{
                background-color: transparent;
                border: none;
            }}
        """
        )
        entry_layout = QHBoxLayout(entry)
        entry_layout.setContentsMargins(12, 12, 12, 12)  # Increased padding

        # File icon (placeholder) with unique identifier
        file_icon = QLabel()
        file_icon.setObjectName(f"fileIcon_{sanitized_name}_{idx}")
        file_icon.setPixmap(self.style().standardIcon(QStyle.SP_FileIcon).pixmap(QSize(16, 16)))

        # File info
        file_info = QVBoxLayout()
        name_label = QLabel(filename)
        name_label.setObjectName(f"nameLabel_{sanitized_name}_{idx}")
        name_label.setFont(QFont("Arial", 10))

        meta_label = QLabel(metadata)
        meta_label.setObjectName(f"metaLabel_{sanitized_name}_{idx}")
        meta_label.setStyleSheet(
            f"""
            #{meta_label.objectName()} {{
                color: #777777; 
                font-size: 10px;
                background-color: transparent;
                border: none;
            }}
        """
        )

        file_info.addWidget(name_label)
        file_info.addWidget(meta_label)

        # Options button with unique identifier
        options_btn = QPushButton("⋮")
        options_btn.setObjectName(f"optionsBtn_{sanitized_name}_{idx}")
        options_btn.setFixedSize(40, 40)  # Set width and height to 40px
        options_btn.setFont(QFont("Arial", 30))  # Increase font size
        options_btn.setStyleSheet(
            f"""
            #{options_btn.objectName()} {{
                background: transparent;
                border: none;
            }}
            #{options_btn.objectName()}:hover {{
                background-color: #e0e0e0;
                border-radius: 20px;
            }}
        """
        )

        entry_layout.addWidget(file_icon)
        entry_layout.addLayout(file_info, 1)
        entry_layout.addWidget(options_btn)

        return entry

    def create_see_all_button(self, text):
        """Create a 'See All' button that looks like a card but serves as a link"""
        btn = QFrame()
        btn.setObjectName("seeAllBtn")
        btn.setFrameShape(QFrame.StyledPanel)
        btn.setStyleSheet(
            """
            #seeAllBtn {
                background-color: #f5f5f5;
                border: 1px dashed #999999;
                border-radius: 8px;
                min-height: 120px;
                min-width: 120px;
            }
            #seeAllBtn:hover {
                background-color: #e6e6e6;
            }
            #seeAllBtn QLabel {
                color: #555555;
                background-color: transparent;
                border: none;
            }
        """
        )

        btn_layout = QVBoxLayout(btn)
        btn_layout.setContentsMargins(10, 10, 10, 10)

        # Add "+" icon
        plus_label = QLabel("+")
        plus_label.setObjectName("plusLabel")
        plus_label.setFont(QFont("Arial", 24))
        plus_label.setAlignment(Qt.AlignCenter)

        # Add text
        text_label = QLabel(text)
        text_label.setObjectName("textLabel")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)

        btn_layout.addStretch()
        btn_layout.addWidget(plus_label)
        btn_layout.addWidget(text_label)
        btn_layout.addStretch()

        # Make clickable
        btn.setCursor(Qt.PointingHandCursor)
        btn.mousePressEvent = lambda event: self.view_all_visualizations()

        return btn

    def view_all_visualizations(self):
        """Handle 'See All' button click"""
        print("Opening all visualizations view")
        # In a real app, you would open a new window or change the current view

    def darken_color(self, hex_color, amount=30):
        """Utility function to darken a hex color"""
        # Remove the # if present
        hex_color = hex_color.lstrip("#")

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Darken
        r = max(0, r - amount)
        g = max(0, g - amount)
        b = max(0, b - amount)

        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def open_visualization(self, title):
        """Handle card click events - would open the specific visualization"""
        print(f"Opening visualization: {title}")
        # In a real app, you would load the visualization based on its title or ID

    def open_import_data_window(self):
        """Open the import data window when import button is clicked"""
        print("Opening import data window")
        self.import_window = ImportDataWindow(parent=self)
        self.import_window.show()

    def open_muedit_window(self):
        """Open the MUedit window (kept for reference but no longer used)"""
        print("Opening MUedit window")
        self.muedit_window = MUedit()
        self.muedit_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HDEMGDashboard()
    window.show()
    sys.exit(app.exec_())