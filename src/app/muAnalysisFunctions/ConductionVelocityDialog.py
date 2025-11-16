from PyQt5.QtWidgets import *
import numpy as np
import traceback
import matplotlib.pyplot as plt
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from app.muAnalysisFunctions.electrode_layouts import get_electrode_grid

from ui.components import ActionButton

from openhdemg.library import plot_muaps_for_cv, sta, xcc_sta, sort_rawemg, double_diff, estimate_cv_via_mle, MUcv_gui

# --- Helper Functions ---
def get_sta_xcc(emgfile, code, orientation, n_cols, n_rows):

    """
    Compute STA and XCC dictionaries for given EMG file and electrode configuration.

    Params:
        - emgfile: EMG file dictionary containing RAW_SIGNAL and MUPULSES
        - code: Electrode grid code (e.g., "GR08MM1305")
        - orientation: Orientation of the electrode grid (0 or 180 degrees)
        - n_cols: Number of columns in the electrode grid
        - n_rows: Number of rows in the electrode grid

    Returns:
        - sta_dict: Dictionary of spike-triggered averages for each motor unit
        - xcc_dict: Dictionary of cross-correlation values for each motor unit
    """

    sorted_rawemg = sort_rawemg(
        emgfile=emgfile,
        code=code,
        orientation=orientation,
        n_cols=n_cols,
        n_rows=n_rows
    )

    dd = double_diff(sorted_rawemg)
    sta_dict = sta(emgfile, dd)
    xcc_dict = xcc_sta(sta_dict)

    return sta_dict, xcc_dict

def get_emg_data(key, default=None):
    """Helper to safely get EMG data from the loaded file.

    Args:
        key: Dictionary key to retrieve from EMG file
        default: Default value to return if key not found or file not loaded

    Returns:
        Value from EMG file or default value
    """
    emgfile = FileUploadFunc.file
    return emgfile.get(key, default) if emgfile else default

def get_available_mus():
    """Get list of available motor unit indices from loaded EMG file.

    Returns:
        List of motor unit indices (0 to NUMBER_OF_MUS-1)
    """
    return list(range(get_emg_data("NUMBER_OF_MUS", 0)))

def get_available_grid_rows(st):
    """Get list of available electrode grid row indices.
    Params:
        st: Spike-triggered average dictionary

    Returns:
        List of string representations of row indices
    """

    columns = get_available_grid_columns(st)

    # reformat column key
    first_column = columns[0]
    col = f"col{first_column}"

    return list(range(len(list(st[0][col].columns))))

def get_available_grid_columns(st):
    """Get list of available electrode grid column indices.

    Params:
        st: Spike-triggered average dictionary

    Returns:
        List of string representations of column indices
    """

    return list(range(len(st[0].keys())))  # 5 columns for GR08MM1305

