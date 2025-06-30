from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QLineEdit, QCheckBox, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.components.CleanTheme import CleanTheme


class MotorUnitTrackingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Motor Unit Tracking")
        self.setMinimumWidth(500)
        self.setStyleSheet(self._get_stylesheet())
        self.setWindowModality(Qt.ApplicationModal)
        self.file1_path = None
        self.file2_path = None
        self.init_ui()


    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)


        title = QLabel("Motor Unit Tracking")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)


        # Load File 1
        file1_layout = QHBoxLayout()
        load_file1_btn = QPushButton("Load File 1")
        load_file1_btn.clicked.connect(self.load_file1)
        self.file1_label = QLabel("No file selected")
        self.file1_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file1_layout.addWidget(load_file1_btn)
        file1_layout.addWidget(self.file1_label)
        layout.addLayout(file1_layout)


        # Load File 2
        file2_layout = QHBoxLayout()
        load_file2_btn = QPushButton("Load File 2")
        load_file2_btn.clicked.connect(self.load_file2)
        self.file2_label = QLabel("No file selected")
        self.file2_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file2_layout.addWidget(load_file2_btn)
        file2_layout.addWidget(self.file2_label)
        layout.addLayout(file2_layout)


        # Threshold input
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Threshold:")
        self.threshold_input = QLineEdit()
        self.threshold_input.setPlaceholderText("e.g. 0.8")
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_input)
        layout.addLayout(threshold_layout)


        # Time window input
        time_window_layout = QHBoxLayout()
        time_window_label = QLabel("Time Window:")
        self.time_window_input = QLineEdit()
        self.time_window_input.setPlaceholderText("e.g. 100ms")
        time_window_layout.addWidget(time_window_label)
        time_window_layout.addWidget(self.time_window_input)
        layout.addLayout(time_window_layout)


        # Checkboxes
        self.filter_checkbox = QCheckBox("Apply Filter")
        self.exclude_checkbox = QCheckBox("Exclude Below Threshold")
        layout.addWidget(self.filter_checkbox)
        layout.addWidget(self.exclude_checkbox)


        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))


        # Track button
        track_btn = QPushButton("Track")
        track_btn.setFixedHeight(40)
        track_btn.clicked.connect(self.on_track)
        layout.addWidget(track_btn)


        self.setLayout(layout)


    def load_file1(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File 1", "", "MAT Files (*.mat)")
        if file_path:
            self.file1_path = file_path
            self.file1_label.setText(file_path.split("/")[-1])


    def load_file2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File 2", "", "MAT Files (*.mat)")
        if file_path:
            self.file2_path = file_path
            self.file2_label.setText(file_path.split("/")[-1])


    def on_track(self):
        if not self.file1_path or not self.file2_path:
            QMessageBox.critical(self, "Invalid Inputs", "Both files must be selected.")
            return


        try:
            threshold = float(self.threshold_input.text())
            time_window = float(self.time_window_input.text())
        except ValueError:
            QMessageBox.critical(self, "Invalid Inputs", "Threshold and Time Window must be numeric.")
            return


        QMessageBox.information(self, "Tracking", "Tracking MUs...\n(You would now show the results UI here)")


    def _get_stylesheet(self):
        return f"""
        QDialog {{
            background-color: {CleanTheme.ANALYSIS_BG_CARD};
        }}
        QLabel {{
            font-size: 12px;
            color: {CleanTheme.TEXT_PRIMARY};
        }}
        QLineEdit {{
            background-color: #ffffff;
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 4px;
            padding: 6px;
        }}
        QCheckBox {{
            font-size: 12px;
        }}
        QPushButton {{
            background-color: {CleanTheme.ANALYSIS_BG_BUTTON};
            color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton:hover {{
            background-color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
            color: {CleanTheme.ANALYSIS_BG_BUTTON};
        }}
        """


