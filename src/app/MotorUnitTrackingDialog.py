from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QLineEdit, QCheckBox, QMessageBox, QSpacerItem, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.components.CleanTheme import CleanTheme
import numpy as np
from scipy.spatial.distance import cosine
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from scipy.io import loadmat
import pandas as pd
from app.FileUploadFunc import FileUploadFunc

def load_otb_data(filepath):
    file_handler = FileUploadFunc()
    success = file_handler.emg_from_otb(filepath)
    if not success:
        raise ValueError("Failed to load .mat file using OpenHDEMG loader")
    return FileUploadFunc.file

class MotorUnitTrackingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Motor Unit Tracking")
        self.setMinimumWidth(900)
        self.setStyleSheet(self._get_stylesheet())
        self.setWindowModality(Qt.ApplicationModal)
        self.file1 = None
        self.file2 = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Motor Unit Tracking")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        file1_layout = QHBoxLayout()
        load_file1_btn = QPushButton("Load File 1")
        load_file1_btn.clicked.connect(self.load_file1)
        self.file1_label = QLabel("No file selected")
        self.file1_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file1_layout.addWidget(load_file1_btn)
        file1_layout.addWidget(self.file1_label)
        layout.addLayout(file1_layout)

        file2_layout = QHBoxLayout()
        load_file2_btn = QPushButton("Load File 2")
        load_file2_btn.clicked.connect(self.load_file2)
        self.file2_label = QLabel("No file selected")
        self.file2_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file2_layout.addWidget(load_file2_btn)
        file2_layout.addWidget(self.file2_label)
        layout.addLayout(file2_layout)

        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Threshold:")
        self.threshold_input = QLineEdit("0.5")
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_input)
        layout.addLayout(threshold_layout)

        window_layout = QHBoxLayout()
        window_label = QLabel("Time Window (ms):")
        self.window_input = QLineEdit("50")
        window_layout.addWidget(window_label)
        window_layout.addWidget(self.window_input)
        layout.addLayout(window_layout)

        self.filter_checkbox = QCheckBox("Apply Filter")
        self.exclude_checkbox = QCheckBox("Exclude Below Threshold")
        layout.addWidget(self.filter_checkbox)
        layout.addWidget(self.exclude_checkbox)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        track_btn = QPushButton("Track")
        track_btn.setFixedHeight(40)
        track_btn.clicked.connect(self.on_track)
        layout.addWidget(track_btn)

        results_layout = QHBoxLayout()

        self.fig1, self.ax1 = plt.subplots()
        self.canvas1 = FigureCanvas(self.fig1)

        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvas(self.fig2)

        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.canvas1)
        plot_layout.addWidget(self.canvas2)

        results_layout.addLayout(plot_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Channel_File1", "Channel_File2", "Correlation"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        results_layout.addWidget(self.table)
        layout.addLayout(results_layout)

        self.setLayout(layout)

    def load_file1(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File 1", "", "MAT Files (*.mat)")
        if file_path:
            self.file1_label.setText(os.path.basename(file_path))
            try:
                self.file1 = load_otb_data(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load File 1:\n{str(e)}")

    def load_file2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File 2", "", "MAT Files (*.mat)")
        if file_path:
            self.file2_label.setText(os.path.basename(file_path))
            try:
                self.file2 = load_otb_data(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load File 2:\n{str(e)}")

    def on_track(self):
        if self.file1 is None or self.file2 is None:
            QMessageBox.critical(self, "Invalid Inputs", "Both files must be selected.")
            return

        try:
            threshold = float(self.threshold_input.text())
            time_window_ms = int(self.window_input.text())
            samples_window = int((time_window_ms / 1000.0) * self.file1["FSAMP"])
        except ValueError:
            QMessageBox.critical(self, "Invalid Inputs", "Threshold and Time Window must be numeric.")
            return

        results = []
        file1 = self.file1["IPTS"]
        file2 = self.file2["IPTS"]
        for i in range(file1.shape[1]):
            vec1 = file1.iloc[-samples_window:, i].to_numpy()
            best_score = -1
            best_idx = -1
            for j in range(file2.shape[1]):
                vec2 = file2.iloc[-samples_window:, j].to_numpy()
                score = 1 - cosine(vec1, vec2)
                if score > best_score:
                    best_score = score
                    best_idx = j
            if best_score >= threshold:
                results.append((i, best_idx, best_score))

        self.display_results(results)

    def display_results(self, results):
        self.table.setRowCount(0)
        for i, (ch1, ch2, score) in enumerate(results):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(ch1)))
            self.table.setItem(i, 1, QTableWidgetItem(str(ch2)))
            self.table.setItem(i, 2, QTableWidgetItem(f"{score:.3f}"))

        if results:
            self.plot_idr(self.file1, results[0][0], self.ax1, self.canvas1)
            self.plot_idr(self.file2, results[0][1], self.ax2, self.canvas2)
        else:
            self.ax1.clear()
            self.ax2.clear()
            self.canvas1.draw()
            self.canvas2.draw()

    def plot_idr(self, file, mu_index, ax, canvas):
        from app.commonOpenFunc import OpenFunct
        common = OpenFunct()
        idr = common.compute_idr(file)

        ax.clear()
        ax2 = ax.twinx()

        # Plot MU IDR dots
        ax.plot(
            idr[mu_index]["timesec"][1:], 
            idr[mu_index]["idr"].dropna(), 
            '.', 
            markersize=8,
            label="MU IDR"
        )
        ax.set_ylabel("Motor Unit")
        ax.set_xlabel("Time (Sec)")
        ax.set_title(f"MU {mu_index}")

        # Plot reference signal (MVC) on secondary y-axis
        if isinstance(file["REF_SIGNAL"], pd.DataFrame) and not file["REF_SIGNAL"].empty:
            ref = file["REF_SIGNAL"][0]
            time = np.arange(len(ref)) / file["FSAMP"]
            ax2.plot(time, ref, color='gray', alpha=0.7, linewidth=1.5, label="MVC")
            ax2.set_ylabel("MVC (%)")
            ax2.set_zorder(0)
            ax.set_zorder(1)
            ax.patch.set_alpha(0)  # Make primary axis background transparent

        canvas.draw()

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