class ConductionVelocityDialog(QDialog):
    def __init__(
            self,
            parent=None,
            matrix_orientation=180,
            matrix_code="GR08MM1305",
            n_rows=None,
            n_cols=None
    ):
        super().__init__(parent)
        self.setWindowTitle("MUs CV estimation")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(self._get_stylesheet())

        # Cache for performance
        self._electrode_grid_cache = None
        self._electrode_positions_cache = None

        self.code = "None" if not matrix_code else matrix_code
        self.orientation = matrix_orientation

        self.rows = n_rows
        self.columns = n_cols

        self._init_ui()
        self._load_initial_data()

    def _get_stylesheet(self):
        """Return consolidated stylesheet for the dialog.

        Returns:
            String containing CSS stylesheet for dialog styling
        """
        return f"""
            QDialog {{ background: {CleanTheme.BG_CARD}; }}
            QLabel {{ color: {CleanTheme.TEXT_PRIMARY}; font-size: 14px; }}
            QGroupBox {{
                border: 1px solid {CleanTheme.BORDER}; border-radius: 6px;
                margin-top: 10px; background: {CleanTheme.BG_CARD};
            }}
            QGroupBox:title {{
                subcontrol-origin: margin; left: 10px; padding: 0 3px;
                color: {CleanTheme.TEXT_SECONDARY};
            }}
            QComboBox, QSpinBox, QTextEdit {{
                background: {CleanTheme.BG_CARD}; color: {CleanTheme.TEXT_PRIMARY};
                border: 1px solid {CleanTheme.BORDER}; border-radius: 4px; font-size: 14px;
            }}
            QPushButton {{
                background: {CleanTheme.ANALYSIS_BG_BUTTON}; color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                border-radius: 5px; padding: 6px 16px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {CleanTheme.ANALYSIS_BG_DROPDOWN}; }}
        """

    def _create_dropdown_group(self, title, items, default_index=0):
        """Helper to create dropdown groups with error handling.

        Args:
            title: Title for the dropdown group
            items: List of items to populate the dropdown
            default_index: Index of default selection

        Returns:
            Tuple of (group_widget, dropdown_widget)
        """
        group = QGroupBox(title)
        layout = QVBoxLayout()
        dropdown = QComboBox()

        try:
            if items:
                dropdown.addItems([str(item) for item in items])
                if default_index < len(items):
                    dropdown.setCurrentIndex(default_index)
            else:
                dropdown.addItem("No data loaded")
        except Exception as e:
            print(f"Error loading {title}: {e}")
            dropdown.addItem("Error loading data")

        layout.addWidget(dropdown)
        group.setLayout(layout)
        return group, dropdown

    def _init_ui(self):
        """Initialize the user interface components and layout.

        Sets up dropdowns, buttons, plot canvas, and results table with proper styling and connections.
        """
        main_layout = QVBoxLayout()

        # Controls layout
        controls_layout = QHBoxLayout()

        # Create dropdowns
        mu_group, self.mu_dropdown = self._create_dropdown_group(
            "MU number", []
        )
        self.mu_dropdown.setObjectName("mu_dropdown")

        col_group, self.col_dropdown = self._create_dropdown_group(
            "Grid Column", []
        )
        self.col_dropdown.setObjectName("col_dropdown")

        # Row selection group
        row_group = QGroupBox("Grid Rows")
        row_layout = QHBoxLayout()

        self.from_row_dropdown = QComboBox()
        self.to_row_dropdown = QComboBox()

        try:
            self.from_row_dropdown.addItem("No data loaded")
            self.to_row_dropdown.addItem("No data loaded")
        except Exception as e:
            print(f"Error loading grid rows: {e}")
            self.from_row_dropdown.addItem("Error loading data")
            self.to_row_dropdown.addItem("Error loading data")

        row_layout.addWidget(QLabel("From:"))
        row_layout.addWidget(self.from_row_dropdown)
        row_layout.addWidget(QLabel("To:"))
        row_layout.addWidget(self.to_row_dropdown)
        row_group.setLayout(row_layout)

        # Estimate button
        self.estimate_btn = ActionButton("Estimate")
        self.estimate_btn.clicked.connect(self._on_estimate)
        self.estimate_btn.setMinimumHeight(40)

        # Add to controls
        for widget in [mu_group, col_group, row_group, self.estimate_btn]:
            controls_layout.addWidget(widget)
        main_layout.addLayout(controls_layout)

        # Content layout
        content_layout = QHBoxLayout()

        # Plot canvas
        self.plot_canvas = FigureCanvas(plt.Figure(figsize=(8, 6)))
        content_layout.addWidget(self.plot_canvas, stretch=3)

        # Results area
        results_layout = QVBoxLayout()
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(
            ["Column", "CV (m/s)", "RMS (µV)", "XCC"]
        )
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        copy_btn = ActionButton("Copy results")
        copy_btn.clicked.connect(self._copy_results)
        self.estimate_btn.setMinimumHeight(40)

        results_layout.addWidget(self.results_table)
        results_layout.addWidget(copy_btn)
        content_layout.addLayout(results_layout, stretch=1)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # Connect signals
        self.mu_dropdown.currentTextChanged.connect(self._update_plot)

    def _load_initial_data(self):
        """Load initial data and update UI components.

        Checks if EMG file is loaded, refreshes dropdowns, and updates the plot display.
        Shows appropriate error messages if no data is available.
        """
        try:
            emgfile = FileUploadFunc.file

            if emgfile is None:
                self._show_message(
                    "No EMG file loaded\nLoad EMG data to see conduction velocity analysis"
                )
            else:
                self.sta, xcc_values = get_sta_xcc(
                    emgfile,
                    code=self.code,
                    orientation=self.orientation,
                    n_cols=self.columns,
                    n_rows=self.rows
                )

                file_channels = len(emgfile["RAW_SIGNAL"].columns)

                if self.rows and self.columns:
                    self.channels = int(self.rows) * int(self.columns)
                else:
                    self.channels = None

                if self.channels and self.channels != file_channels:
                    raise ValueError(
                        f"{self.rows} rows and {self.columns} cols specified do not match {file_channels} channels in file"
                    )

            self._refresh_dropdowns()
            self._update_plot()
        except Exception as e:
            self._show_message(f"Error initializing: {str(e)}")

    def _refresh_dropdowns(self):
        """Refresh all dropdowns with current data from loaded EMG file.

        Updates motor unit, column, and row selection dropdowns with available options
        based on the currently loaded data.
        """

        emgfile = FileUploadFunc.file

        if emgfile is None:
            return

        try:
            # Refresh dropdowns
            dropdowns_data = [
                (self.mu_dropdown, get_available_mus()),
                (self.col_dropdown, get_available_grid_columns(self.sta)),
            ]

            for dropdown, data in dropdowns_data:
                dropdown.clear()
                if data:
                    if dropdown.objectName() == "col_dropdown":
                        dropdown.addItems(["col" + str(item) for item in data])
                    else:
                        dropdown.addItems([str(item) for item in data])
                else:
                    dropdown.addItem("No data loaded")

            # Refresh row dropdowns
            available_rows = get_available_grid_rows(self.sta)
            if available_rows:
                # Clear and repopulate from_row_dropdown
                self.from_row_dropdown.clear()
                self.from_row_dropdown.addItems(str(item) for item in available_rows)
                self.from_row_dropdown.setCurrentIndex(0)

                # Clear and repopulate to_row_dropdown
                self.to_row_dropdown.clear()
                self.to_row_dropdown.addItems(str(item) for item in available_rows)
                self.to_row_dropdown.setCurrentIndex(len(available_rows) - 1)
            else:
                self.from_row_dropdown.clear()
                self.from_row_dropdown.addItem("No data loaded")
                self.to_row_dropdown.clear()
                self.to_row_dropdown.addItem("No data loaded")

        except Exception as e:
            print(f"Error refreshing dropdowns: {e}")

    def _show_message(self, message):
        """Show message in plot area when no data is available or error occurs.

        Args:
            message: Text message to display in the center of the plot area
        """
        fig = self.plot_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12)
        self.plot_canvas.draw()
        self.results_table.setRowCount(0)

    def _get_ui_values(self):
        """Get current UI values safely with error handling.

        Returns:
            Dictionary containing current MU number, column, from_row, and to_row selections
        """

        def safe_int(text, default):
            return (
                default
                if text in ["No data loaded", "Error loading data", ""]
                else int(text.replace("col", ""))
            )

        return {
            "mu": safe_int(self.mu_dropdown.currentText(), 0),
            "col": safe_int(self.col_dropdown.currentText(), 0),
            "from_row": safe_int(self.from_row_dropdown.currentText(), 0),
            "to_row": safe_int(self.to_row_dropdown.currentText(), 10),
        }

    def _update_plot(self):
        """Update plot based on current dropdown selections.

        Redraws the MUAP grid visualization when user changes MU or column selection.
        Shows error message if no EMG file is loaded.
        """
        try:
            if FileUploadFunc.file is not None:
                self._plot_muap_grid()
                self.results_table.setRowCount(0)
            else:
                self._show_message("No EMG file loaded\nPlease load data first")
        except Exception as e:
            print(f"Error updating plot: {e}")
            self._show_message(f"Error: {str(e)}")

    def _on_estimate(self):
        """Perform CV estimation when estimate button is clicked.

        Retrieves current UI values, computes conduction velocity results for all columns,
        and updates the results table with CV, RMS, and XCC values.
        """
        try:
            values = self._get_ui_values()
            table_data = self._compute_results(
                values["mu"], values["col"], values["from_row"], values["to_row"]
            )
            self._fill_results_table(table_data)
        except Exception as e:
            self.results_table.setRowCount(1)
            for i, text in enumerate(["Error", str(e), "", ""]):
                self.results_table.setItem(0, i, QTableWidgetItem(text))
            print(f"Error in estimation: {e}")
            traceback.print_exc()

    def _on_estimate_openhdemg(self):
        """
        Function stub to launch OpenHDEMG's MUcv_GUI for conduction velocity estimation.
        Currently unused as MUcv_GUI does not have a way of returning results yet.
        """

        emgfile = FileUploadFunc.file
        if emgfile is None:
            self._show_message("No EMG file loaded")
            return

        sorted_rawemg = sort_rawemg(
            emgfile=emgfile,
            code=self.code,
            orientation=self.orientation,
            n_cols=self.columns,
            n_rows=self.rows
        )

        MUcv_gui(emgfile, sorted_rawemg)

    def _compute_results(self, mu, selected_col, from_row, to_row):
        """Compute CV estimation results using reference method.

        Args:
            mu: Motor unit index for analysis
            selected_col: Selected column index
            from_row: Starting row for analysis range
            to_row: Ending row for analysis range

        Returns:
            List of tuples containing (column_name, cv_value, rms_value, xcc_value) for each column
        """
        emgfile = FileUploadFunc.file
        if emgfile is None:
            return []

        sta_dict, xcc = get_sta_xcc(
            emgfile,
            code=self.code,
            orientation=self.orientation,
            n_cols=self.columns,
            n_rows=self.rows
        )

        sta_rows = list(range(from_row, to_row + 1))
        xcc_rows = list(range(from_row + 1, to_row +1))

        sta_data = sta_dict[mu]
        xcc_data = xcc[mu]

        if not sta_data:
            return []

        table_data = []

        # Process each column
        for col_name in sorted(
            sta_data.keys(), key=lambda x: int(x.replace("col", ""))
        ):
            col_data = sta_data[col_name].iloc[:, sta_rows]
            if col_data.shape[1] < 2:
                continue

            try:
                # Estimate CV, RMS, and XCC
                cv_value = estimate_cv_via_mle(emgfile, col_data)

                sig = col_data.to_numpy()
                rms = np.mean(np.sqrt((np.mean(sig**2, axis=0))))
                avg_rms = rms * 1000  # Convert to µV

                avg_xcc = xcc_data[col_name].iloc[:, xcc_rows].mean().mean()

                # Only include reasonable CV values
                # if not np.isnan(cv_value) and 0.5 <= cv_value <= 15.0:
                table_data.append((col_name, cv_value, avg_rms, avg_xcc))

            except Exception as e:
                print(f"Error processing column {col_name}: {e}")
                continue

        return table_data

    def _plot_muap_grid(self):
        """Plot MUAP grid with XCC values displayed on each electrode.

        Creates a grid visualization of motor unit action potentials (MUAPs) for the selected MU,
        showing the signal at each electrode position with cross-correlation values overlaid.
        """

        # Get parameters
        emgfile = FileUploadFunc.file
        if emgfile is None:
            self._show_message("No EMG file loaded")
            return

        fig = self.plot_canvas.figure
        fig.clear()

        sta_dict, xcc_values = get_sta_xcc(
            emgfile,
            code=self.code,
            orientation=self.orientation,
            n_cols=self.columns,
            n_rows=self.rows
        )

        values = self._get_ui_values()

        mu = values["mu"]
        muaps = sta_dict[mu]

        if muaps is None:
            self._show_message("MUAPs not available")
            return

        self.plot_canvas.figure = plot_muaps_for_cv(
            sta_dict=sta_dict[mu],
            xcc_sta_dict=xcc_values[mu],
            showimmediately=False
        )

        self.plot_canvas.draw()

    def _fill_results_table(self, table_data):
        """Fill results table with computed CV estimation data.

        Args:
            table_data: List of tuples containing (column, cv, rms, xcc) values for each column
        """
        self.results_table.clearContents()
        self.results_table.setRowCount(len(table_data))

        for row, (column, cv, rms, xcc) in enumerate(table_data):
            items = [
                str(column),
                f"{cv:.2f}",
                f"{rms:.1f}",
                f"{xcc:.3f}" if not np.isnan(xcc) else "N/A",
            ]
            for col, text in enumerate(items):
                self.results_table.setItem(row, col, QTableWidgetItem(text))

        self.results_table.resizeColumnsToContents()

    def _copy_results(self):
        """Copy results table data to clipboard in tab-separated format.

        Copies both headers and data rows to allow pasting into spreadsheet applications.
        """
        rows, cols = self.results_table.rowCount(), self.results_table.columnCount()

        # Header
        text = (
            "\t".join(
                [self.results_table.horizontalHeaderItem(j).text() for j in range(cols)]
            )
            + "\n"
        )

        # Data rows
        for i in range(rows):
            row_data = []
            for j in range(cols):
                item = self.results_table.item(i, j)
                row_data.append(item.text() if item else "")
            text += "\t".join(row_data) + "\n"

        QApplication.clipboard().setText(text)

    def refresh_with_new_data(self):
        """Public method to refresh dialog when new EMG data is loaded.

        Clears cached data, refreshes dropdown options, and updates the plot display
        to reflect the newly loaded EMG file.
        """
        self._electrode_grid_cache = None
        self._electrode_positions_cache = None
        self._refresh_dropdowns()
        self._update_plot()


    """ DEPRECATED FUNCTIONS - to be removed when client approval """


    # def _get_electrode_grid_cached(self):
    #     """Get electrode grid with caching for performance optimization.

    #     Returns:
    #         Tuple of (electrode_grid, electrode_positions_dict) with cached electrode layout data
    #     """
    #     if self._electrode_grid_cache is None:
    #         try:
    #             self._electrode_grid_cache = get_electrode_grid(
    #                 code="GR08MM1305", orientation=180
    #             )
    #             self._electrode_positions_cache = {}
    #             for r in range(len(self._electrode_grid_cache)):
    #                 for c in range(len(self._electrode_grid_cache[0])):
    #                     ch = self._electrode_grid_cache[r][c]
    #                     if not np.isnan(ch):
    #                         self._electrode_positions_cache[int(ch)] = (r, c)
    #         except:
    #             self._electrode_grid_cache = None
    #             self._electrode_positions_cache = {}
    #     return self._electrode_grid_cache, self._electrode_positions_cache

    #     def _compute_sta(self, emgfile, mu, from_row, to_row):
    #     """Compute spike-triggered average for all columns within specified row range.

    #     Args:
    #         emgfile: EMG file dictionary containing RAW_SIGNAL and MUPULSES
    #         mu: Motor unit index for pulse extraction
    #         from_row: Starting row index for channel selection
    #         to_row: Ending row index for channel selection

    #     Returns:
    #         Dictionary with column names as keys and DataFrames of spike-triggered averages as values
    #     """
    #     raw_signal = emgfile.get("RAW_SIGNAL")
    #     mu_pulses = emgfile.get("MUPULSES")

    #     if raw_signal is None or mu_pulses is None:
    #         return {}

    #     if isinstance(raw_signal, dict):
    #         raw_signal = pd.DataFrame(raw_signal)

    #     # Get pulses
    #     if isinstance(mu_pulses, (list, tuple)) and mu < len(mu_pulses):
    #         pulses = np.array(mu_pulses[mu], dtype=int)
    #     else:
    #         return {}

    #     if len(pulses) == 0:
    #         return {}

    #     window = 50
    #     grid, _ = self._get_electrode_grid_cached()

    #     # Organize channels by columns
    #     column_channels = {}
    #     if grid is not None:
    #         for r in range(max(0, from_row), min(11, to_row + 1)):
    #             for c in range(len(grid[0])):
    #                 ch = grid[r][c]
    #                 if not np.isnan(ch):
    #                     col_name = f"col{c}"
    #                     if col_name not in column_channels:
    #                         column_channels[col_name] = []
    #                     column_channels[col_name].append(int(ch))
    #     else:
    #         # Fallback organization
    #         for c in range(5):
    #             col_name = f"col{c}"
    #             channels = [
    #                 r * 5 + c
    #                 for r in range(max(0, from_row), min(11, to_row + 1))
    #                 if r * 5 + c < raw_signal.shape[1]
    #             ]
    #             if channels:
    #                 column_channels[col_name] = channels

    #     # Filter valid pulses
    #     valid_pulses = pulses[
    #         (pulses >= window) & (pulses + window < raw_signal.shape[0])
    #     ]
    #     if len(valid_pulses) < 3:
    #         return {}

    #     raw_signal_array = raw_signal.values
    #     sta_data = {}

    #     # Compute STA for each column
    #     for col_name, channels in column_channels.items():
    #         if len(channels) < 2:
    #             continue

    #         valid_channels = [ch for ch in channels if ch < raw_signal_array.shape[1]]
    #         if len(valid_channels) < 2:
    #             continue

    #         # Extract and average segments
    #         sta_by_channel = {}
    #         for ch in valid_channels:
    #             segments = []
    #             for pulse in valid_pulses:
    #                 start, end = pulse - window, pulse + window + 1
    #                 segment = raw_signal_array[start:end, ch]
    #                 segments.append(segment - np.mean(segment))

    #             if len(segments) >= 3:
    #                 sta_by_channel[ch] = np.mean(segments, axis=0)

    #         if len(sta_by_channel) >= 2:
    #             sta_data[col_name] = pd.DataFrame(sta_by_channel)

    #     return sta_data

    # def _compute_xcc(self, sta_data):
    #     """Compute cross-correlation between adjacent channels in each column.

    #     Args:
    #         sta_data: Dictionary containing spike-triggered average data by column

    #     Returns:
    #         Dictionary with same structure as sta_data but containing cross-correlation values
    #     """
    #     xcc_sta = copy.deepcopy(sta_data)

    #     for col_name in sta_data:
    #         df = sta_data[col_name]
    #         reversed_col = list(reversed(df.columns))

    #         for pos, col in enumerate(reversed_col):
    #             if pos != len(reversed_col) - 1:
    #                 sig1 = df.loc[:, reversed_col[pos]].values
    #                 sig2 = df.loc[:, reversed_col[pos + 1]].values
    #                 xcc = norm_xcorr(sig1, sig2, out="max")
    #             else:
    #                 xcc = np.nan

    #             xcc_sta[col_name][col] = [xcc] * len(df)

    #         xcc_sta[col_name] = xcc_sta[col_name].drop_duplicates()

    #     return xcc_sta

