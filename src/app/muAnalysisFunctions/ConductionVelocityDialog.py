"""
Dialog for estimating Motor Unit Conduction Velocity (CV) for selected MUs, columns, and rows.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QSpinBox, QTextEdit, QGroupBox, QTableWidget, QTableWidgetItem, QApplication
)
from PyQt5.QtCore import Qt
import numpy as np
import pandas as pd
from scipy.signal import correlate
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# --- Utility functions to access EMG data ---
def get_available_mus():
    emgfile = FileUploadFunc.file
    if emgfile is None:
        return []
    return list(range(emgfile["NUMBER_OF_MUS"]))

def get_available_columns():
    emgfile = FileUploadFunc.file
    if emgfile is None:
        return []
    # Return all available columns (matrix codes) from RAW_SIGNAL
    all_cols = list(emgfile["RAW_SIGNAL"].columns)
    # Convert column names to strings for QComboBox compatibility
    return [str(col) for col in all_cols]

def get_row_range():
    emgfile = FileUploadFunc.file
    if emgfile is None:
        return (0, 0)
    # Assume rows are time samples
    n_rows = emgfile["RAW_SIGNAL"].shape[0]
    return (0, n_rows - 1)

# --- Main CV estimation logic ---
def estimate_conduction_velocity(mu, col, from_row, to_row):
    emgfile = FileUploadFunc.file
    if emgfile is None:
        return "No EMG file loaded."
    # Get MUAPs for the selected MU (spike-triggered average)
    # For simplicity, use the mean of the EMG signal at the selected column, triggered by MUPULSES
    mupulses = emgfile["MUPULSES"][mu]
    if len(mupulses) < 2:
        return "Not enough firings for MU {} to estimate CV.".format(mu)
    # Restrict to selected row range (time window)
    mupulses = [p for p in mupulses if from_row <= p <= to_row]
    if len(mupulses) < 2:
        return "Not enough firings in selected range."
    # Extract signal segments around each firing
    win_len = 20  # samples before/after, can be adjusted
    segs = []
    for p in mupulses:
        start = max(p - win_len, 0)
        end = min(p + win_len + 1, emgfile["RAW_SIGNAL"].shape[0])
        seg = emgfile["RAW_SIGNAL"].iloc[start:end, col].to_numpy()
        if len(seg) == 2 * win_len + 1:
            segs.append(seg)
    if len(segs) < 2:
        return "Not enough valid segments for CV estimation."
    # Compute average MUAP
    muap = np.mean(segs, axis=0)
    # For CV, cross-correlate adjacent channels (if possible)
    all_cols = get_available_columns()
    col_idx = all_cols.index(col)
    if col_idx == 0 or col_idx == len(all_cols) - 1:
        return "Select a non-edge column for CV estimation."
    # Use current and next channel
    muap1 = muap
    # Get average MUAP for adjacent channel
    segs2 = []
    for p in mupulses:
        start = max(p - win_len, 0)
        end = min(p + win_len + 1, emgfile["RAW_SIGNAL"].shape[0])
        seg = emgfile["RAW_SIGNAL"].iloc[start:end, all_cols[col_idx + 1]].to_numpy()
        if len(seg) == 2 * win_len + 1:
            segs2.append(seg)
    if len(segs2) < 2:
        return "Not enough valid segments for adjacent channel."
    muap2 = np.mean(segs2, axis=0)
    # Cross-correlation to find lag
    corr = correlate(muap2, muap1, mode='full')
    lags = np.arange(-len(muap1) + 1, len(muap1))
    lag = lags[np.argmax(corr)]
    # Calculate CV
    ied = emgfile.get("IED", 10)  # mm, fallback to 10mm
    fsamp = emgfile.get("FSAMP", 2048)  # Hz, fallback
    if lag == 0:
        return "Unable to estimate lag for CV."
    time_delay = abs(lag) / fsamp  # seconds
    cv = (ied / 1000) / time_delay  # m/s
    return f"Estimated CV for MU {mu}, columns {col}/{all_cols[col_idx+1]}, rows {from_row}-{to_row}: {cv:.2f} m/s (lag={lag} samples, IED={ied}mm, Fs={fsamp}Hz)"

class ConductionVelocityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MUs CV estimation")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        self.setStyleSheet(self._get_stylesheet())
        self.init_ui()
        # Load initial grid automatically
        self.load_initial_grid()

    def _get_stylesheet(self):
        return f"""
            QDialog {{
                background: {CleanTheme.BG_CARD};
            }}
            QLabel {{
                color: {CleanTheme.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QGroupBox {{
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 6px;
                margin-top: 10px;
                background: {CleanTheme.BG_MAIN};
            }}
            QGroupBox:title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: {CleanTheme.TEXT_SECONDARY};
            }}
            QComboBox, QSpinBox, QTextEdit {{
                background: {CleanTheme.BG_MAIN};
                color: {CleanTheme.TEXT_PRIMARY};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton {{
                background: {CleanTheme.ANALYSIS_BG_BUTTON};
                color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                border-radius: 5px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {CleanTheme.ANALYSIS_BG_DROPDOWN};
            }}
        """

    def init_ui(self):
        main_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()
        # MU selection
        mu_group = QGroupBox("MU number")
        mu_layout = QVBoxLayout()
        self.mu_dropdown = QComboBox()
        try:
            available_mus = get_available_mus()
            if available_mus:
                self.mu_dropdown.addItems([str(mu) for mu in available_mus])
            else:
                self.mu_dropdown.addItem("No data loaded")  # Fallback item
        except Exception as e:
            print(f"Error loading MUs: {e}")
            self.mu_dropdown.addItem("Error loading data")  # Fallback item
        self.mu_dropdown.currentTextChanged.connect(self.on_mu_changed)  # Add signal connection
        mu_layout.addWidget(self.mu_dropdown)
        mu_group.setLayout(mu_layout)
        controls_layout.addWidget(mu_group)
        # Column selection
        col_group = QGroupBox("Column")
        col_layout = QVBoxLayout()
        self.col_dropdown = QComboBox()
        try:
            available_cols = get_available_columns()
            if available_cols:
                self.col_dropdown.addItems(available_cols)  # Use matrix codes directly
            else:
                self.col_dropdown.addItem("No data loaded")  # Fallback item
        except Exception as e:
            print(f"Error loading columns: {e}")
            self.col_dropdown.addItem("Error loading data")  # Fallback item
        self.col_dropdown.currentTextChanged.connect(self.on_column_changed)  # Add signal connection
        col_layout.addWidget(self.col_dropdown)
        col_group.setLayout(col_layout)
        controls_layout.addWidget(col_group)
        # Row selection
        row_group = QGroupBox("Rows")
        row_layout = QHBoxLayout()
        try:
            min_row, max_row = get_row_range()
        except Exception as e:
            print(f"Error getting row range: {e}")
            min_row, max_row = 0, 1000  # Fallback values
        self.from_row = QSpinBox()
        self.from_row.setRange(min_row, max_row)
        self.from_row.setValue(min_row)
        self.to_row = QSpinBox()
        self.to_row.setRange(min_row, max_row)
        self.to_row.setValue(max_row)
        row_layout.addWidget(QLabel("From:"))
        row_layout.addWidget(self.from_row)
        row_layout.addWidget(QLabel("To:"))
        row_layout.addWidget(self.to_row)
        row_group.setLayout(row_layout)
        controls_layout.addWidget(row_group)
        self.estimate_btn = QPushButton("Estimate")
        self.estimate_btn.clicked.connect(self.on_estimate)
        controls_layout.addWidget(self.estimate_btn)
        main_layout.addLayout(controls_layout)

        # Split main area: left for plot, right for results
        content_layout = QHBoxLayout()
        # Plot area
        self.plot_canvas = FigureCanvas(plt.Figure(figsize=(8, 6)))
        content_layout.addWidget(self.plot_canvas, stretch=3)
        # Results area
        results_layout = QVBoxLayout()
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["#", "CV", "RMS", "XCC"])
        results_layout.addWidget(self.results_table)
        self.copy_btn = QPushButton("Copy results")
        self.copy_btn.clicked.connect(self.copy_results)
        results_layout.addWidget(self.copy_btn)
        content_layout.addLayout(results_layout, stretch=1)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def on_estimate(self):
        try:
            mu = int(self.mu_dropdown.currentText()) if self.mu_dropdown.currentText() else 0
            col = int(self.col_dropdown.currentText()) if self.col_dropdown.currentText() else 0
            from_row = self.from_row.value()
            to_row = self.to_row.value()
            # Compute and plot grid, fill table
            self.update_plot_and_table()
        except Exception as e:
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.results_table.setItem(0, 1, QTableWidgetItem(str(e)))
            print(f"Error in on_estimate: {e}")  # Debug print

    def load_initial_grid(self):
        """Load the grid automatically when dialog opens"""
        try:
            emgfile = FileUploadFunc.file
            if emgfile is not None:
                self.update_plot_and_table()
            else:
                # No data loaded - show empty plot
                self.plot_canvas.figure.clf()
                self.plot_canvas.draw()
                self.results_table.setRowCount(0)
        except Exception as e:
            print(f"Error in load_initial_grid: {e}")
            # Show empty plot if error
            self.plot_canvas.figure.clf()
            self.plot_canvas.draw()
            self.results_table.setRowCount(0)

    def on_mu_changed(self):
        """Handle MU dropdown change - update the grid"""
        self.update_plot_and_table()
        
    def on_column_changed(self):
        """Handle Column dropdown change - update the grid"""
        self.update_plot_and_table()

    def update_plot_and_table(self):
        """Central method to update the plot and table based on current UI selections."""
        try:
            mu = int(self.mu_dropdown.currentText()) if self.mu_dropdown.currentText() else 0
            col = self.col_dropdown.currentText() if self.col_dropdown.currentText() else ""
            from_row = self.from_row.value()
            to_row = self.to_row.value()
            
            emgfile = FileUploadFunc.file
            if emgfile and col:
                # Compute data for both grid and table using selected matrix code
                grid_data, table_data = self.compute_grid_and_table(mu, col, from_row, to_row)
                
                # Plot the grid using the computed data
                self.plot_muap_grid(grid_data)
                
                # Fill the results table
                self.fill_results_table(table_data)
                
        except Exception as e:
            print(f"Error updating plot and table: {e}")
            # Clear plot and table on error
            self.plot_canvas.figure.clf()
            self.plot_canvas.draw()
            self.results_table.setRowCount(0)
            
    def compute_grid_and_table(self, mu, selected_col, from_row, to_row):
        emgfile = FileUploadFunc.file
        if emgfile is None:
            return [], []
        
        raw_signal = emgfile.get("RAW_SIGNAL")
        mu_pulses = emgfile.get("MUPULSES")
        fsamp = emgfile.get("FSAMP", 2048)  # default if missing

        if raw_signal is None or mu_pulses is None:
            return [], []

        # Convert DataFrame to np.ndarray if needed - using matrix operations
        if isinstance(raw_signal, dict):
            raw_signal = pd.DataFrame(raw_signal)
        if isinstance(raw_signal, pd.DataFrame):
            # Get all available columns (matrix codes)
            all_columns = list(raw_signal.columns)
            # Convert to strings for consistency
            all_columns_str = [str(col) for col in all_columns]
            raw_signal_array = raw_signal.values
        else:
            return [], []

        # Find the index of the selected matrix code
        if selected_col not in all_columns_str:
            return [], []
        
        selected_col_idx = all_columns_str.index(selected_col)

        # Get firing indices for this MU using array operations
        if isinstance(mu_pulses, (list, tuple)) and mu < len(mu_pulses):
            pulses = np.array(mu_pulses[mu], dtype=int)
        else:
            pulses = np.array([], dtype=int)
        
        # Filter by row range using vectorized operations
        mask = (pulses >= from_row) & (pulses <= to_row)
        pulses = pulses[mask]
        if pulses.size == 0:
            return [], []

        # Limit to 11 firings for display
        pulses = pulses[:11]

        window = 25  # samples on each side
        seg_len = 2 * window + 1
        
        # Calculate channel range based on selected matrix code
        total_channels = len(all_columns)
        n_channels = 5  # Always display 5 columns
        
        # Center the view around the selected column
        start_ch = max(0, selected_col_idx - 2)  # Try to put selected col in middle
        end_ch = min(total_channels, start_ch + n_channels)
        
        # Adjust start if we're at the end
        if end_ch - start_ch < n_channels:
            start_ch = max(0, end_ch - n_channels)
        
        channel_indices = list(range(start_ch, end_ch))
        channel_names = [str(all_columns[i]) for i in channel_indices]
        actual_n_channels = len(channel_indices)
        n_pulses = len(pulses)

        # Pre-allocate matrices for efficient processing
        segments_matrix = np.full((n_pulses, actual_n_channels, seg_len), np.nan)
        valid_segments = np.zeros((n_pulses, actual_n_channels), dtype=bool)
        
        # Extract all segments using matrix operations
        for pulse_idx, pulse in enumerate(pulses):
            start = pulse - window
            end = pulse + window + 1
            
            if start >= 0 and end <= raw_signal_array.shape[0]:
                # Extract segments for selected channels at once
                segment_data = raw_signal_array[start:end, channel_indices]
                # Remove DC component using broadcasting
                segment_centered = segment_data - np.mean(segment_data, axis=0, keepdims=True)
                segments_matrix[pulse_idx, :, :] = segment_centered.T
                valid_segments[pulse_idx, :] = True

        # Calculate RMS using matrix operations
        rms_matrix = np.full((n_pulses, actual_n_channels), np.nan)
        valid_mask = valid_segments
        rms_matrix[valid_mask] = np.sqrt(np.mean(segments_matrix[valid_mask] ** 2, axis=1))

        # Calculate XCC using matrix operations
        xcc_matrix = np.full((n_pulses, actual_n_channels), np.nan)
        for ch in range(actual_n_channels):
            for pulse_idx in range(1, n_pulses):  # Start from 1 since we compare with previous
                if valid_segments[pulse_idx, ch] and valid_segments[pulse_idx-1, ch]:
                    seg_current = segments_matrix[pulse_idx, ch, :]
                    seg_prev = segments_matrix[pulse_idx-1, ch, :]
                    
                    if np.std(seg_current) > 1e-10 and np.std(seg_prev) > 1e-10:
                        # Stack for correlation matrix computation
                        stacked = np.vstack([seg_current, seg_prev])
                        corr_matrix = np.corrcoef(stacked)
                        if not np.any(np.isnan(corr_matrix)):
                            xcc_matrix[pulse_idx, ch] = corr_matrix[0, 1]

        # Calculate CV using matrix operations
        cv_matrix = np.full((n_pulses, actual_n_channels), np.nan)
        ied = emgfile.get("IED", 8.75)  # Inter-electrode distance
        
        for pulse_idx in range(1, n_pulses):  # Start from 1
            for ch in range(actual_n_channels - 1):  # Exclude last channel
                if valid_segments[pulse_idx, ch] and valid_segments[pulse_idx, ch + 1]:
                    try:
                        seg1 = segments_matrix[pulse_idx, ch, :]
                        seg2 = segments_matrix[pulse_idx, ch + 1, :]
                        
                        # Cross-correlation using scipy
                        corr = correlate(seg2, seg1, mode='full')
                        lags = np.arange(-len(seg1) + 1, len(seg1))
                        lag = lags[np.argmax(corr)]
                        
                        if lag != 0:
                            time_delay = abs(lag) / fsamp
                            cv_matrix[pulse_idx, ch] = (ied / 1000) / time_delay  # m/s
                    except:
                        pass

        # Convert matrix results back to the expected format
        all_muaps = []
        table_data = []
        
        for pulse_idx in range(n_pulses):
            firing_muaps = []
            for ch in range(actual_n_channels):
                if valid_segments[pulse_idx, ch]:
                    seg = segments_matrix[pulse_idx, ch, :]
                    rms = rms_matrix[pulse_idx, ch]
                    xcc = xcc_matrix[pulse_idx, ch]
                    cv = cv_matrix[pulse_idx, ch]
                else:
                    seg = np.full(seg_len, np.nan)
                    rms = np.nan
                    xcc = np.nan
                    cv = np.nan
                
                firing_muaps.append((seg, rms, xcc, cv))
            
            all_muaps.append(firing_muaps)
            
            # Table data from first column of the selected range
            if firing_muaps:
                seg0, rms0, xcc0, cv0 = firing_muaps[0]
                table_data.append((pulse_idx, cv0, rms0 if not np.isnan(rms0) else np.nan, xcc0))

        # Store channel info for plotting labels
        self.current_channel_names = channel_names
        return all_muaps, table_data

    def plot_muap_grid(self, grid_data):
        if not grid_data:
            self.plot_canvas.figure.clf()
            self.plot_canvas.draw()
            return
        
        fig = self.plot_canvas.figure
        fig.clear()
        
        n_firings = len(grid_data)
        n_cols = len(grid_data[0]) if grid_data else 5
        
        # Create subplot matrix
        axs = fig.subplots(n_firings, n_cols, squeeze=False)
        
        # Extract all segments into a matrix for efficient y-limit calculation
        all_segments = []
        for firing_data in grid_data:
            for seg, rms, xcc, cv in firing_data:
                if len(seg) > 0 and not np.all(np.isnan(seg)):
                    all_segments.append(seg)
        
        # Calculate global y-limits using matrix operations
        if all_segments:
            segments_matrix = np.array(all_segments)
            # Use nanmin/nanmax to handle any remaining NaN values
            ymin = np.nanmin(segments_matrix)
            ymax = np.nanmax(segments_matrix)
            y_range = ymax - ymin
            ymax += 0.1 * y_range
            ymin -= 0.1 * y_range
        else:
            ymin, ymax = -1, 1

        # Get actual matrix code names for labeling
        channel_names = getattr(self, 'current_channel_names', [f"col{i}" for i in range(n_cols)])

        # Plot using matrix indexing and vectorized operations
        for firing_idx in range(n_firings):
            for ch in range(n_cols):
                ax = axs[firing_idx, ch]  # Matrix-style indexing
                
                if firing_idx < len(grid_data) and ch < len(grid_data[firing_idx]):
                    seg, rms, xcc, cv = grid_data[firing_idx][ch]
                    
                    # Plot waveform using efficient numpy operations
                    if len(seg) > 0 and not np.all(np.isnan(seg)):
                        # Use numpy array directly for plotting
                        x_indices = np.arange(len(seg))
                        ax.plot(x_indices, seg, color='#1976d2', linewidth=1)
                    
                    # Set consistent y-axis limits using matrix operations
                    ax.set_ylim(ymin, ymax)
                    
                    # XCC values as titles for rows > 0 with conditional formatting
                    if firing_idx > 0 and not np.isnan(xcc):
                        # Vectorized comparison for color selection
                        xcc_color = "black" if xcc >= 0.8 else "red"
                        ax.set_title(f"{xcc:.2f}", fontsize=8, color=xcc_color, pad=3)
                    
                    # Column headers on top row only - use actual matrix code names
                    if firing_idx == 0:
                        col_label = channel_names[ch] if ch < len(channel_names) else f"col{ch}"
                        ax.set_title(col_label, fontsize=8, pad=15, color="black")
                    
                    # Row labels on left column only
                    if ch == 0:
                        ax.set_ylabel(str(firing_idx), fontsize=8, rotation=0, labelpad=5, ha='right')

                # Apply styling using matrix operations on spine properties
                ax.set_xticks([])
                ax.set_yticks([])
                ax.tick_params(left=False, bottom=False)
                
                # Set spine properties using matrix-like operations
                spine_properties = {'linewidth': 0.5, 'color': 'gray', 'visible': True}
                for spine in ax.spines.values():
                    for prop, value in spine_properties.items():
                        setattr(spine, f'_{prop}', value) if prop == 'visible' else spine.set(**{prop: value})
        
        # Apply tight layout with matrix-aware spacing
        fig.tight_layout(pad=0.5, h_pad=0.5, w_pad=0.5)
        self.plot_canvas.draw()

    def fill_results_table(self, table_data):
        self.results_table.setRowCount(len(table_data))
        for i, (idx, cv, rms, xcc) in enumerate(table_data):
            self.results_table.setItem(i, 0, QTableWidgetItem(str(idx)))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{cv:.2f}" if not np.isnan(cv) else ""))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{rms:.2f}" if not np.isnan(rms) else ""))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{xcc:.2f}" if not np.isnan(xcc) else ""))

    def copy_results(self):
        # Copy table to clipboard
        rows = self.results_table.rowCount()
        cols = self.results_table.columnCount()
        text = '\t'.join([self.results_table.horizontalHeaderItem(j).text() for j in range(cols)]) + '\n'
        for i in range(rows):
            text += '\t'.join([self.results_table.item(i, j).text() if self.results_table.item(i, j) else '' for j in range(cols)]) + '\n'
        QApplication.clipboard().setText(text)
