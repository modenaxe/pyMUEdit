from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QLineEdit, QCheckBox, QMessageBox, QSpacerItem, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
import numpy as np
from scipy.spatial.distance import cosine
import os
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from scipy.io import loadmat
import pandas as pd
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.commonOpenFunc import commonOpenFunc
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog

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
        self.setMinimumWidth(1400)
        self.setMinimumHeight(900)
        self.setStyleSheet(self._get_stylesheet())
        self.file1 = None
        self.file2 = None
        self.results = []
        self.inclusion_status = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # --- File and parameter controls (restored) ---
        file1_layout = QHBoxLayout()
        load_file1_btn = QPushButton("Load File 1")
        load_file1_btn.clicked.connect(self.load_file1)
        self.file1_label = QLabel("No file selected")
        self.file1_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file1_layout.addWidget(load_file1_btn)
        file1_layout.addWidget(self.file1_label)
        main_layout.addLayout(file1_layout)

        file2_layout = QHBoxLayout()
        load_file2_btn = QPushButton("Load File 2")
        load_file2_btn.clicked.connect(self.load_file2)
        self.file2_label = QLabel("No file selected")
        self.file2_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file2_layout.addWidget(load_file2_btn)
        file2_layout.addWidget(self.file2_label)
        main_layout.addLayout(file2_layout)

        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Threshold:")
        self.threshold_input = QLineEdit("0.5")
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_input)
        main_layout.addLayout(threshold_layout)

        window_layout = QHBoxLayout()
        window_label = QLabel("Time Window (ms):")
        self.window_input = QLineEdit("50")
        window_layout.addWidget(window_label)
        window_layout.addWidget(self.window_input)
        main_layout.addLayout(window_layout)

        self.filter_checkbox = QCheckBox("Apply Filter")
        self.exclude_checkbox = QCheckBox("Exclude Below Threshold")
        main_layout.addWidget(self.filter_checkbox)
        main_layout.addWidget(self.exclude_checkbox)

        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        track_btn = QPushButton("Track")
        track_btn.setFixedHeight(40)
        track_btn.clicked.connect(self.on_track)
        main_layout.addWidget(track_btn)

        # --- Top controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        self.mu_pair_selector = QComboBox()
        self.mu_pair_selector.currentIndexChanged.connect(self.on_mu_pair_changed)
        controls_layout.addWidget(QLabel("Pair of MUs to visualise:"))
        controls_layout.addWidget(self.mu_pair_selector)
        self.inclusion_label = QLabel("INCLUDED")
        self.inclusion_label.setStyleSheet("color: green; font-weight: bold;")
        controls_layout.addWidget(self.inclusion_label)
        self.include_btn = QPushButton("Include/Exclude")
        self.include_btn.clicked.connect(self.toggle_inclusion)
        controls_layout.addWidget(self.include_btn)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

        # --- Middle: Plots ---
        plots_layout = QHBoxLayout()
        # Left: MUAP grids
        muap_grids_layout = QVBoxLayout()
        muap_grids_layout.addWidget(QLabel("MUAP Grid (File 1)"))
        self.muap_fig1, _ = plt.subplots(8, 8, figsize=(4, 4))
        self.muap_canvas1 = FigureCanvas(self.muap_fig1)
        muap_grids_layout.addWidget(self.muap_canvas1)
        muap_grids_layout.addWidget(QLabel("MUAP Grid (File 2)"))
        self.muap_fig2, _ = plt.subplots(8, 8, figsize=(4, 4))
        self.muap_canvas2 = FigureCanvas(self.muap_fig2)
        muap_grids_layout.addWidget(self.muap_canvas2)
        plots_layout.addLayout(muap_grids_layout)
        # Right: IDR plots
        idr_plots_layout = QVBoxLayout()
        self.fig1, self.ax1 = plt.subplots(figsize=(3, 1.5))
        self.canvas1 = FigureCanvas(self.fig1)
        idr_plots_layout.addWidget(self.canvas1)
        self.fig2, self.ax2 = plt.subplots(figsize=(3, 1.5))
        self.canvas2 = FigureCanvas(self.fig2)
        idr_plots_layout.addWidget(self.canvas2)
        plots_layout.addLayout(idr_plots_layout)
        main_layout.addLayout(plots_layout)

        # --- Bottom: Results table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["MU_file1", "MU_file2", "XCC", "Inclusion"])
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.table.setMinimumHeight(100)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.table, stretch=2)

        self.setLayout(main_layout)

    def load_file1(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File 1", "", "MAT Files (*.mat)")
        if file_path:
            self.file1_label.setText(os.path.basename(file_path))
            try:
                self.file1 = load_otb_data(file_path)
            except Exception as e:
                ErrorDialog(f"Failed to load File 1:\n{str(e)}", 'Error').exec_()
                

    def load_file2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File 2", "", "MAT Files (*.mat)")
        if file_path:
            self.file2_label.setText(os.path.basename(file_path))
            try:
                self.file2 = load_otb_data(file_path)
            except Exception as e:
                ErrorDialog(f"Failed to load File 2:\n{str(e)}", 'Error').exec_()

    def on_track(self):
        if self.file1 is None or self.file2 is None:
            ErrorDialog("Both files must be selected", 'Error').exec_()
            return

        try:
            threshold = float(self.threshold_input.text())
            time_window_ms = int(self.window_input.text())
            fsamp = self.file1.get("FSAMP") if isinstance(self.file1, dict) else None
            if not isinstance(fsamp, (int, float)):
                ErrorDialog("FSAMP is missing or not numeric in File 1.", 'Error').exec_()
                return
            samples_window = int((time_window_ms / 1000.0) * fsamp)
        except ValueError:
            ErrorDialog("Threshold and Time Window must be numeric.", 'Error').exec_()
            return

        results = []
        file1 = self.file1.get("IPTS") if isinstance(self.file1, dict) else None
        file2 = self.file2.get("IPTS") if isinstance(self.file2, dict) else None
        if not (isinstance(file1, pd.DataFrame) and isinstance(file2, pd.DataFrame)):
            ErrorDialog("Loaded files do not contain valid IPTS DataFrames.", 'Error').exec_()
            return
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
        self.results = results
        self.inclusion_status = ["Included"] * len(results)
        self.table.setRowCount(0)
        self.mu_pair_selector.clear()
        for i, (ch1, ch2, score) in enumerate(results):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(ch1)))
            self.table.setItem(i, 1, QTableWidgetItem(str(ch2)))
            self.table.setItem(i, 2, QTableWidgetItem(f"{score:.3f}"))
            self.table.setItem(i, 3, QTableWidgetItem(self.inclusion_status[i]))
            self.mu_pair_selector.addItem(f"{ch1}-{ch2}")
        if results:
            self.table.selectRow(0)
            self.mu_pair_selector.setCurrentIndex(0)
            self.update_plots(0)
        else:
            self.clear_all_plots()

    def on_table_selection_changed(self):
        selected = self.table.selectedItems()
        if selected and len(selected) >= 1:
            row = selected[0].row()
            self.mu_pair_selector.setCurrentIndex(row)
            self.update_plots(row)

    def on_mu_pair_changed(self, idx):
        if idx >= 0 and idx < len(self.results):
            self.table.selectRow(idx)
            self.update_plots(idx)

    def update_plots(self, idx):
        # --- Update all plots and grids for the selected MU pair ---
        ch1, ch2, _ = self.results[idx]
        # IDR plots
        self.plot_idr(self.file1, ch1, self.ax1, self.canvas1)
        self.plot_idr(self.file2, ch2, self.ax2, self.canvas2)
        # MUAP grids
        self.plot_muap_grid(self.file1, ch1, self.muap_fig1, self.muap_canvas1)
        self.plot_muap_grid(self.file2, ch2, self.muap_fig2, self.muap_canvas2)
        # Inclusion label
        self.inclusion_label.setText(self.inclusion_status[idx].upper())
        self.inclusion_label.setStyleSheet(
            "color: green; font-weight: bold;" if self.inclusion_status[idx] == "Included" else "color: red; font-weight: bold;"
        )

    def plot_muap_grid(self, file, mu_index, fig, canvas):
        raw_signal = file.get("RAW_SIGNAL")
        mu_pulses = file.get("MUPULSES")
        if raw_signal is None or mu_pulses is None:
            fig.clf()
            canvas.draw()
            return
        if isinstance(raw_signal, dict):
            raw_signal = pd.DataFrame(raw_signal)
        if not isinstance(raw_signal, (np.ndarray, pd.DataFrame)):
            fig.clf()
            canvas.draw()
            return
        if isinstance(raw_signal, pd.DataFrame):
            raw_signal = raw_signal.values
        if not (isinstance(raw_signal, np.ndarray) and raw_signal.ndim == 2):
            fig.clf()
            canvas.draw()
            return
        n_channels = raw_signal.shape[1]
        pulses = []
        if isinstance(mu_pulses, (list, tuple)) and mu_index < len(mu_pulses):
            pulses = mu_pulses[mu_index]
        if not isinstance(pulses, (list, np.ndarray)):
            pulses = []
        window = 40
        muaps = np.zeros((n_channels, 2 * window + 1))
        valid_signal = (
            isinstance(raw_signal, np.ndarray)
            and raw_signal.ndim == 2
        )
        for ch in range(n_channels):
            segments = []
            if isinstance(pulses, (list, np.ndarray)):
                for p in pulses:
                    try:
                        p_int = int(p)
                    except Exception:
                        continue
                    start = p_int - window
                    end = p_int + window + 1
                    if (
                        isinstance(start, int) and isinstance(end, int)
                        and start >= 0 and end <= raw_signal.shape[0] and end > start
                        and valid_signal and 0 <= ch < raw_signal.shape[1]
                    ):
                        segments.append(raw_signal[start:end, ch])
            if segments:
                muaps[ch, :] = np.mean(segments, axis=0)
            else:
                muaps[ch, :] = np.nan
        grid_size = int(np.ceil(np.sqrt(n_channels)))
        n_rows = n_cols = grid_size
        if n_rows * n_cols < n_channels:
            n_rows += 1
        fig.clf()
        axs = fig.subplots(n_rows, n_cols, squeeze=False)
        for ch in range(n_channels):
            r, c = divmod(ch, n_cols)
            axs[r][c].plot(muaps[ch, :], color='orange')
            axs[r][c].set_xticks([])
            axs[r][c].set_yticks([])
            axs[r][c].spines['top'].set_visible(False)
            axs[r][c].spines['right'].set_visible(False)
            axs[r][c].spines['bottom'].set_visible(False)
            axs[r][c].spines['left'].set_visible(False)
        for i in range(n_rows * n_cols):
            if i >= n_channels:
                r, c = divmod(i, n_cols)
                axs[r][c].axis('off')
        fig.tight_layout()
        canvas.draw()

    def clear_all_plots(self):
        self.fig1.clf()
        self.canvas1.draw()
        self.fig2.clf()
        self.canvas2.draw()
        self.muap_fig1.clf()
        self.muap_canvas1.draw()
        self.muap_fig2.clf()
        self.muap_canvas2.draw()

    def toggle_inclusion(self):
        idx = self.mu_pair_selector.currentIndex()
        if idx >= 0 and idx < len(self.inclusion_status):
            if self.inclusion_status[idx] == "Included":
                self.inclusion_status[idx] = "Excluded"
            else:
                self.inclusion_status[idx] = "Included"
            self.table.setItem(idx, 3, QTableWidgetItem(self.inclusion_status[idx]))
            self.inclusion_label.setText(self.inclusion_status[idx].upper())
            self.inclusion_label.setStyleSheet(
                "color: green; font-weight: bold;" if self.inclusion_status[idx] == "Included" else "color: red; font-weight: bold;"
            )

    def plot_idr(self, file, mu_index, ax, canvas, color='blue'):
        common = commonOpenFunc()
        idr = common.compute_idr(file)

        ax.clear()
        ax2 = ax.twinx()

        # Plot MU IDR dots
        ax.plot(
            idr[mu_index]["timesec"][1:], 
            idr[mu_index]["idr"].dropna(), 
            '.', 
            markersize=8,
            label="MU IDR",
            color=color
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
