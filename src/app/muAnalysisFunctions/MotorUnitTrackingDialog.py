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
from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from app.muAnalysisFunctions.electrode_layouts import get_electrode_grid
from scipy.signal import correlate2d

def load_otb_data(filepath):
    file_handler = FileUploadFunc()
    success = file_handler.emg_from_otb(filepath)
    if not success:
        raise ValueError("Failed to load .mat file using OpenHDEMG loader")
    return FileUploadFunc.file

class MotorUnitTrackingDialog(QDialog):

    """Motor Unit Tracking Advaced Tool functionality and display"""

    def __init__(self, parent=None, matrix_orientation=None, matrix_code=None):
        super().__init__(parent)
        self.setWindowTitle("Motor Unit Tracking")
        self.setMinimumWidth(1200)
        self.setMinimumHeight(700)
        self.setStyleSheet(self._get_stylesheet())
        self.file1 = None
        self.file2 = None
        self.results = []
        self.inclusion_status = []
        self.init_ui()
        
        
        self.matrix_orientation = int(matrix_orientation) if matrix_orientation else 0
        self.matrix_code = None if matrix_code in (None, "", "None") else matrix_code
        

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # --- File and parameter controls (restored) ---
        file1_layout = QHBoxLayout()
        load_file1_btn = QPushButton("Load File 1")
        load_file1_btn.clicked.connect(self.load_file1)
        
        load_json1_btn = QPushButton("Load JSON 1")
        load_json1_btn.clicked.connect(self.load_json1)
        self.file1_label = QLabel("No file selected")
        self.file1_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file1_layout.addWidget(load_file1_btn)
        file1_layout.addWidget(load_json1_btn)
        file1_layout.addWidget(self.file1_label)
        main_layout.addLayout(file1_layout)

        file2_layout = QHBoxLayout()
        load_file2_btn = QPushButton("Load File 2")
        load_file2_btn.clicked.connect(self.load_file2)
        load_json2_btn = QPushButton("Load JSON 2")
        load_json2_btn.clicked.connect(self.load_json2)
        self.file2_label = QLabel("No file selected")
        self.file2_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        file2_layout.addWidget(load_file2_btn)
        file2_layout.addWidget(load_json2_btn)
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

        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        track_btn = QPushButton("Track")
        track_btn.setFixedHeight(32)
        track_btn.clicked.connect(self.on_track)
        main_layout.addWidget(track_btn)

        # --- Top controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        self.mu_pair_selector = QComboBox()
        self.mu_pair_selector.currentIndexChanged.connect(self.on_mu_pair_changed)
        controls_layout.addWidget(QLabel("Pair of MUs to visualise:"))
        controls_layout.addWidget(self.mu_pair_selector)
        # --- Add manual input for MU pair ---
        self.mu_pair_input = QLineEdit()
        self.mu_pair_input.setPlaceholderText("e.g. 3-7")
        self.mu_pair_input.setFixedWidth(70)
        controls_layout.addWidget(self.mu_pair_input)
        self.mu_pair_input_btn = QPushButton("Go")
        self.mu_pair_input_btn.setFixedWidth(40)
        self.mu_pair_input_btn.clicked.connect(self.on_manual_mu_pair_input)
        controls_layout.addWidget(self.mu_pair_input_btn)
        # --- End manual input ---
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
      
        
        
        muap_grids_layout.addWidget(QLabel("MUAP Overlay Grid"))
        self.muap_fig1, _ = plt.subplots(8, 8, figsize=(3, 3))  # Size can be changed if needed
        self.muap_canvas1 = FigureCanvas(self.muap_fig1)
        muap_grids_layout.addWidget(self.muap_canvas1)
          
        plots_layout.addLayout(muap_grids_layout)
        
        # Right: IDR plots
        idr_plots_layout = QVBoxLayout()

        self.fig1, self.ax1 = plt.subplots(figsize=(2.9, 1.4), constrained_layout=True)
        self.canvas1 = FigureCanvas(self.fig1)
        idr_plots_layout.addWidget(self.canvas1)

        self.fig2, self.ax2 = plt.subplots(figsize=(2.9, 1.4), constrained_layout=True)


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
    def load_json1(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select JSON File 1", "", "JSON Files (*.json *.json.gz);;All Files (*)"
        )
        if file_path:
            self.file1_label.setText(os.path.basename(file_path))
            try:
                file_handler = FileUploadFunc()
                success = file_handler.emg_from_json(file_path)
                if not success:
                    raise ValueError("Failed to load JSON file")
                self.file1 = FileUploadFunc.file
            except Exception as e:
                ErrorDialog(f"Failed to load JSON File 1:\n{str(e)}", 'Error').exec_()

    def load_json2(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select JSON File 2", "", "JSON Files (*.json *.json.gz);;All Files (*)"
        )
        if file_path:
            self.file2_label.setText(os.path.basename(file_path))
            try:
                file_handler = FileUploadFunc()
                success = file_handler.emg_from_json(file_path)
                if not success:
                    raise ValueError("Failed to load JSON file")
                self.file2 = FileUploadFunc.file
            except Exception as e:
                ErrorDialog(f"Failed to load JSON File 2:\n{str(e)}", 'Error').exec_()
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

        num_mus_1 = len(self.file1.get("MUPULSES", []))
        num_mus_2 = len(self.file2.get("MUPULSES", []))

        results = []

        for i in range(num_mus_1):
            muaps1, _ = self.compute_muaps(self.file1, i, samples_window)
            if muaps1 is None:
                continue

            best_score = -1
            best_idx = -1
            for j in range(num_mus_2):
                muaps2, _ = self.compute_muaps(self.file2, j, samples_window)
                if muaps2 is None:
                    continue

                score = self.compute_xcc(muaps1, muaps2)
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
        self.plot_idr(self.file1, ch1, self.ax1, self.canvas1,color='blue')
        self.plot_idr(self.file2, ch2, self.ax2, self.canvas2,color='orange')
        # MUAP grids
        # self.plot_muap_grid(self.file1, ch1, self.muap_fig1, self.muap_canvas1)
        # self.plot_muap_grid(self.file2, ch2, self.muap_fig2, self.muap_canvas2)
        self.plot_muap_grid_overlay(self.file1, ch1, self.file2, ch2, self.muap_fig1, self.muap_canvas1)

        # Inclusion label
        self.inclusion_label.setText(self.inclusion_status[idx].upper())
        self.inclusion_label.setStyleSheet(
            "color: green; font-weight: bold;" if self.inclusion_status[idx] == "Included" else "color: red; font-weight: bold;"
        )
    def plot_muap_grid_overlay(self, file1, mu_index1, file2, mu_index2, fig, canvas):
        def compute_muaps(file, mu_index, window):
            # Extract signals
            raw_signal = file.get("RAW_SIGNAL")
            mu_pulses = file.get("MUPULSES")
            fsamp = file.get("FSAMP", 2048)

            if raw_signal is None or mu_pulses is None:
                return None, fsamp

            if isinstance(raw_signal, dict):
                raw_signal = pd.DataFrame(raw_signal)
            if isinstance(raw_signal, pd.DataFrame):
                raw_signal = raw_signal.values
            if not (isinstance(raw_signal, np.ndarray) and raw_signal.ndim == 2):
                return None, fsamp

            pulses = mu_pulses[mu_index] if isinstance(mu_pulses, (list, tuple)) and mu_index < len(mu_pulses) else []
            pulses = np.array(pulses, dtype=int) if len(pulses) > 0 else np.array([], dtype=int)

            # Remove pulses too close to signal edges
            valid_pulses = pulses[(pulses - window >= 0) & (pulses + window + 1 <= raw_signal.shape[0])]

            seg_len = 2 * window + 1
            n_channels = raw_signal.shape[1]
            max_channels = 64
            muaps = np.full((max_channels, seg_len), np.nan)

            for ch in range(min(n_channels, max_channels)):
                segments = []
                for p in valid_pulses:
                    start = p - window
                    end = p + window + 1
                    segments.append(raw_signal[start:end, ch])
                if segments:
                    muaps[ch, :] = np.mean(segments, axis=0)
            return muaps, fsamp

        # Set your desired window here
        window = 50  # You can change this to any positive integer
        muaps1, fsamp1 = compute_muaps(file1, mu_index1, window)
        muaps2, fsamp2 = compute_muaps(file2, mu_index2, window)
        fig.clear()

        if muaps1 is None or muaps2 is None:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "MUAPs not available", ha="center", va="center")
            canvas.draw()
            return

        # Get grid definition
        grid = get_electrode_grid(code=self.matrix_code, orientation=self.matrix_orientation)
        n_rows = len(grid)
        n_cols = len(grid[0])

        # X-axis time in ms
        time_ms = np.arange(-window, window + 1) * 1000.0 / fsamp1

        # Get global y-limits for normalization
        combined_muaps = np.concatenate([
            muaps1[np.isfinite(muaps1)],
            muaps2[np.isfinite(muaps2)]
        ])
        if combined_muaps.size > 0:
            ymin, ymax = np.min(combined_muaps), np.max(combined_muaps)
            if np.isclose(ymin, ymax):
                ymin -= 1
                ymax += 1
            else:
                yrange = ymax - ymin
                ymin -= 0.05 * yrange
                ymax += 0.05 * yrange
        else:
            ymin, ymax = -1, 1

        axs = fig.subplots(n_rows, n_cols, squeeze=False)

        for r in range(n_rows):
            for c in range(n_cols):
                ch = grid[r][c]
                ax = axs[r][c]
                ax.clear()
                if np.isnan(ch):
                    ax.axis('off')
                    continue
                ch = int(ch)
                valid1 = muaps1[ch, :].shape[0] > 0 and np.any(np.isfinite(muaps1[ch, :]))
                valid2 = muaps2[ch, :].shape[0] > 0 and np.any(np.isfinite(muaps2[ch, :]))
                if valid1:
                    ax.plot(time_ms, muaps1[ch, :], color='blue', linewidth=1, label='File 1')
                if valid2:
                    ax.plot(time_ms, muaps2[ch, :], color='orange', linewidth=1, label='File 2')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_ylim([ymin, ymax])
                for spine in ax.spines.values():
                    spine.set_visible(False)
                if r == 0 and c == 0:
                    ax.legend(frameon=False, fontsize=7, loc='upper left')

        fig.tight_layout(pad=0)
        fig.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0.15, hspace=0.05)
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
        common = CommonOpenFunc()
        idr = common.compute_idr(file)

        # get or make a persistent right axis for this left axis
        if not hasattr(self, "_idr_right_axes"):
            self._idr_right_axes = {}
        key = id(ax)
        ax_right = self._idr_right_axes.get(key)

        # if missing/stale, create and remember it
        if ax_right is None or ax_right.figure is not ax.figure:
            ax_right = ax.twinx()
            self._idr_right_axes[key] = ax_right

        # clear BOTH axes before plotting
        ax.clear()
        ax_right.clear()

        # Plot MU IDR dots on left axis
        ax.plot(
            idr[mu_index]["timesec"][1:],
            idr[mu_index]["idr"].dropna(),
            '.',
            markersize=8,
            label="MU IDR",
            color=color,
        )
        ax.set_ylabel("Discharge Rate (pps)")
        ax.set_xlabel("Time (Sec)")
        ax.set_title(f"MU {mu_index}")

        # Plot MVC on right axis
        if isinstance(file.get("REF_SIGNAL"), pd.DataFrame) and not file["REF_SIGNAL"].empty:
            ref = file["REF_SIGNAL"][0]
            time = np.arange(len(ref)) / file["FSAMP"]
            ax_right.plot(time, ref, color='gray', alpha=0.7, linewidth=1.5, label="MVC")
            ax_right.yaxis.set_label_position("right")
            ax_right.yaxis.tick_right()
            ax_right.set_ylabel("MVC (%)", labelpad=8, rotation=270)  # rotation=270 looks natural on the right
            # optional: nudge the right spine outward a bit for even more space
            ax_right.spines["right"].set_position(("outward", 6))
            # optional: match label color to the MVC trace
            ax_right.yaxis.label.set_color("gray")

            # keep dots visible above the MVC trace
            ax_right.set_zorder(0)
            ax.set_zorder(1)
            ax.patch.set_alpha(0)

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

    # --- Add handler for manual MU pair input ---
    def on_manual_mu_pair_input(self):
        text = self.mu_pair_input.text().strip()
        if '-' not in text:
            ErrorDialog("Invalid Motor unit provided", 'Error').exec_()
            return
        try:
            mu1_str, mu2_str = text.split('-', 1)
            mu1 = int(mu1_str)
            mu2 = int(mu2_str)
        except Exception:
            ErrorDialog("Invalid Motor unit provided", 'Error').exec_()
            return
        # Find the index in results
        found_idx = -1
        for idx, (ch1, ch2, _) in enumerate(self.results):
            if ch1 == mu1 and ch2 == mu2:
                found_idx = idx
                break
        if found_idx == -1:
            ErrorDialog("Invalid Motor unit provided", 'Error').exec_()
            return
        # Update selection
        self.mu_pair_selector.setCurrentIndex(found_idx)
        self.table.selectRow(found_idx)
        self.update_plots(found_idx)
    
    from scipy.signal import correlate2d

    def compute_xcc(self, muap1, muap2):
        muap1 = muap1 - np.nanmean(muap1)
        muap2 = muap2 - np.nanmean(muap2)

        # Replace NaNs with 0 for correlation
        muap1 = np.nan_to_num(muap1)
        muap2 = np.nan_to_num(muap2)

        corr = correlate2d(muap1, muap2, mode='valid')
        norm = np.linalg.norm(muap1) * np.linalg.norm(muap2)

        return (corr[0, 0] / norm) if norm != 0 else 0
        
    def compute_muaps(self, file, mu_index, window):
        # Extract signals
        raw_signal = file.get("RAW_SIGNAL")
        mu_pulses = file.get("MUPULSES")
        fsamp = file.get("FSAMP", 2048)

        if raw_signal is None or mu_pulses is None:
            return None, fsamp

        if isinstance(raw_signal, dict):
            raw_signal = pd.DataFrame(raw_signal)
        if isinstance(raw_signal, pd.DataFrame):
            raw_signal = raw_signal.values
        if not (isinstance(raw_signal, np.ndarray) and raw_signal.ndim == 2):
            return None, fsamp

        pulses = mu_pulses[mu_index] if isinstance(mu_pulses, (list, tuple)) and mu_index < len(mu_pulses) else []
        pulses = np.array(pulses, dtype=int) if len(pulses) > 0 else np.array([], dtype=int)

        # Remove pulses too close to signal edges
        valid_pulses = pulses[(pulses - window >= 0) & (pulses + window + 1 <= raw_signal.shape[0])]

        seg_len = 2 * window + 1
        n_channels = raw_signal.shape[1]
        max_channels = 64
        muaps = np.full((max_channels, seg_len), np.nan)

        for ch in range(min(n_channels, max_channels)):
            segments = []
            for p in valid_pulses:
                start = p - window
                end = p + window + 1
                segments.append(raw_signal[start:end, ch])
            if segments:
                muaps[ch, :] = np.mean(segments, axis=0)
        return muaps, fsamp
