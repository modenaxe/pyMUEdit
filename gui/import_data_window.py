import sys
import os
import shutil
import tarfile
import numpy as np
import scipy.io as sio
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFrame, QFileDialog,
                            QSizePolicy, QSpacerItem, QToolButton, QMenu, QAction)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal

# Add necessary paths to the system path
current_dir = os.path.dirname(os.path.abspath(__file__))  # gui folder
project_root = os.path.dirname(current_dir)  # project root
sys.path.append(project_root)
sys.path.append(current_dir)

# Import needed functions from other modules
from utils.config_and_input.openOTBplus import openOTBplus
from SaveMatWorker import SaveMatWorker

# Import our navigator module (create an empty file first if it doesn't exist)
try:
    import navigator
except ImportError:
    # If navigator.py doesn't exist yet, create it
    with open(os.path.join(current_dir, 'navigator.py'), 'w') as f:
        f.write('"""Navigator module placeholder"""')
    import navigator

class ImportDataWindow(QMainWindow):
    # Signal to notify other windows when a file is imported
    fileImported = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle("HDEMG Analysis - Import Data")
        self.resize(1200, 800)
        
        # Initialize variables for file loading
        self.filename = None
        self.pathname = None
        self.imported_signal = None  # Will store the imported signal data
        self.threads = []  # Keep reference to worker threads
        
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
        
        title_label = QLabel("HDEMG Analysis - Import Data")
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
        import_btn.clicked.connect(self.select_file)  # Connect to file selection function
        
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
        
        # Make item clickable
        item.setCursor(Qt.PointingHandCursor)
        item.mousePressEvent = lambda event: self.load_recent_file(filename)
        
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
        self.dropzone = self.create_dropzone()
        
        # Create Signal Preview section
        preview_label = QLabel("Signal Preview")
        preview_label.setFont(QFont("Arial", 14))
        preview_label.setContentsMargins(0, 10, 0, 10)
        
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("previewFrame")
        self.preview_frame.setMinimumHeight(300)
        self.preview_frame.setStyleSheet(f"""
            #previewFrame {{
                background-color: #f0f0f0;
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
            }}
        """)
        
        # Create a preview message label
        self.preview_message = QLabel("No file selected. Import a file to see a preview.")
        self.preview_message.setAlignment(Qt.AlignCenter)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.addWidget(self.preview_message)
        
        # Add widgets to right panel
        right_layout.addWidget(self.dropzone)
        right_layout.addWidget(preview_label)
        right_layout.addWidget(self.preview_frame)
        
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
        
        # File info
        self.file_info_label = QLabel("")
        self.file_info_label.setAlignment(Qt.AlignCenter)
        self.file_info_label.setFont(QFont("Arial", 11))
        self.file_info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.file_info_label.setVisible(False)
        
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
        browse_btn.clicked.connect(self.select_file)  # Connect to file selection function
        
        # Add widgets to dropzone
        dropzone_layout.addStretch()
        dropzone_layout.addWidget(cloud_icon)
        dropzone_layout.addWidget(drag_label)
        dropzone_layout.addWidget(self.file_info_label)
        dropzone_layout.addWidget(or_label)
        dropzone_layout.addWidget(browse_btn, 0, Qt.AlignCenter)
        dropzone_layout.addStretch()
        
        # Set up file drag and drop
        dropzone.setAcceptDrops(True)
        dropzone.dragEnterEvent = self.dragEnterEvent
        dropzone.dropEvent = self.dropEvent
        
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
        self.footer_file_info = QLabel("No file selected")
        
        # Center spacer
        footer_layout.addWidget(self.footer_file_info)
        footer_layout.addStretch(1)
        
        # File size info
        self.size_info = QLabel("Size: --")
        footer_layout.addWidget(self.size_info)
        
        # Format info
        self.format_info = QLabel("Format: --")
        footer_layout.addWidget(self.format_info)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        prev_btn = QPushButton("← Previous")
        prev_btn.setObjectName("navButton")
        prev_btn.clicked.connect(self.go_back)
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.setObjectName("navButton")
        self.next_btn.clicked.connect(self.go_to_algorithm_screen)
        self.next_btn.setEnabled(False)  # Disabled until file is selected
        
        # Apply styling to nav buttons
        for btn in [prev_btn, self.next_btn]:
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
                #navButton:disabled {{
                    background-color: #777777;
                    color: #aaaaaa;
                }}
            """)
        
        nav_layout.addWidget(prev_btn)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.next_btn)
        
        footer_layout.addLayout(nav_layout)
        
        self.main_layout.addWidget(footer)

    # File loading functionality
    def select_file(self):
        """Open file dialog to select a file"""
        file, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All Files (*.*)")
        if not file:
            return
            
        self.filename = os.path.basename(file)
        self.pathname = os.path.dirname(file) + "/"
        
        # Update UI to show selected file
        self.file_info_label.setText(f"Selected: {self.filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {self.filename}")
        
        # Get file size and format
        file_size = os.path.getsize(file)
        file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/(1024*1024):.1f} MB"
            
        self.size_info.setText(f"Size: {size_str}")
        self.format_info.setText(f"Format: {file_format}")
        
        # Load the file
        self.load_file(self.pathname, self.filename)
    
    def load_recent_file(self, filename):
        """Load a file from the recent files list"""
        # In a real app, this would look up the path for the filename
        # For this example, just simulate selecting the file
        self.filename = filename
        self.pathname = "./"  # Default directory
        
        # Update UI
        self.file_info_label.setText(f"Selected: {self.filename}")
        self.file_info_label.setVisible(True)
        self.footer_file_info.setText(f"File: {self.filename}")
        self.size_info.setText("Size: 2.4 MB")  # Example size
        self.format_info.setText(f"Format: {os.path.splitext(filename)[1].upper().replace('.', '')}")
        
        # Load the file 
        # Note: Since we don't have actual files, this would fail in practice
        # self.load_file(self.pathname, self.filename)
        
        # Simulate successful load for demo purposes
        self.preview_message.setText(f"Preview of {filename}\n(Simulated data for demonstration)")
        self.next_btn.setEnabled(True)
    
    def load_file(self, path, file):
        """Load the selected file"""
        # Update the preview message while loading
        self.preview_message.setText("Loading file...")
        
        # Check file extension to determine how to load it
        ext = os.path.splitext(file)[1].lower()
        
        # Handle OTB+ files (using the function from openOTBplus.py)
        if ext == ".otb+":
            try:
                config, signal, savename = openOTBplus(path, file, 0)  # Pass 0 to not show dialog
                
                if savename:
                    # Save the file in background for later use
                    self.save_mat_in_background(savename, {"signal": signal}, True)
                
                # Store the signal data for later use
                self.imported_signal = signal
                
                # Update preview
                self.preview_message.setText(f"Successfully loaded {file}\nFile contains EMG data with {signal['data'].shape[0]} channels")
                
                # Enable next button
                self.next_btn.setEnabled(True)
                
            except Exception as e:
                self.preview_message.setText(f"Error loading file: {str(e)}")
                print(f"Error loading OTB+ file: {e}")
                self.next_btn.setEnabled(False)
        else:
            # For other file types, show message that only OTB+ is supported in this demo
            self.preview_message.setText(f"File type {ext} not supported in this demo.\nPlease select an OTB+ file.")
            self.next_btn.setEnabled(False)
    
    def save_mat_in_background(self, filename, data, compression=True):
        """Save a MATLAB .mat file in a background thread"""
        # Create and configure the worker thread
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)

        worker.finished.connect(lambda: self.on_save_finished(worker))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))

        worker.start()

    def on_save_finished(self, worker):
        """Handle successful save"""
        print("Data saved successfully")
        self.cleanup_thread(worker)

    def on_save_error(self, worker, error_msg):
        """Handle save error"""
        print(f"Error saving data: {error_msg}")
        self.cleanup_thread(worker)

    def cleanup_thread(self, worker):
        """Remove the worker from the threads list"""
        if worker in self.threads:
            self.threads.remove(worker)
    
    # Navigation functions
    def go_back(self):
        """Go back to previous screen"""
        self.close()  # Close this window
    
    def go_to_algorithm_screen(self):
        """Navigate to algorithm selection screen"""
        if not self.filename or not self.imported_signal:
            return  # Shouldn't happen since the button is disabled
        
        try:
            # Save the signal data for the algorithm window to load
            savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
            self.save_mat_in_background(savename, {"signal": self.imported_signal}, True)
            
            # Import from the file with hyphens, which is the real implementation
            import importlib.util
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    'views', 'Algorithm_Selection_Decomposition', 'algo-select-screen.py')
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return
                
            print(f"Loading algorithm screen from: {file_path}")
            spec = importlib.util.spec_from_file_location("decomp_app", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            DecompositionApp = module.DecompositionApp
            
            # Create the algorithm window
            self.algo_window = DecompositionApp()
            
            # Add the missing method to allow initializing properly
            def select_file_button_pushed(self_inner):
                file, _ = QFileDialog.getOpenFileName(self_inner, "Select file", "", "All Files (*.*)")
                if not file:
                    return
                self_inner.filename = os.path.basename(file)
                self_inner.pathname = os.path.dirname(file) + "/"
                self_inner.edit_field_saving_3.setText(self_inner.filename)
            
            # Attach the method to the instance
            from types import MethodType
            self.algo_window.select_file_button_pushed = MethodType(select_file_button_pushed, self.algo_window)
            
            # Now handle the rest of the setup...
            self.algo_window.filename = self.filename
            self.algo_window.pathname = self.pathname
            self.algo_window.edit_field_saving_3.setText(self.filename)
            
            # Update reference dropdown
            self.algo_window.reference_dropdown.blockSignals(True)
            self.algo_window.reference_dropdown.clear()
            
            if "auxiliaryname" in self.imported_signal:
                self.algo_window.reference_dropdown.addItem("EMG amplitude")
                for name in self.imported_signal["auxiliaryname"]:
                    self.algo_window.reference_dropdown.addItem(str(name))
            elif "target" in self.imported_signal:
                self.algo_window.reference_dropdown.addItem("EMG amplitude")
                self.algo_window.reference_dropdown.addItem("Path")
                self.algo_window.reference_dropdown.addItem("Target")
            else:
                self.algo_window.reference_dropdown.addItem("EMG amplitude")
            
            self.algo_window.reference_dropdown.blockSignals(False)
            
            if hasattr(self.algo_window, 'set_configuration_button'):
                self.algo_window.set_configuration_button.setEnabled(True)
            
            # Show the window and close this one
            self.algo_window.show()
            self.close()
            
        except Exception as e:
            print(f"Error opening algorithm screen: {e}")
            import traceback
            traceback.print_exc()
    
    # Event handling for drag and drop
    def dragEnterEvent(self, event):
        """Handle drag enter events for the dropzone"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events for the dropzone"""
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            
            # Check if it's a file
            if os.path.isfile(file_path):
                self.filename = os.path.basename(file_path)
                self.pathname = os.path.dirname(file_path) + "/"
                
                # Update UI
                self.file_info_label.setText(f"Selected: {self.filename}")
                self.file_info_label.setVisible(True)
                self.footer_file_info.setText(f"File: {self.filename}")
                
                # Get file size and format
                file_size = os.path.getsize(file_path)
                file_format = os.path.splitext(self.filename)[1].upper().replace(".", "")
                
                # Format file size
                if file_size < 1024:
                    size_str = f"{file_size} bytes"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"
                    
                self.size_info.setText(f"Size: {size_str}")
                self.format_info.setText(f"Format: {file_format}")
                
                # Load the file
                self.load_file(self.pathname, self.filename)


# For testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportDataWindow()
    window.show()
    sys.exit(app.exec_())