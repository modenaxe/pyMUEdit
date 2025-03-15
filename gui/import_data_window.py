import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFrame, QFileDialog,
                            QSizePolicy, QSpacerItem, QToolButton, QMenu, QAction)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QSize, QRect, QPoint

class ImportDataWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle("HDEMG Analysis")
        self.resize(1200, 800)
        
        # Define color scheme
        self.colors = {
            'bg_main': '#ffffff',
            'bg_sidebar': '#f8f8f8',
            'bg_dropzone': '#f8f8f8',
            'text_primary': '#333333',
            'text_secondary': '#777777',
            'border': '#e0e0e0',
            'accent': '#000000',
            'button_bg': '#222222',
            'button_text': '#ffffff'
        }
        
        # Sample data - in a real app, this would be loaded dynamically
        self.recent_files = [
            "HDEMG_data_001.csv",
            "HDEMG_data_002.csv",
            "HDEMG_data_003.csv"
        ]
        
        # Set up main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create header
        self.create_header()
        
        # Create main content area
        self.create_content_area()
        
        # Create footer
        self.create_footer()
    
    def create_header(self):
        """Create the header with title and menu options"""
        header = QFrame()
        header.setObjectName("header")
        header.setFrameShape(QFrame.NoFrame)
        header.setStyleSheet(f"""
            #header {{
                background-color: {self.colors['bg_main']};
                border-bottom: 1px solid {self.colors['border']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(self.style().standardIcon(self.style().SP_FileDialogDetailedView).pixmap(QSize(24, 24)))
        
        title_label = QLabel("HDEMG Analysis")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Menu buttons
        file_btn = QPushButton("File")
        file_btn.setObjectName("menuButton")
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("menuButton")
        view_btn = QPushButton("View")
        view_btn.setObjectName("menuButton")
        help_btn = QPushButton("Help")
        help_btn.setObjectName("menuButton")
        
        # Apply styling to menu buttons
        for btn in [file_btn, edit_btn, view_btn, help_btn]:
            btn.setStyleSheet("""
                #menuButton {
                    background: transparent;
                    border: none;
                    padding: 8px 12px;
                    font-size: 14px;
                }
                #menuButton:hover {
                    background-color: #f0f0f0;
                }
            """)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)
        header_layout.addWidget(file_btn)
        header_layout.addWidget(edit_btn)
        header_layout.addWidget(view_btn)
        header_layout.addWidget(help_btn)
        
        self.main_layout.addWidget(header)
    
    def create_content_area(self):
        """Create the main content area with sidebar and dropzone"""
        content_container = QFrame()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet(f"""
            #contentContainer {{
                background-color: {self.colors['bg_main']};
                border: none;
            }}
        """)
        
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Create sidebar
        self.create_sidebar(content_layout)
        
        # Create right panel with dropzone and preview
        self.create_right_panel(content_layout)
        
        self.main_layout.addWidget(content_container, 1)  # 1 means this widget takes available space
    
    def create_sidebar(self, parent_layout):
        """Create the left sidebar with import button and recent files"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"""
            #sidebar {{
                background-color: {self.colors['bg_sidebar']};
                border-right: 1px solid {self.colors['border']};
            }}
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)
        
        # Import File button
        import_btn = QPushButton("  Import File")
        import_btn.setObjectName("importButton")
        import_btn.setIcon(self.style().standardIcon(self.style().SP_DialogOpenButton))
        import_btn.setIconSize(QSize(16, 16))
        import_btn.setMinimumHeight(40)
        import_btn.setStyleSheet(f"""
            #importButton {{
                background-color: {self.colors['button_bg']};
                color: {self.colors['button_text']};
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                text-align: left;
            }}
            #importButton:hover {{
                background-color: #444444;
            }}
        """)
        
        # Recent Files label
        recent_label = QLabel("Recent Files")
        recent_label.setFont(QFont("Arial", 12, QFont.Bold))
        recent_label.setContentsMargins(0, 10, 0, 0)
        
        # Add widgets to sidebar
        sidebar_layout.addWidget(import_btn)
        sidebar_layout.addWidget(recent_label)
        
        # Recent files list
        for file in self.recent_files:
            file_item = self.create_file_item(file)
            sidebar_layout.addWidget(file_item)
        
        sidebar_layout.addStretch(1)
        
        # Add expand/collapse button at bottom
        expand_btn = QToolButton()
        expand_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        expand_btn.setIconSize(QSize(16, 16))
        expand_btn.setFixedSize(32, 32)
        expand_btn.setStyleSheet("""
            QToolButton {
                background-color: #e0e0e0;
                border: none;
                border-radius: 16px;
            }
            QToolButton:hover {
                background-color: #d0d0d0;
            }
        """)
        
        sidebar_layout.addWidget(expand_btn, 0, Qt.AlignHCenter)
        
        parent_layout.addWidget(sidebar)
    
    def create_file_item(self, filename):
        """Create a file item for the recent files list"""
        item = QFrame()
        item.setObjectName(f"fileItem_{filename.replace('.', '_')}")
        item.setMinimumHeight(40)
        item.setStyleSheet(f"""
            #fileItem_{filename.replace('.', '_')} {{
                background-color: transparent;
                border-radius: 4px;
            }}
            #fileItem_{filename.replace('.', '_')}:hover {{
                background-color: #f0f0f0;
            }}
        """)
        
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(10, 5, 10, 5)
        
        # File icon
        file_icon = QLabel()
        file_icon.setPixmap(self.style().standardIcon(self.style().SP_FileIcon).pixmap(QSize(16, 16)))
        
        # Filename
        file_label = QLabel(filename)
        
        item_layout.addWidget(file_icon)
        item_layout.addWidget(file_label)
        item_layout.addStretch()
        
        return item
    
    def create_right_panel(self, parent_layout):
        """Create the right panel with dropzone and preview"""
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_panel.setStyleSheet(f"""
            #rightPanel {{
                background-color: {self.colors['bg_main']};
                border: none;
            }}
        """)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)
        
        # Create dropzone
        dropzone = self.create_dropzone()
        
        # Create Signal Preview section
        preview_label = QLabel("Signal Preview")
        preview_label.setFont(QFont("Arial", 14))
        preview_label.setContentsMargins(0, 10, 0, 10)
        
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_frame.setMinimumHeight(300)
        preview_frame.setStyleSheet(f"""
            #previewFrame {{
                background-color: #f0f0f0;
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
            }}
        """)
        
        # Add widgets to right panel
        right_layout.addWidget(dropzone)
        right_layout.addWidget(preview_label)
        right_layout.addWidget(preview_frame)
        
        parent_layout.addWidget(right_panel, 1)  # 1 means this widget takes available space
    
    def create_dropzone(self):
        """Create a dropzone for files"""
        dropzone = QFrame()
        dropzone.setObjectName("dropzone")
        dropzone.setMinimumHeight(200)
        dropzone.setStyleSheet(f"""
            #dropzone {{
                background-color: {self.colors['bg_dropzone']};
                border: 2px dashed {self.colors['border']};
                border-radius: 8px;
            }}
        """)
        
        dropzone_layout = QVBoxLayout(dropzone)
        
        # Cloud icon
        cloud_icon = QLabel()
        cloud_icon_pixmap = self.style().standardIcon(self.style().SP_DriveNetIcon).pixmap(QSize(48, 48))
        cloud_icon.setPixmap(cloud_icon_pixmap)
        cloud_icon.setAlignment(Qt.AlignCenter)
        
        # Text
        drag_label = QLabel("Drag and drop your HDEMG files here")
        drag_label.setAlignment(Qt.AlignCenter)
        drag_label.setFont(QFont("Arial", 12))
        
        or_label = QLabel("or")
        or_label.setAlignment(Qt.AlignCenter)
        
        # Browse button
        browse_btn = QPushButton("Browse Files")
        browse_btn.setObjectName("browseButton")
        browse_btn.setFixedWidth(150)
        browse_btn.setStyleSheet(f"""
            #browseButton {{
                background-color: #e0e0e0;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            #browseButton:hover {{
                background-color: #d0d0d0;
            }}
        """)
        
        # Add widgets to dropzone
        dropzone_layout.addStretch()
        dropzone_layout.addWidget(cloud_icon)
        dropzone_layout.addWidget(drag_label)
        dropzone_layout.addWidget(or_label)
        dropzone_layout.addWidget(browse_btn, 0, Qt.AlignCenter)
        dropzone_layout.addStretch()
        
        return dropzone
    
    def create_footer(self):
        """Create footer with file info and navigation"""
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFrameShape(QFrame.NoFrame)
        footer.setStyleSheet(f"""
            #footer {{
                background-color: {self.colors['bg_main']};
                border-top: 1px solid {self.colors['border']};
            }}
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        
        # File info
        file_info = QLabel("File: HDEMG_data_001.csv")
        
        # Center spacer
        footer_layout.addWidget(file_info)
        footer_layout.addStretch(1)
        
        # File size info
        size_info = QLabel("Size: 2.4 MB")
        footer_layout.addWidget(size_info)
        
        # Format info
        format_info = QLabel("Format: CSV")
        footer_layout.addWidget(format_info)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        prev_btn = QPushButton("← Previous")
        prev_btn.setObjectName("navButton")
        
        next_btn = QPushButton("Next →")
        next_btn.setObjectName("navButton")
        
        # Apply styling to nav buttons
        for btn in [prev_btn, next_btn]:
            btn.setMinimumWidth(120)
            btn.setStyleSheet(f"""
                #navButton {{
                    background-color: {self.colors['button_bg']};
                    color: {self.colors['button_text']};
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                #navButton:hover {{
                    background-color: #444444;
                }}
            """)
        
        nav_layout.addWidget(prev_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(next_btn)
        
        footer_layout.addLayout(nav_layout)
        
        self.main_layout.addWidget(footer)


# For testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportDataWindow()
    window.show()
    sys.exit(app.exec_())