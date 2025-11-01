from PyQt5.QtWidgets import (
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QWidget,
    QFrame,
)
import numpy as np
from PyQt5.QtCore import Qt

from core.utils.manual_editing.getsil import getsil
from core.utils.manual_editing.refinesil import refinesil
from app.muEditFunctions.plotting import (
    update_spike_train_plot,
    update_dr_plot
)
import pyqtgraph as pg


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
    self.clear_layout(self.mu_checkbox_layout)

    # for i in reversed(range(self.mu_checkbox_layout.count())):
    #     item = self.mu_checkbox_layout.itemAt(i)
    #     if item and item.widget():
    #         item.widget().deleteLater()

    # Add checkboxes for each MU
    if not self.MUedition or len(self.MUedition["edition"]["Pulsetrain"]) == 0:
        no_mu_label = QLabel("No MUs loaded")
        no_mu_label.setStyleSheet("color: #333333; font-family: 'Poppins'; font-size: 10pt;")
        self.mu_checkbox_layout.addWidget(no_mu_label)
        # Add stretch to keep items at the top
        self.mu_checkbox_layout.addStretch(1)
        return

    from ui.components import CollapsiblePanel

    for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
        # Ignore Empty Pulsetrain
        if self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0] == 0:
            continue

        # Create collapsible panel for this array
        array_panel = CollapsiblePanel(f"Array #{array_idx+1}")
        self.mu_panels.append(array_panel)

        # Create container widget for checkboxes in this array
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(5, 2, 5, 2)
        checkbox_layout.setSpacing(5)

        # Add "Check All" checkbox at the top
        check_all_checkbox = QCheckBox("Check All")
        check_all_checkbox.setStyleSheet(
            "color: #333333; font-family: 'Segoe UI'; font-size: 13pt; font-weight: normal;"
        )
        check_all_checkbox.setProperty("array_idx", array_idx)
        check_all_checkbox.stateChanged.connect(
            lambda state: array_checkbox_state_changed(self, state)
        )
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
            checkbox.setStyleSheet("color: #333333; font-family: 'Segoe UI'; font-size: 12pt;")
            checkbox.setObjectName(mu_identifier)  # Keep the full identifier in objectName
            checkbox.setProperty("array_idx", array_idx)  # Store array index for check all functionality
            checkbox.stateChanged.connect(
                lambda state: mu_checkbox_state_changed(self, state)
            )
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

def mu_checkbox_state_changed(self, _state=None, *, pluse_train_color="#D95535", update_act_btn=True):
    """Handle changes in MU checkbox selection."""
    # Get all checked MUs
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())

    # Update "Check All" checkboxes based on individual selections
    update_array_checkboxes(self)
    if self.resetPlot:
        self.zoom_slider.set_slider_value(0)

    # If none are checked, don't update display
    if not checked_mus:
        return
    if len(checked_mus) > 1:
        self.plot_display_mode = 1
    else:
        self.plot_display_mode = 0

    # Update the display based on selection
    display_selected_mus(self, checked_mus, pluse_train_color)
    if update_act_btn:
        self.update_action_button_states()

def update_display_mus(self, pluse_train_color="#D95535"):
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())

    display_selected_mus(self, checked_mus, pluse_train_color)

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
                if state == Qt.CheckState.Checked:
                    self.plot_display_mode = 1
                    self.update_action_button_states()
                else:
                    self.plot_display_mode = 0
                    self.update_action_button_states()

        # Unblock signals
        for checkbox in self.mu_checkboxes:
            checkbox.blockSignals(False)

        mu_checkbox_state_changed(self)

        # Update the display based on selection
        # self.display_selected_mus([cb.objectName() for cb in self.mu_checkboxes if cb.isChecked()])

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

def display_selected_mus(self, checked_mus, pluse_train_color="#D95535"):
    """Display the currently selected motor units."""
    if not self.MUedition:
        return
    print("display_selected_mus ")

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
            self.plots_layout.addWidget(self.sil_plot, stretch=1)

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
        self.plots_layout.addWidget(self.spiketrain_plot, stretch=2)
        update_spike_train_plot(self, array_idx, mu_idx, pulse_train, pluse_train_color)

        discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

        # Show and update discharge rate plot
        self.plots_layout.addWidget(self.dr_plot, stretch=2)
        update_dr_plot(self, discharge_times)

        def on_xrange_changed(_, ranges):
            if self.update_plot_setRange:
                return
            self.graphstart, self.graphend = ranges

        self.dr_plot.setXLink(self.spiketrain_plot)

        # self.dr_plot.getViewBox().sigXRangeChanged.connect(on_xrange_changed, type=Qt.UniqueConnection) 
        self.spiketrain_plot.getViewBox().sigXRangeChanged.connect(on_xrange_changed, type=Qt.UniqueConnection)

        self.resetPlot = False

    else:
        # Multiple MUs selected - show only pulse trains stacked vertically
        self.sil_info.setText(f"{len(checked_mus)} MUs selected")

        if len(checked_mus) == 0:
            return

        container_height = self.plots_scroll_area.viewport().height()
        plot_height = container_height // min(3, len(checked_mus))
        plot_height = min(500, plot_height)

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
            plot_widget.setFixedHeight(plot_height)  # Fixed height for each plot

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
    self._sync_pan_slider()#moy
