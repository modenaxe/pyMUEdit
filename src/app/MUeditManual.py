import os
import sys
import numpy as np
import scipy.io as sio
import pyqtgraph as pg
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QWidget,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QApplication,
    QMainWindow,
    QFileDialog,
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from ui.MUeditManualUI import setup_ui
from core.utils.manual_editing.getsil import getsil
from core.utils.manual_editing.refinesil import refinesil
from core.utils.manual_editing.extendfilter import extendfilter
from core.utils.manual_editing.selection_tools import SelectionTool, process_selection
from core.utils.decomposition.remove_outliers import remove_outliers
from core.utils.decomposition.remove_duplicates import remove_duplicates
from core.utils.decomposition.remove_duplicates_between_arrays import remove_duplicates_between_arrays
from core.utils.decomposition.extend_emg import extend_emg
from core.utils.decomposition.whiten_emg import whiten_emg


class MUeditManual(QMainWindow):
    """
    Manual Motor Unit Editor for EMG Data
    Allows for viewing and editing motor unit discharge patterns.
    """

    # Add signal to return to dashboard if needed
    return_to_dashboard_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize main data structures
        self.filename = None
        self.pathname = None
        self.MUedition = None
        self.Backup = {"lock": 0, "Pulsetrain": None, "Dischargetimes": None}
        self.graphstart = None
        self.graphend = None
        self.roi = None
        self.current_selection = None
        self.mu_checkboxes = []  # Initialize the mu_checkboxes list

        # Set up the UI
        setup_ui(self)

        # Add back button if needed when used in embedded mode
        if parent:
            self.add_back_button()

    def add_back_button(self):
        """Add a back button to return to dashboard when used in embedded mode."""
        # This method is called only when embedded in the dashboard
        back_button = QPushButton("← Back to Dashboard")
        back_button.clicked.connect(self.request_return_to_dashboard)
        back_button.setFixedWidth(200)
        back_button.setStyleSheet(
            """
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """
        )

        # Find a suitable place to add the button
        # Option 1: Add to the main layout if it exists
        if hasattr(self, "main_layout"):
            self.main_layout.addWidget(back_button)
        # Option 2: Create a container for it at the top of the window
        else:
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(10, 10, 10, 0)
            container_layout.addWidget(back_button)
            container_layout.addStretch(1)

            # Insert at the top of the window
            central_widget_layout = self.central_widget.layout()
            if central_widget_layout:
                central_widget_layout.insertWidget(0, container)

    def request_return_to_dashboard(self):
        """Emit signal to request returning to dashboard."""
        self.return_to_dashboard_requested.emit()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Left:
            self.scroll_left_button_pushed()
        elif event.key() == Qt.Key.Key_Right:
            self.scroll_right_button_pushed()
        elif event.key() == Qt.Key.Key_Up:
            self.zoom_in_button_pushed()
        elif event.key() == Qt.Key.Key_Down:
            self.zoom_out_button_pushed()
        elif event.key() == Qt.Key.Key_A:
            self.add_spikes_button_pushed()
        elif event.key() == Qt.Key.Key_D:
            self.delete_spikes_button_pushed()
        elif event.key() == Qt.Key.Key_R:
            self.remove_outliers_button_pushed()
        elif event.key() == Qt.Key.Key_Space:
            self.update_mu_filter_button_pushed()
        elif event.key() == Qt.Key.Key_S:
            self.lock_spikes_button_pushed()
        elif event.key() == Qt.Key.Key_E:
            self.extend_mu_filter_button_pushed()
        else:
            super().keyPressEvent(event)

    # Event handlers
    def select_file_button_pushed(self):
        """Open file dialog to select file for editing and automatically import it."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select file", "", "MAT Files (*.mat);;All Files (*.*)")

        if file_path:
            self.pathname = os.path.dirname(file_path) + "/"
            self.filename = os.path.basename(file_path)
            self.file_path_field.setText(self.filename)

            self.import_data()

    def import_data(self):
        """Import data from selected file."""
        if not self.filename or not self.pathname:
            return

        try:
            filepath = os.path.join(self.pathname, self.filename)
            files = sio.loadmat(filepath)

            # Initialize the MUedition data structure
            self.MUedition = {"edition": {}, "signal": {}, "parameters": {}}

            if "edited" in self.filename:
                self.import_edited_file(files)
            else:
                self.import_decomposed_file(files)

            # Calculate array numbers for each channel
            self.MUedition["edition"]["arraynb"] = np.zeros(self.MUedition["signal"]["data"].shape[0], dtype=int)
            ch1 = 0

            # Use scalar ngrid value
            ngrid = int(self.MUedition["signal"]["ngrid"][0, 0])

            for i in range(ngrid):
                mask = self.MUedition["signal"]["EMGmask"][0, i]
                mask_length = len(mask)
                self.MUedition["edition"]["arraynb"][ch1 : ch1 + mask_length] = i
                ch1 += mask_length

            # Update reference dropdown
            self.reference_dropdown.clear()
            if "auxiliary" in self.MUedition["signal"] and self.MUedition["signal"]["auxiliary"].size > 0:
                if "auxiliaryname" in self.MUedition["signal"]:
                    aux_names = self.MUedition["signal"]["auxiliaryname"][0]
                    for i in range(aux_names.shape[0]):
                        name = aux_names[i]
                        if isinstance(name, np.ndarray) and name.size > 0:
                            self.reference_dropdown.addItem(str(name[0]))
                        else:
                            self.reference_dropdown.addItem(str(name))

            # Update MU checkboxes
            self.update_mu_checkboxes()

            # Set initial view limits
            self.graphstart = self.MUedition["edition"]["time"][0]
            self.graphend = self.MUedition["edition"]["time"][-1]
            self.update_plot_limits()

        except Exception as e:
            import traceback

            print(f"Error importing data: {e}")
            traceback.print_exc()

    def update_mu_checkboxes(self):
        """Update the MU checkboxes based on loaded data using collapsible panels."""
        # Initialize array panels list if it doesn't exist
        if not hasattr(self, "mu_panels"):
            self.mu_panels = []

        # Initialize array "check all" checkboxes list if it doesn't exist
        if not hasattr(self, "array_checkboxes"):
            self.array_checkboxes = []

        # Clear existing checkboxes and panels
        for checkbox in self.mu_checkboxes:
            checkbox.deleteLater()
        self.mu_checkboxes = []

        for checkbox in self.array_checkboxes:
            checkbox.deleteLater()
        self.array_checkboxes = []

        for panel in self.mu_panels:
            panel.deleteLater()
        self.mu_panels = []

        # Clear any existing widgets
        for i in reversed(range(self.mu_checkbox_layout.count())):
            item = self.mu_checkbox_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        # Add checkboxes for each MU
        if not self.MUedition or len(self.MUedition["edition"]["Pulsetrain"]) == 0:
            no_mu_label = QLabel("No MUs loaded")
            no_mu_label.setStyleSheet("color: #333333; font-family: 'Poppins'; font-size: 16pt;")
            self.mu_checkbox_layout.addWidget(no_mu_label)
            # Add stretch to keep items at the top
            self.mu_checkbox_layout.addStretch(1)
            return

        from ui.components import CollapsiblePanel

        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            # Create collapsible panel for this array
            array_panel = CollapsiblePanel(f"Array #{array_idx+1}")
            self.mu_panels.append(array_panel)

            # Create container widget for checkboxes in this array
            checkbox_container = QWidget()
            checkbox_layout = QVBoxLayout(checkbox_container)
            checkbox_layout.setContentsMargins(10, 5, 10, 5)
            checkbox_layout.setSpacing(5)

            # Add "Check All" checkbox at the top
            check_all_checkbox = QCheckBox("Check All")
            check_all_checkbox.setStyleSheet(
                "color: #333333; font-family: 'Poppins'; font-size: 14pt; font-weight: bold;"
            )
            check_all_checkbox.setProperty("array_idx", array_idx)
            check_all_checkbox.stateChanged.connect(self.array_checkbox_state_changed)
            self.array_checkboxes.append(check_all_checkbox)
            checkbox_layout.addWidget(check_all_checkbox)

            # Add separator line
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #cccccc;")
            separator.setMaximumHeight(1)
            checkbox_layout.addWidget(separator)

            # Add MU checkboxes for this array
            has_checkboxes = False
            for mu_idx in range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]):
                has_checkboxes = True
                mu_identifier = f"Array_{array_idx+1}_MU_{mu_idx+1}"

                # Get SIL value if available
                sil_value = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)
                # Simplified display text without array_number
                checkbox_text = f"MU_{mu_idx+1} (SIL: {sil_value:.4f})"

                checkbox = QCheckBox(checkbox_text)
                checkbox.setStyleSheet("color: #333333; font-family: 'Poppins'; font-size: 14pt;")
                checkbox.setObjectName(mu_identifier)  # Keep the full identifier in objectName
                checkbox.setProperty("array_idx", array_idx)  # Store array index for check all functionality
                checkbox.stateChanged.connect(self.mu_checkbox_state_changed)

                self.mu_checkboxes.append(checkbox)
                checkbox_layout.addWidget(checkbox)

            # Only add panel if it has checkboxes
            if has_checkboxes:
                # Add the checkbox container to the panel
                array_panel.add_widget(checkbox_container)
                # Add the panel to the main layout
                self.mu_checkbox_layout.addWidget(array_panel)

        # Add stretch at the end to keep items at the top
        self.mu_checkbox_layout.addStretch(1)

        # Check the first checkbox by default if any exist
        if self.mu_checkboxes:
            self.mu_checkboxes[0].setChecked(True)

    def mu_checkbox_state_changed(self):
        """Handle changes in MU checkbox selection."""
        # Get all checked MUs
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())

        # Update "Check All" checkboxes based on individual selections
        self.update_array_checkboxes()

        # If none are checked, don't update display
        if not checked_mus:
            return

        # Update the display based on selection
        self.display_selected_mus(checked_mus)

    def update_array_checkboxes(self):
        """Update the state of "Check All" checkboxes based on individual MU selections."""
        # Block signals to prevent recursive updates
        for checkbox in self.array_checkboxes:
            checkbox.blockSignals(True)

        # Check each array's checkboxes
        for array_checkbox in self.array_checkboxes:
            array_idx = array_checkbox.property("array_idx")
            if array_idx is None:
                continue

            # Count how many MUs are in this array and how many are checked
            array_mu_count = 0
            array_checked_count = 0

            for mu_checkbox in self.mu_checkboxes:
                if mu_checkbox.property("array_idx") == array_idx:
                    array_mu_count += 1
                    if mu_checkbox.isChecked():
                        array_checked_count += 1

            # Set the array checkbox state
            if array_checked_count == 0:
                array_checkbox.setCheckState(Qt.CheckState.Unchecked)
            elif array_checked_count == array_mu_count:
                array_checkbox.setCheckState(Qt.CheckState.Checked)
            else:
                array_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)

        # Unblock signals
        for checkbox in self.array_checkboxes:
            checkbox.blockSignals(False)

    def import_edited_file(self, files):
        """Import data from a previously edited file."""
        if not self.MUedition:
            return

        # Copy structured data from MATLAB file
        edition_data = files["edition"][0, 0]
        for field in edition_data.dtype.names:
            self.MUedition["edition"][field] = edition_data[field]

        signal_data = files["signal"][0, 0]
        for field in signal_data.dtype.names:
            self.MUedition["signal"][field] = signal_data[field]

        if "parameters" in files:
            parameters_data = files["parameters"][0, 0]
            for field in parameters_data.dtype.names:
                self.MUedition["parameters"][field] = parameters_data[field]

    def import_decomposed_file(self, files):
        """Import data from a new decomposition file that hasn't been edited yet."""
        if not self.MUedition:
            return

        signal_data = files["signal"][0, 0]

        # Copy signal fields
        for field in signal_data.dtype.names:
            self.MUedition["signal"][field] = signal_data[field]

        # Copy parameters if available
        if "parameters" in files:
            parameters_data = files["parameters"][0, 0]
            for field in parameters_data.dtype.names:
                self.MUedition["parameters"][field] = parameters_data[field]

        # Initialize edition data structures
        self.MUedition["edition"]["Pulsetrain"] = []
        self.MUedition["edition"]["Dischargetimes"] = {}
        self.MUedition["edition"]["silval"] = {}
        self.MUedition["edition"]["silvalcon"] = {}

        # Extract scalar values
        ngrid = int(self.MUedition["signal"]["ngrid"][0, 0])
        fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])

        # Calculate time vector
        signal_length = self.MUedition["signal"]["data"].shape[1]
        self.MUedition["edition"]["time"] = np.linspace(0, signal_length / fsamp, signal_length)

        # Copy Pulsetrain data
        pulsetrain_data = self.MUedition["signal"]["Pulsetrain"][0]

        # Handle as a 1D array
        for i in range(len(pulsetrain_data)):
            self.MUedition["edition"]["Pulsetrain"].append(pulsetrain_data[i])

        # Copy Dischargetimes
        dischargetimes_data = self.MUedition["signal"]["Dischargetimes"]
        for i in range(dischargetimes_data.shape[0]):
            for j in range(dischargetimes_data.shape[1]):
                # Get the discharge times array and check if it's not empty
                dt = dischargetimes_data[i, j]
                if dt.size > 0:
                    # Flatten and store as tuple key (array_idx, mu_idx)
                    self.MUedition["edition"]["Dischargetimes"][(i, j)] = dt.flatten()

        # Calculate SIL values for each motor unit
        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

            for mu_idx in range(pulse_train.shape[0]):
                if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                    self.calculate_silval(array_idx, mu_idx)

    def calculate_silval(self, array_idx, mu_idx):
        """Calculate silhouette value for a motor unit."""
        if not self.MUedition:
            return

        if "silval" not in self.MUedition["edition"]:
            self.MUedition["edition"]["silval"] = {}

        if "silvalcon" not in self.MUedition["edition"]:
            self.MUedition["edition"]["silvalcon"] = {}

        # Calculate SIL value
        discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

        # Store it back
        self.MUedition["edition"]["Dischargetimes"][(array_idx, mu_idx)] = discharge_times

        if len(discharge_times) > 2:
            try:
                if self.MUedition["signal"]["fsamp"].ndim > 1:
                    fsamp = float(self.MUedition["signal"]["fsamp"][0][0])
                else:
                    fsamp = float(self.MUedition["signal"]["fsamp"][0])

                # Calculate silhouette value
                self.MUedition["edition"]["silval"][(array_idx, mu_idx)] = getsil(
                    self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :], fsamp
                )

                # Calculate continuous silhouette values
                self.MUedition["edition"]["silvalcon"][(array_idx, mu_idx)] = refinesil(
                    self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :], discharge_times, fsamp
                )

            except Exception as e:
                print(f"Error calculating SIL for array {array_idx}, MU {mu_idx}: {e}")
                self.MUedition["edition"]["silval"][(array_idx, mu_idx)] = 0
                self.MUedition["edition"]["silvalcon"][(array_idx, mu_idx)] = np.zeros((1, 2))
        else:
            self.MUedition["edition"]["silval"][(array_idx, mu_idx)] = 0
            self.MUedition["edition"]["silvalcon"][(array_idx, mu_idx)] = np.zeros((1, 2))

        # Update the checkbox text if it exists
        for checkbox in self.mu_checkboxes:
            if checkbox.objectName() == f"Array_{array_idx+1}_MU_{mu_idx+1}":
                sil_value = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)
                checkbox.setText(f"MU_{mu_idx+1} (SIL: {sil_value:.4f})")
                break

    def display_selected_mus(self, checked_mus):
        """Display the currently selected motor units."""
        if not self.MUedition:
            return

        # Clear existing plots in the container
        for i in reversed(range(self.plots_layout.count())):
            item = self.plots_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)

        # If only one MU is selected, show pulse train and discharge rate
        if len(checked_mus) == 1:
            # Single MU display logic - similar to original display_current_mu
            mu_text = checked_mus[0]
            parts = mu_text.split("_")

            if len(parts) < 4:
                return

            array_idx = int(parts[1]) - 1
            mu_idx = int(parts[3]) - 1

            # Get the correct pulse train for this MU
            pulse_train_array = self.MUedition["edition"]["Pulsetrain"][array_idx]
            pulse_train = pulse_train_array[mu_idx, :]  # Use 2D indexing to get the full row

            # Store the current MU in backup for undo functionality
            self.Backup["Pulsetrain"] = pulse_train.copy()
            self.Backup["Dischargetimes"] = (
                self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
            )

            # Update SIL info
            sil_value = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)
            self.sil_info.setText(f"Array_{array_idx+1}_MU_{mu_idx+1} - SIL = {sil_value:.4f}")

            # Show SIL plot if checkbox is checked
            if self.sil_checkbox.isChecked():
                self.sil_plot.setVisible(True)
                self.plots_layout.addWidget(self.sil_plot)

                # Clear and update SIL plot
                self.sil_plot.clear()
                sil_data = self.MUedition["edition"]["silvalcon"].get((array_idx, mu_idx), np.array([]))

                if hasattr(sil_data, "shape") and sil_data.shape[0] > 0 and sil_data.shape[1] > 1:
                    # Extract time and SIL values
                    time_indices = sil_data[:, 0].astype(int)
                    # Make sure indices are valid
                    valid_indices = np.where(
                        (time_indices >= 0) & (time_indices < len(self.MUedition["edition"]["time"]))
                    )[0]
                    if len(valid_indices) > 0:
                        time_indices = time_indices[valid_indices]
                        sil_values = sil_data[valid_indices, 1]

                        # Create bar chart
                        x_values = self.MUedition["edition"]["time"][time_indices]

                        for i in range(len(x_values)):
                            bar_width = 0.5  # seconds
                            bar = pg.BarGraphItem(
                                x=[x_values[i]], height=[sil_values[i]], width=bar_width, brush="#262626", pen="#333333"
                            )
                            self.sil_plot.addItem(bar)

                        # Add a line at SIL=0.9
                        threshold_line = pg.InfiniteLine(pos=0.9, angle=0, pen=pg.mkPen(color="#76AC30", width=2))
                        self.sil_plot.addItem(threshold_line)

                        # Set axis ranges
                        self.sil_plot.setYRange(0.5, 1.0)
            else:
                self.sil_plot.setVisible(False)

            # Show and update spike train plot
            self.plots_layout.addWidget(self.spiketrain_plot)
            self.spiketrain_plot.clear()
            time_vector = self.MUedition["edition"]["time"]

            if isinstance(time_vector, np.ndarray) and isinstance(pulse_train, np.ndarray):
                self.spiketrain_plot.plot(
                    time_vector,
                    pulse_train,
                    pen=pg.mkPen(color="#333333", width=1),
                )

                # Plot reference signal if available
                if "target" in self.MUedition["signal"] and self.MUedition["signal"]["target"].size > 0:
                    target_data = self.MUedition["signal"]["target"]
                    if target_data.ndim > 1:
                        target_data = target_data[0]

                    if isinstance(target_data, np.ndarray) and len(target_data) == len(time_vector):
                        target_max = np.max(target_data)
                        if target_max > 0:
                            target_normalized = target_data / target_max
                            self.spiketrain_plot.plot(
                                time_vector,
                                target_normalized,
                                pen=pg.mkPen(color="#4CAF50", width=1, style=Qt.PenStyle.DashLine),
                            )

            # Plot discharge times
            discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))
            if len(discharge_times) > 0:
                scatter = pg.ScatterPlotItem()

                # Find local maxima around each discharge time
                window_size = 10
                x_values = []
                y_values = []

                for dt in discharge_times:
                    if 0 <= dt < len(pulse_train):
                        start = int(max(0, dt - window_size))
                        end = int(min(len(pulse_train), dt + window_size + 1))

                        window = pulse_train[start:end]
                        if len(window) > 0:
                            local_max_idx = start + np.argmax(window)

                            x_values.append(time_vector[local_max_idx])
                            y_values.append(pulse_train[local_max_idx])

                if len(x_values) > 0:
                    scatter.addPoints(x=x_values, y=y_values, pen=None, brush=pg.mkBrush("#D95535"), size=10)
                    self.spiketrain_plot.addItem(scatter)

            # Show and update discharge rate plot
            self.plots_layout.addWidget(self.dr_plot)
            self.dr_plot.clear()

            if len(discharge_times) > 1:
                # Calculate discharge times for plotting
                distime = np.zeros(len(discharge_times) - 1)
                for i in range(len(discharge_times) - 1):
                    midpoint = (discharge_times[i + 1] - discharge_times[i]) // 2 + discharge_times[i]
                    distime[i] = midpoint / float(self.MUedition["signal"]["fsamp"][0, 0])

                # Calculate discharge rates
                dr = 1.0 / (np.diff(discharge_times) / float(self.MUedition["signal"]["fsamp"][0, 0]))

                # Plot as scatter plot
                scatter_dr = pg.ScatterPlotItem()
                scatter_dr.addPoints(x=distime, y=dr, pen=None, brush=pg.mkBrush("#D95535"), size=10)
                self.dr_plot.addItem(scatter_dr)

                # Set y-axis range with margin
                if len(dr) > 0:
                    dr_max = np.max(dr)
                    self.dr_plot.setYRange(0, dr_max * 1.5)

        else:
            # Multiple MUs selected - show only pulse trains stacked vertically
            self.sil_info.setText(f"{len(checked_mus)} MUs selected")

            # Create a new plot widget for each selected MU
            for mu_text in checked_mus:
                parts = mu_text.split("_")
                if len(parts) < 4:
                    continue

                array_idx = int(parts[1]) - 1
                mu_idx = int(parts[3]) - 1

                # Get pulse train data
                pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]
                time_vector = self.MUedition["edition"]["time"]

                # Create a new plot for this MU
                plot_widget = self.create_plot_widget(f"Array_{array_idx+1}_MU_{mu_idx+1}")
                plot_widget.setFixedHeight(200)  # Fixed height for each plot

                # Plot pulse train with consistent style
                plot_widget.plot(
                    time_vector,
                    pulse_train,
                    pen=pg.mkPen(color="#333333", width=1),
                )

                # Plot discharge times
                discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))
                if len(discharge_times) > 0:
                    scatter = pg.ScatterPlotItem()

                    # Find local maxima around each discharge time
                    window_size = 10
                    x_values = []
                    y_values = []

                    for dt in discharge_times:
                        if 0 <= dt < len(pulse_train):
                            start = int(max(0, dt - window_size))
                            end = int(min(len(pulse_train), dt + window_size + 1))

                            window = pulse_train[start:end]
                            if len(window) > 0:
                                local_max_idx = start + np.argmax(window)

                                x_values.append(time_vector[local_max_idx])
                                y_values.append(pulse_train[local_max_idx])

                    if len(x_values) > 0:
                        scatter.addPoints(x=x_values, y=y_values, pen=None, brush=pg.mkBrush("#D95535"), size=8)
                        plot_widget.addItem(scatter)

                # Add the plot to the layout
                self.plots_layout.addWidget(plot_widget)

        # Update plot limits
        self.update_plot_limits()

    # Helper function for creating plot widgets in multi-MU view
    def create_plot_widget(self, y_label, x_label="Time (s)"):
        """Create a standardized plot widget with consistent styling for multi-MU view."""
        plot = pg.PlotWidget()
        plot.setBackground("w")  # White background

        # Set axis labels
        if y_label:
            plot.setLabel("left", y_label)
        if x_label:
            plot.setLabel("bottom", x_label)

        # Style the axes with dark color for visibility
        axis_color = "#333333"
        plot.getAxis("left").setPen(pg.mkPen(color=axis_color))
        plot.getAxis("bottom").setPen(pg.mkPen(color=axis_color))
        plot.getAxis("left").setTextPen(pg.mkPen(color=axis_color))
        plot.getAxis("bottom").setTextPen(pg.mkPen(color=axis_color))

        # Add grid
        plot.showGrid(x=True, y=True, alpha=0.3)

        # Set y-axis range for proper visualization of pulse trains
        plot.setYRange(-0.05, 1.5)

        return plot

    def array_checkbox_state_changed(self, state):
        """Handle changes in the "Check All" checkbox for an array."""
        # Get the sender checkbox
        sender = self.sender()
        if not sender:
            return

        # Get the array index from the sender's property
        array_idx = sender.property("array_idx")
        if array_idx is None:
            return

        # Block signals temporarily to prevent recursive signal handling
        for checkbox in self.mu_checkboxes:
            checkbox.blockSignals(True)

        # Set all MU checkboxes in this array to the same state
        for checkbox in self.mu_checkboxes:
            if checkbox.property("array_idx") == array_idx:
                checkbox.setChecked(state == Qt.CheckState.Checked)

        # Unblock signals
        for checkbox in self.mu_checkboxes:
            checkbox.blockSignals(False)

        # Update the display based on selection
        self.display_selected_mus([cb.objectName() for cb in self.mu_checkboxes if cb.isChecked()])

    def reference_dropdown_value_changed(self):
        """Handle change in reference signal."""
        if not self.MUedition:
            return

        idx = self.reference_dropdown.currentIndex()

        if (
            idx < 0
            or "auxiliary" not in self.MUedition["signal"]
            or self.MUedition["signal"]["auxiliary"].shape[0] <= idx
        ):
            return

        try:
            # Get the auxiliary data for the selected index
            auxiliary_data = self.MUedition["signal"]["auxiliary"][idx]

            # Make sure it's a 1D array
            if auxiliary_data.ndim > 1:
                auxiliary_data = auxiliary_data.flatten()

            # Set the selected reference as the target
            self.MUedition["signal"]["target"] = auxiliary_data

            # Update the current view based on checkboxes
            self.mu_checkbox_state_changed()
        except Exception as e:
            print(f"Error setting reference: {e}")

    def sil_checkbox_value_changed(self):
        """Toggle SIL plot visibility."""
        # Update the plots (visibility of SIL plot will be handled in display_selected_mus)
        self.mu_checkbox_state_changed()

    # Navigation actions
    def zoom_in_button_pushed(self):
        """Zoom in on the time axis."""
        if not self.MUedition or not self.graphend:
            return

        duration = self.graphend - self.graphstart
        center = self.graphstart + duration / 2
        duration = duration * 0.8
        self.graphstart = center - duration / 2
        self.graphend = center + duration / 2
        self.update_plot_limits()

    def zoom_out_button_pushed(self):
        """Zoom out on the time axis."""
        if not self.MUedition or not self.graphend:
            return

        duration = self.graphend - self.graphstart
        center = self.graphstart + duration / 2
        duration = duration * 1.5

        if duration > (self.MUedition["edition"]["time"][-1] - self.MUedition["edition"]["time"][0]):
            self.graphstart = self.MUedition["edition"]["time"][0]
            self.graphend = self.MUedition["edition"]["time"][-1]
        else:
            self.graphstart = center - duration / 2
            self.graphend = center + duration / 2

        self.update_plot_limits()

    def scroll_left_button_pushed(self):
        """Scroll left on the time axis."""
        if not self.MUedition or not self.graphend:
            return

        duration = self.graphend - self.graphstart
        step = 0.05 * duration

        if (self.graphstart - step) < self.MUedition["edition"]["time"][0]:
            self.graphstart = self.MUedition["edition"]["time"][0]
            self.graphend = self.graphstart + duration
        else:
            self.graphstart = self.graphstart - step
            self.graphend = self.graphstart + duration

        self.update_plot_limits()

    def scroll_right_button_pushed(self):
        """Scroll right on the time axis."""
        if not self.MUedition or not self.graphend:
            return

        duration = self.graphend - self.graphstart
        step = 0.05 * duration

        if (self.graphend + step) > self.MUedition["edition"]["time"][-1]:
            self.graphend = self.MUedition["edition"]["time"][-1]
            self.graphstart = self.graphend - duration
        else:
            self.graphend = self.graphend + step
            self.graphstart = self.graphend - duration

        self.update_plot_limits()

    def update_plot_limits(self):
        """Update the limits of all plots to match the current view."""
        if self.graphstart is None or self.graphend is None:
            return

        # For single MU view (standard plots)
        self.spiketrain_plot.setXRange(self.graphstart, self.graphend)
        self.dr_plot.setXRange(self.graphstart, self.graphend)
        self.spiketrain_plot.setYRange(-0.05, 1.5)

        if self.sil_checkbox.isChecked():
            self.sil_plot.setXRange(self.graphstart, self.graphend)

        # For multiple MU view (plots in scroll area)
        for i in range(self.plots_layout.count()):
            item = self.plots_layout.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, pg.PlotWidget):
                    widget.setXRange(self.graphstart, self.graphend)
                    if widget != self.sil_plot and widget != self.dr_plot:
                        widget.setYRange(-0.05, 1.5)

    # Editing actions
    def disable_action_buttons(self):
        """Temporarily disable action buttons during selection."""
        self.add_spikes_btn.setEnabled(False)
        self.delete_spikes_btn.setEnabled(False)
        self.delete_dr_btn.setEnabled(False)
        self.update_mu_filter_btn.setEnabled(False)
        self.extend_mu_filter_btn.setEnabled(False)

    def enable_action_buttons(self):
        """Re-enable action buttons after selection is complete."""
        self.add_spikes_btn.setEnabled(True)
        self.delete_spikes_btn.setEnabled(True)
        self.delete_dr_btn.setEnabled(True)
        self.update_mu_filter_btn.setEnabled(True)
        self.extend_mu_filter_btn.setEnabled(True)

    def add_spikes_button_pushed(self):
        """Add spikes by drawing a selection rectangle."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            return

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store current state for undo
        self.Backup["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :].copy()
        self.Backup["Dischargetimes"] = (
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
        )

        # Create selection tool
        self.selection_tool = SelectionTool(
            self.spiketrain_plot,
            "add_spikes",
            lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
                "add_spikes", array_idx, mu_idx, x_min, x_max, y_min, y_max
            ),
        )

    def delete_spikes_button_pushed(self):
        """Delete spikes by drawing a selection rectangle."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            return

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store current state for undo
        self.Backup["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :].copy()
        self.Backup["Dischargetimes"] = (
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
        )

        # Create selection tool
        self.selection_tool = SelectionTool(
            self.spiketrain_plot,
            "delete_spikes",
            lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
                "delete_spikes", array_idx, mu_idx, x_min, x_max, y_min, y_max
            ),
        )

    def delete_dr_button_pushed(self):
        """Delete discharge rates by drawing a selection rectangle in the DR plot."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            return

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store current state for undo
        self.Backup["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :].copy()
        self.Backup["Dischargetimes"] = (
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
        )

        # Create selection tool
        self.selection_tool = SelectionTool(
            self.dr_plot,
            "delete_dr",
            lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
                "delete_dr", array_idx, mu_idx, x_min, x_max, y_min, y_max
            ),
        )

    def handle_selection_complete(self, action_type, array_idx, mu_idx, x_min, x_max, y_min, y_max):
        """Handle the completion of a selection and process it."""
        # Process the selection
        process_selection(self.MUedition, action_type, array_idx, mu_idx, x_min, x_max, y_min, y_max)

        # Update the display
        for checkbox in self.mu_checkboxes:
            if checkbox.objectName() == f"Array_{array_idx+1}_MU_{mu_idx+1}":
                if checkbox.isChecked():
                    # If the MU is currently checked, update the display
                    self.mu_checkbox_state_changed()
                break

    def lock_spikes_button_pushed(self):
        """Lock the current spikes to keep them during filter updates."""
        self.Backup["lock"] = 1
        self.lock_spikes_btn.setStyleSheet(
            "color: #f0f0f0; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
        )

    def remove_outliers_button_pushed(self):
        """Remove outliers from the current motor unit."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            return

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store current state for undo
        self.Backup["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :].copy()
        self.Backup["Dischargetimes"] = (
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
        )

        # Get discharge times
        if (array_idx, mu_idx) not in self.MUedition["edition"]["Dischargetimes"] or len(
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]
        ) <= 1:
            return

        # Create dummy PulseT and Distime arrays for remoutliers function
        pulse_trains = np.zeros((1, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[1]))
        pulse_trains[0, :] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]

        distime_list = [self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]]

        # Apply remoutliers
        filtered_distime = remove_outliers(
            pulse_trains, distime_list, 0.3, self.MUedition["signal"]["fsamp"]  # Threshold for CoV of Discharge rate
        )

        # Update discharge times
        if filtered_distime and len(filtered_distime) > 0:
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = filtered_distime[0]

            # Update the display
            self.mu_checkbox_state_changed()

    def update_mu_filter_button_pushed(self):
        """Update the motor unit filter using the current discharge times."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            return

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store current state for undo
        self.Backup["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :].copy()
        self.Backup["Dischargetimes"] = (
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
        )

        # Get the indices for the current view
        idx = np.where(
            (self.MUedition["edition"]["time"] > self.graphstart) & (self.MUedition["edition"]["time"] < self.graphend)
        )[0]

        if len(idx) == 0:
            return

        # Get EMG data for the current array and view
        emg_data = self.MUedition["signal"]["data"][self.MUedition["edition"]["arraynb"] == array_idx, :]
        emg_mask = self.MUedition["signal"]["EMGmask"][array_idx]
        emg_data = emg_data[emg_mask == 0, :]  # Use only non-rejected channels

        # Get the MUAP templates using extendfilter
        old_sil = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)

        # Apply filter update
        updated_pulse_train, updated_discharge_times = extendfilter(
            emg_data,
            emg_mask,
            self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :],
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx],
            idx,
            self.MUedition["signal"]["fsamp"],
            self.MUedition["signal"]["emgtype"][array_idx],
        )

        # Handle spike locking
        if self.Backup["lock"] == 1:
            self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = updated_pulse_train

            # Reset the lock
            self.Backup["lock"] = 0
            self.lock_spikes_btn.setStyleSheet(
                "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 18pt;"
            )
        else:
            # Update both pulse train and discharge times
            self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = updated_pulse_train
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = updated_discharge_times

        # Recalculate SIL values
        self.calculate_silval(array_idx, mu_idx)

        # Update the display
        self.mu_checkbox_state_changed()

    def extend_mu_filter_button_pushed(self):
        """Extend the motor unit filter to the entire signal."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            return

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store current state for undo
        self.Backup["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :].copy()
        self.Backup["Dischargetimes"] = (
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
        )

        # Get EMG data for the current array
        emg_data = self.MUedition["signal"]["data"][self.MUedition["edition"]["arraynb"] == array_idx, :]
        emg_mask = self.MUedition["signal"]["EMGmask"][array_idx]
        emg_data = emg_data[emg_mask == 0, :]  # Use only non-rejected channels

        # Get the current view indices
        current_idx = np.where(
            (self.MUedition["edition"]["time"] > self.graphstart) & (self.MUedition["edition"]["time"] < self.graphend)
        )[0]

        if len(current_idx) == 0:
            return

        # Save old SIL for later comparison
        old_sil = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)

        # Zoom out to full signal
        self.graphstart = self.MUedition["edition"]["time"][0]
        self.graphend = self.MUedition["edition"]["time"][-1]
        self.update_plot_limits()

        # Process the signal in windows to extend the filter
        signal_length = self.MUedition["edition"]["time"].shape[0]
        step = current_idx.shape[0] // 2

        # First extend forward
        idx = current_idx.copy()
        for j in range(int((signal_length - idx[-1]) / step)):
            # Move idx forward
            idx = idx + step
            idx = idx[idx < signal_length]

            if len(idx) == 0:
                break

            # Apply extendfilter
            updated_pulse_train, updated_discharge_times = extendfilter(
                emg_data,
                emg_mask,
                self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :],
                self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx],
                idx,
                self.MUedition["signal"]["fsamp"],
                self.MUedition["signal"]["emgtype"][array_idx],
            )

            # Update the data
            self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = updated_pulse_train
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = updated_discharge_times

            # Update the display to show progress
            self.mu_checkbox_state_changed()
            QApplication.processEvents()

        # Then extend backward
        idx = current_idx.copy()
        for j in range(int(idx[0] / step)):
            # Move idx backward
            idx = idx - step
            idx = idx[idx >= 0]

            if len(idx) == 0:
                break

            # Apply extendfilter
            updated_pulse_train, updated_discharge_times = extendfilter(
                emg_data,
                emg_mask,
                self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :],
                self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx],
                idx,
                self.MUedition["signal"]["fsamp"],
                self.MUedition["signal"]["emgtype"][array_idx],
            )

            # Update the data
            self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = updated_pulse_train
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = updated_discharge_times

            # Update the display to show progress
            self.mu_checkbox_state_changed()
            QApplication.processEvents()

        # Recalculate SIL values
        self.calculate_silval(array_idx, mu_idx)

        # Final display update
        self.mu_checkbox_state_changed()

    def undo_button_pushed(self):
        """Undo the last edit."""
        if not self.MUedition or self.Backup["Pulsetrain"] is None:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            return

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Restore from backup
        self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = self.Backup["Pulsetrain"].copy()
        self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = self.Backup["Dischargetimes"].copy()

        # Recalculate SIL
        self.calculate_silval(array_idx, mu_idx)

        # Update the display
        self.mu_checkbox_state_changed()

    def flag_mu_for_deletion_button_pushed(self):
        """Flag the selected motor units for deletion."""
        if not self.MUedition:
            return

        # Find all checked MUs
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                mu_text = checkbox.objectName()
                parts = mu_text.split("_")

                if len(parts) < 4:
                    continue

                array_idx = int(parts[1]) - 1
                mu_idx = int(parts[3]) - 1

                # Store current state for undo (only for the last MU - limitation)
                self.Backup["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :].copy()
                self.Backup["Dischargetimes"] = (
                    self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([])).copy()
                )

                # Extract the sampling frequency as a scalar
                if self.MUedition["signal"]["fsamp"].ndim > 1:
                    fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])
                else:
                    fsamp = float(self.MUedition["signal"]["fsamp"][0])

                # Set pulse train to zeros and minimal discharge times
                self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = 0
                self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = np.array([1, fsamp])

                # Update SIL in checkbox text
                sil_value = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)
                checkbox.setText(f"{mu_text} (SIL: {sil_value:.4f}) - FLAGGED")

        # Update the display
        self.mu_checkbox_state_changed()

    # Batch processing
    def remove_all_outliers_button_pushed(self):
        """Remove outliers from all motor units."""
        if not self.MUedition:
            return

        # Create a progress dialog
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import QTimer

        progress = QProgressDialog("Removing outliers...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # Count total MUs
        total_mus = 0
        for i in range(len(self.MUedition["edition"]["Pulsetrain"])):
            total_mus += self.MUedition["edition"]["Pulsetrain"][i].shape[0]

        # Process each MU
        processed_mus = 0
        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            num_mus = self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]

            for mu_idx in range(num_mus):
                progress.setValue(int(processed_mus / total_mus * 100))
                progress.setLabelText(f"Removing outliers for Array #{array_idx+1} MU #{mu_idx+1}")
                QApplication.processEvents()

                if progress.wasCanceled():
                    break

                # Create dummy arrays for remoutliers function
                pulse_trains = np.zeros((1, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[1]))
                pulse_trains[0, :] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]

                distime_list = [self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))]

                # Apply remoutliers if there are discharge times
                if len(distime_list[0]) > 1:
                    filtered_distime = remove_outliers(
                        pulse_trains,
                        distime_list,
                        0.3,  # Threshold for CoV of Discharge rate
                        self.MUedition["signal"]["fsamp"],
                    )

                    # Update discharge times
                    if filtered_distime and len(filtered_distime) > 0:
                        self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = filtered_distime[0]

                    # Update SIL values
                    self.calculate_silval(array_idx, mu_idx)

                processed_mus += 1

            if progress.wasCanceled():
                break

        progress.setValue(100)

        # Update the current MU display
        self.mu_checkbox_state_changed()

    def update_all_mu_filters_button_pushed(self):
        """Update filters for all motor units."""
        if not self.MUedition:
            return

        # Create a progress dialog
        from PyQt5.QtWidgets import QProgressDialog

        progress = QProgressDialog("Updating MU filters...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # Count total MUs
        total_mus = 0
        for i in range(len(self.MUedition["edition"]["Pulsetrain"])):
            total_mus += self.MUedition["edition"]["Pulsetrain"][i].shape[0]

        # Process each MU
        processed_mus = 0
        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            # Get EMG data for this array
            emg_data = self.MUedition["signal"]["data"][self.MUedition["edition"]["arraynb"] == array_idx, :]
            emg_mask = self.MUedition["signal"]["EMGmask"][array_idx]
            emg_data = emg_data[emg_mask == 0, :]  # Use only non-rejected channels

            num_mus = self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]

            for mu_idx in range(num_mus):
                progress.setValue(int(processed_mus / total_mus * 100))
                progress.setLabelText(f"Updating filter for Array #{array_idx+1} MU #{mu_idx+1}")
                QApplication.processEvents()

                if progress.wasCanceled():
                    break

                # Get discharge times
                discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

                if len(discharge_times) > 1:
                    # Create extension factor
                    extension_factor = min(1000 // emg_data.shape[0], 25)

                    # Extend the EMG signal
                    extended_emg = np.zeros(
                        [emg_data.shape[0] * extension_factor, emg_data.shape[1] + extension_factor - 1]
                    )
                    extended_emg = extend_emg(extended_emg, emg_data, extension_factor)

                    # Calculate covariance and pseudo-inverse
                    covariance = extended_emg @ extended_emg.T / extended_emg.shape[1]
                    inverse_cov = np.linalg.pinv(covariance)

                    # Get whitened signal
                    _, _, dewhitening_matrix = whiten_emg(extended_emg)

                    # Calculate motor unit filter
                    mu_filter = np.sum(extended_emg[:, discharge_times], axis=1, keepdims=True)

                    # Calculate pulse train
                    pulse_train = ((dewhitening_matrix @ mu_filter).T @ inverse_cov) @ extended_emg
                    pulse_train = pulse_train[0, : emg_data.shape[1]]

                    # Square and rectify
                    pulse_train = pulse_train * np.abs(pulse_train)

                    # Find peaks
                    from scipy.signal import find_peaks

                    peaks, _ = find_peaks(pulse_train, distance=round(0.005 * self.MUedition["signal"]["fsamp"]))

                    # Normalize using top peaks
                    if len(peaks) >= 10:
                        top_values = np.sort(pulse_train[peaks])[-10:]
                        pulse_train = pulse_train / np.mean(top_values)
                    elif len(peaks) > 0:
                        pulse_train = pulse_train / np.mean(pulse_train[peaks])

                    # Cluster peaks to find spikes
                    if len(peaks) >= 2:
                        from sklearn.cluster import KMeans

                        kmeans = KMeans(n_clusters=2, random_state=0).fit(pulse_train[peaks].reshape(-1, 1))
                        labels = kmeans.labels_
                        centroids = kmeans.cluster_centers_

                        # Find class with highest centroid
                        high_centroid_idx = np.argmax(centroids)
                        spikes = peaks[labels == high_centroid_idx]

                        # Remove outliers
                        threshold = np.mean(pulse_train[spikes]) + 3 * np.std(pulse_train[spikes])
                        spikes = spikes[pulse_train[spikes] <= threshold]
                    else:
                        spikes = peaks

                    # Update the pulse train and discharge times
                    self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = pulse_train
                    self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = spikes

                    # Recalculate SIL
                    self.calculate_silval(array_idx, mu_idx)

                processed_mus += 1

            if progress.wasCanceled():
                break

        progress.setValue(100)

        # Update the current MU display
        self.mu_checkbox_state_changed()

    def remove_flagged_mu_button_pushed(self):
        """Remove motor units that have been flagged for deletion."""
        if not self.MUedition:
            return

        # Create a progress dialog
        from PyQt5.QtWidgets import QProgressDialog

        progress = QProgressDialog("Removing flagged MUs...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # Count total arrays
        total_arrays = len(self.MUedition["edition"]["Pulsetrain"])

        # Create clean versions of Pulsetrain and Dischargetimes
        clean_pulsetrain = []
        clean_dischargetimes = {}
        clean_silval = {}
        clean_silvalcon = {}

        # Process each array
        for array_idx in range(total_arrays):
            progress.setValue(int(array_idx / total_arrays * 100))
            progress.setLabelText(f"Processing Array #{array_idx+1}")
            QApplication.processEvents()

            if progress.wasCanceled():
                break

            # Get the pulse trains for this array
            array_pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

            # Create a mask for non-flagged MUs
            keep_mask = np.ones(array_pulse_train.shape[0], dtype=bool)

            # Check each MU
            for mu_idx in range(array_pulse_train.shape[0]):
                # Get discharge times
                discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

                # Check if it's flagged for deletion (0 pulse train and minimal discharge times)
                if (
                    np.all(array_pulse_train[mu_idx, :] == 0)
                    and len(discharge_times) == 2
                    and discharge_times[0] == 1
                    and discharge_times[1] == self.MUedition["signal"]["fsamp"]
                ):
                    keep_mask[mu_idx] = False

            # Keep only non-flagged MUs
            if np.any(keep_mask):
                clean_pulsetrain.append(array_pulse_train[keep_mask])

                # Keep corresponding discharge times and SIL values
                for mu_idx, new_idx in enumerate(np.where(keep_mask)[0]):
                    if (array_idx, new_idx) in self.MUedition["edition"]["Dischargetimes"]:
                        clean_dischargetimes[array_idx, mu_idx] = self.MUedition["edition"]["Dischargetimes"][
                            array_idx, new_idx
                        ]

                    if (array_idx, new_idx) in self.MUedition["edition"]["silval"]:
                        clean_silval[array_idx, mu_idx] = self.MUedition["edition"]["silval"][array_idx, new_idx]

                    if (array_idx, new_idx) in self.MUedition["edition"]["silvalcon"]:
                        clean_silvalcon[array_idx, mu_idx] = self.MUedition["edition"]["silvalcon"][array_idx, new_idx]
            else:
                # Add empty array if all MUs are flagged
                clean_pulsetrain.append(np.zeros((0, array_pulse_train.shape[1])))

        progress.setValue(100)

        # Update the data
        self.MUedition["edition"]["Pulsetrain"] = clean_pulsetrain
        self.MUedition["edition"]["Dischargetimes"] = clean_dischargetimes
        self.MUedition["edition"]["silval"] = clean_silval
        self.MUedition["edition"]["silvalcon"] = clean_silvalcon

        # Update the MU checkboxes
        self.update_mu_checkboxes()

    def remove_duplicates_within_grids_button_pushed(self):
        """Remove duplicate motor units within each grid."""
        if not self.MUedition:
            return

        # Extract the sampling frequency as a scalar
        if self.MUedition["signal"]["fsamp"].ndim > 1:
            fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])
        else:
            fsamp = float(self.MUedition["signal"]["fsamp"][0])

        # Process each array
        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            # Skip if there are no MUs
            if self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0] == 0:
                continue

            # Create arrays for remduplicates
            pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

            discharge_times = []
            for mu_idx in range(pulse_train.shape[0]):
                if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                    discharge_times.append(self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx])
                else:
                    discharge_times.append(np.array([]))

            # Remove duplicates
            unique_discharge_times, unique_pulse_train, _ = remove_duplicates(
                pulse_train,
                discharge_times,
                discharge_times,
                np.zeros((1, 1)),  # Placeholder for mu_filters (not used)
                round(fsamp / 40),
                0.00025,
                0.3,  # Duplicate threshold
                fsamp,
            )

            # Replace with unique MUs
            self.MUedition["edition"]["Pulsetrain"][array_idx] = unique_pulse_train

            # Update discharge times and SIL values
            for mu_idx in range(unique_pulse_train.shape[0]):  # type:ignore
                self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = unique_discharge_times[mu_idx]
                self.calculate_silval(array_idx, mu_idx)

        # Update the MU checkboxes
        self.update_mu_checkboxes()

    def remove_duplicates_between_grids_button_pushed(self):
        """Remove duplicate motor units between grids."""
        if not self.MUedition:
            return

        # Extract the sampling frequency as a scalar
        if self.MUedition["signal"]["fsamp"].ndim > 1:
            fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])
        else:
            fsamp = float(self.MUedition["signal"]["fsamp"][0])

        # Count total MUs
        mu_count = 0
        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            mu_count += self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]

        # Create arrays for remduplicatesbgrids
        all_pulse_trains = np.zeros((mu_count, self.MUedition["edition"]["time"].shape[0]))
        all_discharge_times = []
        muscle = np.zeros(mu_count, dtype=int)

        # Collect all MUs
        mu_idx_global = 0
        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            for mu_idx in range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]):
                all_pulse_trains[mu_idx_global] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx]

                if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                    all_discharge_times.append(self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx])
                else:
                    all_discharge_times.append(np.array([]))

                muscle[mu_idx_global] = array_idx
                mu_idx_global += 1

        # Remove duplicates between arrays
        unique_discharge_times, unique_pulse_train, unique_muscle = remove_duplicates_between_arrays(
            all_pulse_trains, all_discharge_times, muscle, round(fsamp / 40), 0.00025, 0.3, fsamp  # Duplicate threshold
        )

        # Recreate data structures
        new_pulsetrain = []
        new_dischargetimes = {}
        new_silval = {}
        new_silvalcon = {}

        # Initialize arrays for each grid
        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            array_indices = np.where(unique_muscle == array_idx)[0]

            if len(array_indices) > 0:
                # Get pulse trains for this array
                array_pulse_train = unique_pulse_train[array_indices]
                new_pulsetrain.append(array_pulse_train)

                # Get discharge times for this array
                for mu_idx, global_idx in enumerate(array_indices):
                    if global_idx < len(unique_discharge_times):
                        new_dischargetimes[array_idx, mu_idx] = unique_discharge_times[global_idx]

                    # Calculate SIL values
                    self.calculate_silval(array_idx, mu_idx)
            else:
                # Add empty array
                new_pulsetrain.append(
                    np.zeros(
                        (
                            0,
                            (
                                unique_pulse_train.shape[1]
                                if unique_pulse_train.shape[0] > 0
                                else self.MUedition["edition"]["time"].shape[0]
                            ),
                        )
                    )
                )

        # Update the data
        self.MUedition["edition"]["Pulsetrain"] = new_pulsetrain
        self.MUedition["edition"]["Dischargetimes"] = new_dischargetimes

        # Update the MU checkboxes
        self.update_mu_checkboxes()

    # Visualization methods
    def plot_mu_spiketrains_button_pushed(self):
        """Plot all motor unit spike trains in a new window."""
        if not self.MUedition:
            return

        # Create a new window for the plot
        dialog = QDialog(self)
        dialog.setWindowTitle("Motor Unit Spike Trains")
        dialog.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout(dialog)

        # Create a figure with subplots for each array
        fig, axes = plt.subplots(1, len(self.MUedition["edition"]["Pulsetrain"]), figsize=(15, 8))
        if len(self.MUedition["edition"]["Pulsetrain"]) == 1:
            axes = [axes]

        # Set figure background color
        fig.patch.set_facecolor("#262626")

        # Plot each array
        for array_idx, ax in enumerate(axes):
            # Set axes properties
            ax.set_facecolor("#262626")
            ax.tick_params(colors="#f0f0f0")
            ax.spines["bottom"].set_color("#f0f0f0")
            ax.spines["top"].set_color("#f0f0f0")
            ax.spines["left"].set_color("#f0f0f0")
            ax.spines["right"].set_color("#f0f0f0")

            # Plot target reference
            if "target" in self.MUedition["signal"] and self.MUedition["signal"]["target"].size > 0:
                # Get target data and ensure it's a 1D array
                target_data = self.MUedition["signal"]["target"]
                if target_data.ndim > 1:
                    target_data = target_data[0]  # Get the first row if it's a 2D array

                # Normalize target to 0-1 range
                target_max = np.max(target_data)
                if target_max > 0:
                    target_normalized = target_data / target_max
                    ax.plot(
                        self.MUedition["edition"]["time"],
                        target_normalized * self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0],
                        "--",
                        linewidth=1,
                        color="#D95535",
                    )

            # Create firing times array
            firings = np.full(
                (self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0], len(self.MUedition["edition"]["time"])),
                np.nan,
            )

            # Fill with MU indices at discharge times
            for mu_idx in range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]):
                if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                    firings[mu_idx, self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]] = mu_idx + 1

            # Plot as raster plot
            for mu_idx in range(firings.shape[0]):
                time_indices = np.where(~np.isnan(firings[mu_idx]))[0]
                ax.plot(
                    self.MUedition["edition"]["time"][time_indices],
                    np.ones_like(time_indices) * (mu_idx + 1),
                    "|",
                    markersize=10,
                    color="#f0f0f0",
                )

            # Set labels
            ax.set_title(
                f'Array #{array_idx+1} with {self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]} MUs',
                color="#f0f0f0",
                fontsize=12,
            )
            ax.set_xlabel("Time (s)", color="#f0f0f0")
            if array_idx == 0:
                ax.set_ylabel("MU #", color="#f0f0f0")

            # Set y-axis limits with margin
            ax.set_ylim(0, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0] + 1)

        # Add a overall title
        fig.suptitle(
            f'Raster plots for {len(self.MUedition["edition"]["Pulsetrain"])} arrays', color="#f0f0f0", fontsize=16
        )

        # Add the figure to the dialog
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        plt.tight_layout()
        dialog.show()

    def plot_mu_firingrates_button_pushed(self):
        """Plot all motor unit firing rates in a new window."""
        if not self.MUedition:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Motor Unit Firing Rates")
        dialog.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout(dialog)

        # Create a figure with subplots for each array
        fig, axes = plt.subplots(1, len(self.MUedition["edition"]["Pulsetrain"]), figsize=(15, 8))
        if len(self.MUedition["edition"]["Pulsetrain"]) == 1:
            axes = [axes]

        # Set figure background color
        fig.patch.set_facecolor("#262626")

        # Get the currently selected MUs
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())

        # Extract the sampling frequency as a scalar
        if self.MUedition["signal"]["fsamp"].ndim > 1:
            fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])
        else:
            fsamp = float(self.MUedition["signal"]["fsamp"][0])

        # Create window for smoothing
        window_size = int(fsamp)
        hann_window = np.hanning(window_size)

        # Plot each array
        for array_idx, ax in enumerate(axes):
            # Set axes properties
            ax.set_facecolor("#262626")
            ax.tick_params(colors="#f0f0f0")
            ax.spines["bottom"].set_color("#f0f0f0")
            ax.spines["top"].set_color("#f0f0f0")
            ax.spines["left"].set_color("#f0f0f0")
            ax.spines["right"].set_color("#f0f0f0")

            # Process each MU in this array
            for mu_idx in range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]):
                # Create binary spike train
                firing = np.zeros(len(self.MUedition["edition"]["time"]))

                if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                    discharge_times = self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]
                    if len(discharge_times) > 0:
                        firing[discharge_times] = 1

                # Smooth using convolution
                smoothed_dr = np.convolve(firing, hann_window, mode="same")

                # Determine line style - highlight current MUs
                mu_text = f"Array_{array_idx+1}_MU_{mu_idx+1}"
                if mu_text in checked_mus:
                    ax.plot(self.MUedition["edition"]["time"], smoothed_dr, color="#D95535", linewidth=3)
                else:
                    ax.plot(self.MUedition["edition"]["time"], smoothed_dr, color="#f0f0f0", linewidth=1, alpha=0.7)

            # Set labels
            ax.set_title(
                f'Array #{array_idx+1} with {self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]} MUs',
                color="#f0f0f0",
                fontsize=12,
            )
            ax.set_xlabel("Time (s)", color="#f0f0f0")
            if array_idx == 0:
                ax.set_ylabel("Smoothed discharge rates", color="#f0f0f0")

        # Add a overall title
        fig.suptitle(
            f'Smoothed discharge rates for {len(self.MUedition["edition"]["Pulsetrain"])} arrays',
            color="#f0f0f0",
            fontsize=16,
        )

        # Add the figure to the dialog
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        plt.tight_layout()
        dialog.show()

    def save_button_pushed(self):
        """Save the edited motor units to a file."""
        if not self.MUedition:
            return

        # Remove flagged MUs before saving
        from PyQt5.QtWidgets import QProgressDialog

        progress = QProgressDialog("Checking flagged units...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # Count total arrays
        total_arrays = len(self.MUedition["edition"]["Pulsetrain"])

        # Clean the data structures
        for array_idx in range(total_arrays):
            progress.setValue(int(array_idx / total_arrays * 100))
            progress.setLabelText(f"Checking flagged units for Array #{array_idx+1}")
            QApplication.processEvents()

            if progress.wasCanceled():
                break

            # Get the pulse trains for this array
            array_pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

            # Check each MU from the end to avoid indexing issues when removing
            for mu_idx in range(array_pulse_train.shape[0] - 1, -1, -1):
                # Get discharge times
                discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

                # Check if it's flagged for deletion (0 pulse train and minimal discharge times)
                if (
                    np.all(array_pulse_train[mu_idx, :] == 0)
                    and len(discharge_times) == 2
                    and discharge_times[0] == 1
                    and discharge_times[1] == self.MUedition["signal"]["fsamp"]
                ):

                    # Remove this MU
                    self.MUedition["edition"]["Pulsetrain"][array_idx] = np.delete(
                        self.MUedition["edition"]["Pulsetrain"][array_idx], mu_idx, axis=0
                    )

                    # Remove from discharge times and SIL values
                    if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                        del self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]

                    if (array_idx, mu_idx) in self.MUedition["edition"]["silval"]:
                        del self.MUedition["edition"]["silval"][array_idx, mu_idx]

                    if (array_idx, mu_idx) in self.MUedition["edition"]["silvalcon"]:
                        del self.MUedition["edition"]["silvalcon"][array_idx, mu_idx]

                    # Shift higher motor units down
                    for shift_mu in range(mu_idx + 1, array_pulse_train.shape[0]):
                        if (array_idx, shift_mu) in self.MUedition["edition"]["Dischargetimes"]:
                            self.MUedition["edition"]["Dischargetimes"][array_idx, shift_mu - 1] = self.MUedition[
                                "edition"
                            ]["Dischargetimes"][array_idx, shift_mu]
                            del self.MUedition["edition"]["Dischargetimes"][array_idx, shift_mu]

                        if (array_idx, shift_mu) in self.MUedition["edition"]["silval"]:
                            self.MUedition["edition"]["silval"][array_idx, shift_mu - 1] = self.MUedition["edition"][
                                "silval"
                            ][array_idx, shift_mu]
                            del self.MUedition["edition"]["silval"][array_idx, shift_mu]

                        if (array_idx, shift_mu) in self.MUedition["edition"]["silvalcon"]:
                            self.MUedition["edition"]["silvalcon"][array_idx, shift_mu - 1] = self.MUedition["edition"][
                                "silvalcon"
                            ][array_idx, shift_mu]
                            del self.MUedition["edition"]["silvalcon"][array_idx, shift_mu]

        progress.setValue(100)

        # Determine the save filename
        if self.filename is None:
            return

        if "edited" in self.filename:
            savename = os.path.join(self.pathname or "", self.filename)
        else:
            savename = os.path.join(self.pathname or "", os.path.splitext(self.filename)[0] + "_edited.mat")

        # Prepare data for saving
        signal = self.MUedition["signal"]
        parameters = self.MUedition.get("parameters", {})
        edition = self.MUedition["edition"]

        # Save the data
        sio.savemat(savename, {"signal": signal, "parameters": parameters, "edition": edition})

        # Show a confirmation message
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.information(self, "Save Complete", f"Data saved to {savename}", QMessageBox.Ok)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MUeditManual()
    window.show()
    sys.exit(app.exec_())
