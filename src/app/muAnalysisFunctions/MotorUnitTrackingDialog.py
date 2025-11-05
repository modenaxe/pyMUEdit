# import numpy as np

# from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# import matplotlib.pyplot as plt
# import pandas as pd
# from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
# from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
# from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown
# from app.muAnalysisFunctions.electrode_layouts import get_electrode_grid
# from scipy.signal import correlate2d
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QLineEdit
)

from ui.components.muAnalysisComponents.AnalysisCheckboxDark import \
    AnalysisCheckboxDark
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog

from ui.components import ActionButton
from openhdemg.library import (
    emg_from_otb, emg_from_json, tracking
)

class MotorUnitTrackingDialog(QDialog):

    """
    Motor Unit Tracking Advanced Tool UI and logic.

    Provides a PyQt5 dialog for loading two EMG recordings, computing MU
    matches across files via cross-correlation of MUAP averages, visualising
    IDR and MUAP overlays, and curating inclusion/exclusion for result pairs.

    Args:
        parent (QWidget, optional): Parent widget. Defaults to None.
        matrix_orientation (int|str|None): Electrode grid orientation used by
            get_electrode_grid. Cast to int if provided. Defaults to 0.
        matrix_code (str|None): Electrode grid code for layout lookup.
            Use None if not provided.

    Attributes:
        file1 (dict|None): Parsed EMG data for File 1.
        file2 (dict|None): Parsed EMG data for File 2.
        results (list[tuple[int,int,float]]): [(mu1, mu2, xcc_score), ...].
        inclusion_status (list[str]): Parallel list of "Included"/"Excluded".
        matrix_orientation (int): Orientation passed to grid helper.
        matrix_code (str|None): Grid code passed to grid helper.
    """

    def __init__(self, parent=None, matrix_orientation=None, matrix_code=None, n_rows=None, n_cols=None):
        """
        Initialize the dialog, theme, state, and build the UI.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
            matrix_orientation (int|str|None): Orientation index. Defaults to 0.
            matrix_code (str|None): Electrode grid code. Defaults to None.

        Returns:
            None
        """
        super().__init__(parent)
        self.setWindowTitle("Motor Unit Tracking")
        self.setMinimumWidth(600)
        self.setMinimumHeight(220)
        self.setStyleSheet(self._get_stylesheet())
        self.files = [None, None]
        self.results = []
        self.inclusion_status = []
        self.init_ui()

        self.matrix_orientation = matrix_orientation
        self.matrix_code = "None" if not matrix_code else matrix_code
        self.rows = n_rows
        self.columns = n_cols

    def init_ui(self):
        """
        Build and lay out all UI controls and connect signal handlers.

        Creates file loaders, parameter inputs, plotting canvases, and the results
        table. Wires up selection syncing between widgets.

        Returns:
            None
        """
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # --- File buttons ---
        file1_layout = QHBoxLayout()

        load_file1_btn = ActionButton("Load File 1")
        load_file1_btn.clicked.connect(lambda:self.load_file(0, False))
        load_json1_btn = ActionButton("Load JSON 1")
        load_json1_btn.clicked.connect(lambda:self.load_file(0, True))

        self.file1_label = QLabel("No file selected")
        self.file1_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")

        file1_layout.addWidget(load_file1_btn)
        file1_layout.addWidget(load_json1_btn)
        main_layout.addWidget(self.file1_label)
        main_layout.addLayout(file1_layout)

        file2_layout = QHBoxLayout()

        load_file2_btn = ActionButton("Load File 2")
        load_file2_btn.clicked.connect(lambda:self.load_file(1, False))

        load_json2_btn = ActionButton("Load JSON 2")
        load_json2_btn.clicked.connect(lambda:self.load_file(1, True))

        self.file2_label = QLabel("No file selected")
        self.file2_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")

        file2_layout.addWidget(load_file2_btn)
        file2_layout.addWidget(load_json2_btn)

        main_layout.addWidget(self.file2_label)
        main_layout.addLayout(file2_layout)

        # --- Parameter inputs ---

        param_layout = QHBoxLayout()
        input_layout = QVBoxLayout()

        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Threshold:")
        self.threshold_input = QLineEdit("0.6")
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_input)
        threshold_layout.setSpacing(10)
        input_layout.addLayout(threshold_layout)

        window_layout = QHBoxLayout()
        window_label = QLabel("Time Window (ms):")
        self.window_input = QLineEdit("50")
        window_layout.addWidget(window_label)
        window_layout.addWidget(self.window_input)
        window_layout.setSpacing(10)
        input_layout.addLayout(window_layout)

        # Checkbox parameters
        checkbox_layout = QVBoxLayout()
        self.filter_checkbox = AnalysisCheckboxDark("Filter")
        self.filter_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.filter_checkbox)

        self.exclude_checkbox = AnalysisCheckboxDark("Exclude Below Threshold")
        self.exclude_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.exclude_checkbox)

        # Layout entire parameter section
        param_layout.addLayout(input_layout)
        param_layout.addLayout(checkbox_layout)
        param_layout.addStretch()
        param_layout.setSpacing(5)
        # checkbox_layout.setSpacing(0)
        # input_layout.setSpacing(0)

        main_layout.addLayout(param_layout)

        track_btn = ActionButton("Track")
        track_btn.setFixedHeight(40)
        track_btn.clicked.connect(self.on_track)
        main_layout.addWidget(track_btn)

        main_layout.addSpacing(10)
        main_layout.addStretch()

        """ LEGACY CODE - to be deleted upon client approval """

        # # --- Top controls ---

        # controls_layout = QHBoxLayout()
        # controls_layout.setSpacing(10)
        # self.mu_pair_selector = AnalysisDropdown("Select MU Pair", parent=self)
        # self.mu_pair_selector.currentIndexChanged.connect(self.on_mu_pair_changed)
        # controls_layout.addWidget(QLabel("Pair of MUs to visualise:"))
        # controls_layout.addWidget(self.mu_pair_selector)

        # # --- Add manual input for MU pair ---

        # self.mu_pair_input = QLineEdit()
        # self.mu_pair_input.setPlaceholderText("e.g. 3-7")
        # self.mu_pair_input.setFixedWidth(100)
        # controls_layout.addWidget(self.mu_pair_input)
        # self.mu_pair_input_btn = ActionButton("Go")
        # self.mu_pair_input_btn.setFixedWidth(60)
        # self.mu_pair_input_btn.clicked.connect(self.on_manual_mu_pair_input)
        # controls_layout.addWidget(self.mu_pair_input_btn)

        # # --- End manual input ---

        # self.inclusion_label = QLabel("INCLUDED")
        # self.inclusion_label.setStyleSheet("color: green; font-weight: bold;")
        # controls_layout.addWidget(self.inclusion_label)
        # self.include_btn = ActionButton("Include/Exclude")
        # self.include_btn.clicked.connect(self.toggle_inclusion)
        # controls_layout.addWidget(self.include_btn)
        # controls_layout.addStretch()
        # main_layout.addLayout(controls_layout)

        # # --- Middle: Plots ---

        # plots_layout = QHBoxLayout()

        # # Left: MUAP grids
        # muap_grids_layout = QVBoxLayout()

        # muap_grids_layout.addWidget(QLabel("MUAP Overlay Grid"))
        # self.muap_fig1, _ = plt.subplots(8, 8, figsize=(3, 3))  # Size can be changed if needed
        # self.muap_canvas1 = FigureCanvas(self.muap_fig1)
        # muap_grids_layout.addWidget(self.muap_canvas1)

        # plots_layout.addLayout(muap_grids_layout)

        # # Right: IDR plots
        # idr_plots_layout = QVBoxLayout()

        # self.fig1, self.ax1 = plt.subplots(figsize=(2.9, 1.4), constrained_layout=True)
        # self.canvas1 = FigureCanvas(self.fig1)
        # idr_plots_layout.addWidget(self.canvas1)

        # self.fig2, self.ax2 = plt.subplots(figsize=(2.9, 1.4), constrained_layout=True)

        # self.canvas2 = FigureCanvas(self.fig2)
        # idr_plots_layout.addWidget(self.canvas2)
        # plots_layout.addLayout(idr_plots_layout)
        # main_layout.addLayout(plots_layout)

        # # --- Bottom: Results table ---

        # self.table = QTableWidget()
        # self.table.setColumnCount(4)
        # self.table.setHorizontalHeaderLabels(["MU_file1", "MU_file2", "XCC", "Inclusion"])
        # header = self.table.horizontalHeader()
        # if header is not None:
        #     header.setSectionResizeMode(QHeaderView.Stretch)
        # self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        # self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        # self.table.setMinimumHeight(100)
        # self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # main_layout.addWidget(self.table, stretch=2)

        self.setLayout(main_layout)

    def _get_stylesheet(self):
        """
        Build the Qt stylesheet string for the dialog.

        Returns:
            str: Stylesheet (QSS) applied to the dialog and child widgets.
        """

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
        """

    def load_file(self, n, json):
        """
        Prompt for and load file (.mat), updating the label and state.

        Returns:
            None

        Raises:
            ValueError: Propagated as a user dialog if loading fails.
        """
        labels = [self.file1_label, self.file2_label]

        if json:
            text = f"Select JSON File {n + 1}"
            file_type = "JSON Files (*.json *.json.gz);;All Files (*)"
        else:
            text = f"Select File {n + 1}"
            file_type = "MAT Files (*.mat)"

        file_path, _ = QFileDialog.getOpenFileName(self, text, "", file_type)

        if file_path:
            labels[n].setText(os.path.basename(file_path))
            try:
                if json:
                    self.files[n] = emg_from_json(file_path)
                else:
                    self.files[n] = emg_from_otb(file_path)
            except Exception as e:
                error_message = "JSON" if json else ""
                ErrorDialog(f"Failed to load {error_message} File {n + 1}:\n{str(e)}", 'Error').exec_()

    def on_track(self):
        """
        Run MU tracking between File 1 and File 2 using openHDEMG GUI

        Returns:
            None

        Raises:
            ValueError: If threshold/time window parsing fails.
        """

        file_1 = self.files[0]
        file_2 = self.files[1]

        if file_1 is None or file_2 is None:
            ErrorDialog("Both files must be selected", 'Error').exec_()
            return

        try:
            threshold = float(self.threshold_input.text())
            time_window_ms = int(self.window_input.text())
            matrix_code = self.matrix_code
            orientation = self.matrix_orientation
            n_rows = self.rows
            n_cols = self.columns
            exclude_belowthreshold = self.exclude_checkbox.isChecked()
            to_filter = self.filter_checkbox.isChecked()

            tracking(
                emgfile1=file_1,
                emgfile2=file_2,
                threshold=threshold,
                timewindow=time_window_ms,
                matrixcode=matrix_code,
                orientation=orientation,
                n_cols=n_cols,
                n_rows=n_rows,
                exclude_belowthreshold=exclude_belowthreshold,
                filter=to_filter
            )

        except Exception as e:
            ErrorDialog(e, 'Error').exec_()
            return

    """ LEGACY CODE - to be deleted upon client approval """

    # def get_sta(self, emgfile, code, orientation, n_cols, n_rows):
    #     """Compute spike-triggered average for one MU.

    #     Args:
    #         file (dict): Parsed EMG data.
    #         mu_index (int): MU index to compute STA for.
    #         window (int): Half-window size in samples.

    #     """

    #     sorted_rawemg = sort_rawemg(
    #         emgfile=emgfile,
    #         code=code,
    #         orientation=orientation,
    #         n_cols=n_cols,
    #         n_rows=n_rows
    #     )

    #     d = diff(sorted_rawemg)
    #     return sta(emgfile, d)

    # def display_results(self, results):
    #     """
    #     Populate the table and selector with tracking results.

    #     Args:
    #         results (list[tuple[int,int,float]]): Pairs and scores to display.

    #     Returns:
    #         None
    #     """
    #     self.results = results
    #     self.inclusion_status = ["Included"] * len(results)
    #     self.table.setRowCount(0)
    #     self.mu_pair_selector.clear()
    #     for i, (ch1, ch2, score) in enumerate(results):
    #         self.table.insertRow(i)
    #         self.table.setItem(i, 0, QTableWidgetItem(str(ch1)))
    #         self.table.setItem(i, 1, QTableWidgetItem(str(ch2)))
    #         self.table.setItem(i, 2, QTableWidgetItem(f"{score:.3f}"))
    #         self.table.setItem(i, 3, QTableWidgetItem(self.inclusion_status[i]))
    #         self.mu_pair_selector.addItem(f"{ch1}-{ch2}")
    #     if results:
    #         self.table.selectRow(0)
    #         self.mu_pair_selector.setCurrentIndex(0)
    #         self.update_plots(0)
    #     else:
    #         self.clear_all_plots()

    # def on_table_selection_changed(self):
    #     """Synchronizes table selection with dropdown and updates plots.
    #     Params: None
    #     Returns: None
    #     """

    #     selected = self.table.selectedItems()
    #     if selected and len(selected) >= 1:
    #         row = selected[0].row()
    #         self.mu_pair_selector.setCurrentIndex(row)
    #         self.update_plots(row)

    # def on_mu_pair_changed(self, idx):
    #     """Handles MU pair dropdown changes.
    #     Args:
    #         idx (int): Selected index in results.
    #     Returns:
    #         None
    #     """

    #     if idx >= 0 and idx < len(self.results):
    #         self.table.selectRow(idx)
    #         self.update_plots(idx)

    # def update_plots(self, idx):
    #     """
    #     Refresh all plots for the selected MU pair.

    #     Plots IDR for each file and overlays MUAP grids using the configured
    #     electrode layout. Also updates the inclusion label.

    #     Args:
    #         idx (int): Index into self.results for the selected pair.

    #     Returns:
    #         None
    #     """

    #     # --- Update all plots and grids for the selected MU pair ---
    #     ch1, ch2, _ = self.results[idx]
    #     file_1, file_2 = self.files[0], self.files[1]
    #     # IDR plots
    #     self.plot_idr(file_1, ch1, self.ax1, self.canvas1,color='blue')
    #     self.plot_idr(file_2, ch2, self.ax2, self.canvas2,color='orange')
    #     # MUAP grids

    #     self.plot_muap_grid_overlay(file_1, ch1, file_2, ch2, self.muap_fig1, self.muap_canvas1)

    #     # Inclusion label
    #     self.inclusion_label.setText(self.inclusion_status[idx].upper())
    #     self.inclusion_label.setStyleSheet(
    #         "color: green; font-weight: bold;" if self.inclusion_status[idx] == "Included" else "color: red; font-weight: bold;"
    #     )

    # def clear_all_plots(self):
    #     """
    #     Clear and redraw all figures/canvases to a blank state.

    #     Returns:
    #         None
    #     """
    #     self.fig1.clf()
    #     self.canvas1.draw()
    #     self.fig2.clf()
    #     self.canvas2.draw()
    #     self.muap_fig1.clf()
    #     self.muap_canvas1.draw()
    #     self.muap_fig2.clf()
    #     self.muap_canvas2.draw()

    # def toggle_inclusion(self):
    #     """
    #     Toggle Included/Excluded status for the currently selected MU pair.

    #     Updates the table cell and status label styling accordingly.

    #     Returns:
    #         None
    #     """
    #     idx = self.mu_pair_selector.currentIndex()
    #     if idx >= 0 and idx < len(self.inclusion_status):
    #         if self.inclusion_status[idx] == "Included":
    #             self.inclusion_status[idx] = "Excluded"
    #         else:
    #             self.inclusion_status[idx] = "Included"
    #         self.table.setItem(idx, 3, QTableWidgetItem(self.inclusion_status[idx]))
    #         self.inclusion_label.setText(self.inclusion_status[idx].upper())
    #         self.inclusion_label.setStyleSheet(
    #             "color: green; font-weight: bold;" if self.inclusion_status[idx] == "Included" else "color: red; font-weight: bold;"
    #         )

    # # --- Add handler for manual MU pair input ---
    # def on_manual_mu_pair_input(self):
        # """
        # Jump to a specific MU pair typed as 'a-b' and update views.

        # Parses user text (e.g., '3-7'), finds the matching pair in self.results,
        # and selects it. Shows an error dialog if parsing or lookup fails.

        # Returns:
        #     None

        # Raises:
        #     ValueError: If the typed pair is not in 'int-int' format.
        # """

        # text = self.mu_pair_input.text().strip()
        # if '-' not in text:
        #     ErrorDialog("Invalid Motor unit provided", 'Error').exec_()
        #     return
        # try:
        #     mu1_str, mu2_str = text.split('-', 1)
        #     mu1 = int(mu1_str)
        #     mu2 = int(mu2_str)
        # except Exception:
        #     ErrorDialog("Invalid Motor unit provided", 'Error').exec_()
        #     return
        # # Find the index in results
        # found_idx = -1
        # for idx, (ch1, ch2, _) in enumerate(self.results):
        #     if ch1 == mu1 and ch2 == mu2:
        #         found_idx = idx
        #         break
        # if found_idx == -1:
        #     ErrorDialog("Invalid Motor unit provided", 'Error').exec_()
        #     return
        # # Update selection
        # self.mu_pair_selector.setCurrentIndex(found_idx)
        # self.table.selectRow(found_idx)
        # self.update_plots(found_idx)