# def norm_xcorr(sig1, sig2, out="max"):
#     """Calculate normalized cross-correlation between two signals.

#     Args:
#         sig1: First signal array
#         sig2: Second signal array
#         out: Output type, either "max" to return maximum correlation or "full" for full correlation array

#     Returns:
#         Maximum absolute correlation value if out="max", otherwise full correlation array
#     """
#     sig1, sig2 = sig1 - np.mean(sig1), sig2 - np.mean(sig2)
#     corr = correlate(sig1, sig2, mode="full")
#     norm_factor = np.sqrt(np.sum(sig1**2) * np.sum(sig2**2))
#     if norm_factor > 0:
#         corr = corr / norm_factor
#     return np.max(np.abs(corr)) if out == "max" else corr


# def find_mle_teta(sig1, sig2, ied, fsamp):
#     """Find initial theta estimate for MLE CV estimation.

#     Args:
#         sig1: First signal array
#         sig2: Second signal array
#         ied: Inter-electrode distance in mm
#         fsamp: Sampling frequency in Hz

#     Returns:
#         Initial theta estimate (1/cv_estimate) for optimization
#     """
#     corr = correlate(sig1, sig2, mode="full")
#     lags = np.arange(-len(sig1) + 1, len(sig1))
#     delay_samples = max(1, abs(lags[np.argmax(np.abs(corr))]))
#     cv_estimate = (ied / 1000) / (delay_samples / fsamp)
#     return 1.0 / cv_estimate if cv_estimate > 0 else 1.0


