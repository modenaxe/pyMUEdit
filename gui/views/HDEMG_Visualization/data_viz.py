import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QComboBox, QCheckBox, QLineEdit, QToolButton, 
    QFrame, QGridLayout, QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont


class HDEMGVisualizationInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Visualization Interface")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up the main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create the title and navigation bar
        title_layout = self.create_title_bar()
        main_layout.addLayout(title_layout)
        
        # Create the main content area
        content_layout = QHBoxLayout()
        
        # Left sidebar for settings
        left_sidebar = self.create_left_sidebar()
        content_layout.addWidget(left_sidebar)
        
        # Main visualization area
        visualization_area = self.create_visualization_area()
        content_layout.addWidget(visualization_area, 1)  # 1 = stretch factor
        
        main_layout.addLayout(content_layout)
        
    def create_title_bar(self):
        title_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Data Visualization Interface")
        title_label.setFont(QFont("Arial", 14))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)  # Push everything to sides
        
        # Navigation buttons
        prev_button = QPushButton("← Previous")
        prev_button.setFixedWidth(100)
        
        next_button = QPushButton("Next →")
        next_button.setFixedWidth(100)
        next_button.setStyleSheet("background-color: #222; color: white;")
        
        title_layout.addWidget(prev_button)
        title_layout.addWidget(next_button)
        
        return title_layout
    
    def create_left_sidebar(self):
        sidebar_widget = QWidget()
        sidebar_widget.setMaximumWidth(250)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # Recording Settings
        recording_label = QLabel("Recording Settings")
        recording_label.setFont(QFont("Arial", 10, QFont.Bold))
        sidebar_layout.addWidget(recording_label)
        
        # Grid Selection
        grid_label = QLabel("Grid Selection")
        sidebar_layout.addWidget(grid_label)
        
        muscle_label = QLabel("Muscle names")
        
        grid_muscle_layout = QHBoxLayout()
        grid_muscle_layout.addWidget(grid_label)
        grid_muscle_layout.addWidget(muscle_label)
        sidebar_layout.addLayout(grid_muscle_layout)
        
        # Grid 1
        grid1_layout = QHBoxLayout()
        grid1_checkbox = QCheckBox("Grid #1")
        grid1_checkbox.setChecked(True)
        grid1_text = QLineEdit("TA")
        
        grid1_layout.addWidget(grid1_checkbox)
        grid1_layout.addWidget(grid1_text)
        sidebar_layout.addLayout(grid1_layout)
        
        # Grid 2
        grid2_layout = QHBoxLayout()
        grid2_checkbox = QCheckBox("Grid #2")
        grid2_text = QLineEdit()
        
        grid2_layout.addWidget(grid2_checkbox)
        grid2_layout.addWidget(grid2_text)
        sidebar_layout.addLayout(grid2_layout)
        
        # Grid 3
        grid3_layout = QHBoxLayout()
        grid3_checkbox = QCheckBox("Grid #3")
        grid3_text = QLineEdit()
        
        grid3_layout.addWidget(grid3_checkbox)
        grid3_layout.addWidget(grid3_text)
        sidebar_layout.addLayout(grid3_layout)
        
        # Frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency")
        freq_combo = QComboBox()
        freq_combo.addItem("500 Hz")
        freq_combo.addItem("1000 Hz")
        freq_combo.addItem("2000 Hz")
        
        sidebar_layout.addWidget(freq_label)
        sidebar_layout.addWidget(freq_combo)
        
        # HP Filter
        hp_layout = QHBoxLayout()
        hp_label = QLabel("HP Filter")
        hp_combo = QComboBox()
        hp_combo.addItem("10 Hz")
        hp_combo.addItem("20 Hz")
        hp_combo.addItem("30 Hz")
        
        sidebar_layout.addWidget(hp_label)
        sidebar_layout.addWidget(hp_combo)
        
        # LP Filter
        lp_layout = QHBoxLayout()
        lp_label = QLabel("LP Filter")
        lp_combo = QComboBox()
        lp_combo.addItem("450 Hz")
        lp_combo.addItem("500 Hz")
        lp_combo.addItem("550 Hz")
        
        sidebar_layout.addWidget(lp_label)
        sidebar_layout.addWidget(lp_combo)
        
        # Refresh Rate
        refresh_layout = QHBoxLayout()
        refresh_label = QLabel("Refresh Rate")
        refresh_combo = QComboBox()
        refresh_combo.addItem("30 fps")
        refresh_combo.addItem("60 fps")
        refresh_combo.addItem("120 fps")
        
        sidebar_layout.addWidget(refresh_label)
        sidebar_layout.addWidget(refresh_combo)
        
        # Saving Settings
        saving_label = QLabel("Saving Settings")
        saving_label.setFont(QFont("Arial", 10, QFont.Bold))
        sidebar_layout.addWidget(saving_label)
        
        # Select Folder
        folder_button = QPushButton("Select Folder")
        folder_button.setIcon(QIcon.fromTheme("folder-open"))
        sidebar_layout.addWidget(folder_button)
        
        # Export Button
        export_button = QPushButton("Export")
        export_button.setIcon(QIcon.fromTheme("document-save"))
        sidebar_layout.addWidget(export_button)
        
        # Start Visualization buttons
        start_noise_button = QPushButton("Start Visualization - Check Noise")
        start_noise_button.setStyleSheet("background-color: #1b6e41; color: white;")
        sidebar_layout.addWidget(start_noise_button)
        
        start_emg_button = QPushButton("Start Visualization - Check EMG")
        start_emg_button.setStyleSheet("background-color: #1e2d7a; color: white;")
        sidebar_layout.addWidget(start_emg_button)
        
        sidebar_layout.addStretch(1)  # Push everything up
        
        return sidebar_widget
    
    def create_visualization_area(self):
        viz_widget = QWidget()
        viz_layout = QVBoxLayout(viz_widget)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Channel dropdown
        channel_layout = QHBoxLayout()
        channel_label = QLabel("Show All Channels")
        channel_dropdown = QComboBox()
        channel_dropdown.addItem("Show All Channels")
        channel_dropdown.addItem("Show Selected Channels")
        
        control_layout.addWidget(channel_label)
        control_layout.addWidget(channel_dropdown)
        
        # Channel Groups
        groups_label = QLabel("Channel Groups:")
        control_layout.addWidget(groups_label)
        
        # Channel buttons
        btn_1_10 = QPushButton("1-10")
        btn_11_20 = QPushButton("11-20")
        btn_21_30 = QPushButton("21-30")
        
        control_layout.addWidget(btn_1_10)
        control_layout.addWidget(btn_11_20)
        control_layout.addWidget(btn_21_30)
        
        # Zoom buttons
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(30, 30)
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(30, 30)
        
        control_layout.addWidget(zoom_in_btn)
        control_layout.addWidget(zoom_out_btn)
        
        control_layout.addStretch(1)  # Push to left
        
        # Initialize and Disconnect buttons
        init_button = QPushButton("Initialize Quattrocento")
        init_button.setStyleSheet("background-color: #c4be18; color: black;")
        
        disconnect_button = QPushButton("Disconnect Quattrocento")
        disconnect_button.setStyleSheet("background-color: #c22c32; color: white;")
        
        control_layout.addWidget(init_button)
        control_layout.addWidget(disconnect_button)
        
        viz_layout.addLayout(control_layout)
        
        # Visualization canvas (placeholder with a frame)
        canvas = QFrame()
        canvas.setFrameShape(QFrame.StyledPanel)
        canvas.setStyleSheet("background-color: #e5e5e5;")
        canvas.setMinimumHeight(500)
        
        viz_layout.addWidget(canvas)
        
        return viz_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HDEMGVisualizationInterface()
    window.show()
    sys.exit(app.exec_())