# def mle_cv_est(sig, initial_teta, ied, fsamp):
#     """Maximum likelihood estimation of conduction velocity.

#     Args:
#         sig: Signal array for CV estimation
#         initial_teta: Initial theta value for optimization
#         ied: Inter-electrode distance in mm
#         fsamp: Sampling frequency in Hz

#     Returns:
#         Tuple of (estimated_cv, optimized_teta) where cv is in m/s
#     """

#     def objective(teta):
#         cv = 1.0 / teta if teta > 0 else 0.1
#         return abs(cv - 3.0)  # Bias towards physiological range

#     try:
#         result = minimize(objective, initial_teta, method="BFGS")
#         teta_opt = result.x[0] if result.success else initial_teta
#         cv = 1.0 / teta_opt if teta_opt > 0 else 1.0 / initial_teta
#     except:
#         cv = 1.0 / initial_teta if initial_teta > 0 else 3.0
#         teta_opt = initial_teta
#     return cv, teta_opt


# def estimate_cv_via_mle(emgfile, signal):
#     """Estimate conduction velocity via maximum likelihood estimation.

#     Args:
#         emgfile: EMG file dictionary containing IED and FSAMP parameters
#         signal: Signal data for CV estimation (DataFrame or array)

#     Returns:
#         Estimated conduction velocity in m/s, or NaN if estimation fails
#     """
#     ied, fsamp = emgfile.get("IED", 8.0), emgfile.get("FSAMP", 2048)
#     sig = (signal.values if hasattr(signal, "values") else signal).T
#     if sig.ndim == 1:
#         return np.nan

#     sig1, sig2 = (sig[1, :], sig[2, :]) if sig.shape[0] > 3 else (sig[0, :], sig[1, :])
#     teta = find_mle_teta(sig1, sig2, ied, fsamp)
#     cv, _ = mle_cv_est(sig, teta, ied, fsamp)
#     return abs(cv)
