import os
import sys
import copy # moy
import numpy as np
import scipy.io as sio
import pyqtgraph as pg
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox
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
    QLayout,
    QStackedWidget,
    QProgressDialog, # moy
    QShortcut,
)
from PyQt5.QtGui import QKeySequence

import h5py

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from ui.MUeditManualUI import setup_ui
from core.utils.manual_editing.getsil import getsil
from core.utils.manual_editing.refinesil import refinesil
from core.utils.manual_editing.h5_import import h5py_convert
from core.utils.manual_editing.save_worker import Save_worker
from core.utils.manual_editing.extendfilter import extendfilter
from core.utils.manual_editing.selection_tools import SelectionTool, process_selection

from core.utils.decomposition.remove_duplicates import remove_duplicates
from core.utils.decomposition.remove_duplicates_between_arrays import remove_duplicates_between_arrays
from core.utils.decomposition.extend_emg import extend_emg
from core.utils.decomposition.whiten_emg import whiten_emg

from core.utils.manual_editing.smart_button_pushed import smart_button_pushed
from core.utils.manual_editing.batch_filter_worker import batch_filter_worker
from core.utils.manual_editing.duplicates_within_grids_worker import duplicates_within_grids_worker
from core.utils.manual_editing.duplicates_between_grids_worker import duplicates_between_grids_worker

from app.muEditFunctions.importer import import_data
from app.muEditFunctions.plotting import *
# Import custom components
from ui.components import (
    WarningDialog,
    SuccessDialog,
    ErrorDialog,
    MessageDialog,
    HelpDialog,
    PlotDialog,
    CleanTheme
)
import json

class MUeditManual(QMainWindow):
    """
    Manual Motor Unit Editor for EMG Data
    Allows for viewing and editing motor unit discharge patterns.
    """

    # Add signal to return to dashboard if needed
    return_to_dashboard_requested = pyqtSignal()

    def __init__(self, filename=None, pathname=None, parent=None):
        super().__init__(parent)

        # Initialize main data structures
        self.filename = filename
        self.pathname = pathname
        self.MUedition = None
        self.Backup = {"lock": 0, "Pulsetrain": None, "Dischargetimes": None, "lock_changable": 1}
        self.undo_stack = [] # add undo stack moy
        self.redo_stack = []
        self.graphstart = None
        self.graphend = None
        self.array_checkboxes = []# moy
        self.roi = None
        self.resetPlot = False
        self.current_selection = None
        self.mu_checkboxes = []  # Initialize the mu_checkboxes list
        self.plot_display_mode = 0  # 0 for Single MU Seleted
        self.update_plot_setRange = False
        self.aa_fix = False
        self.RasterPlotDialog = None
        self.DischagePlotDialog = None
        self.spike_train_plot_sort_mode = True
        self._save_flag = True
        self._on_save = 0
        self._ish5 = False

        # Set up the UI
        setup_ui(self)

        self.dirty = False
        self.update_save_button()
        self.dirty_depth = 0
        # Imports data (only if filename and pathname exist)
        if filename and pathname:
            self.file_path_field.setText(self.filename)
            import_data(self)

        # Add back button if needed when used in embedded mode
        if parent:
            self.add_back_button()

        self._create_shortcuts()

    def show_tip(self, text, duration_ms=3000):
        self.tip_bar.setText(text)
        self.tip_timer.start(duration_ms)

    def clear_tip(self):
        self.tip_bar.setText("")

    def center_pan_slider(self): # moy
        if not hasattr(self, "pan_slider"):
            return
        mid = (self.pan_slider.minimum() + self.pan_slider.maximum()) // 2
        self.pan_slider.setSliderPosition(mid)

    def check_current_data_save_by_dirty(self):
        if self.MUedition is None:
            return False
        """Compare Current Data With initial Data"""
        current_data = self.MUedition["edition"]
        #Same == False，Different == True
        answer = self.compare_current_initial_data(current_data, self.initial_data)
        return answer

    def compare_current_initial_data(self, current_data, initial_data):

        fields = ["Pulsetrain", "Dischargetimes", "silval", "silvalcon", "time", "arraynb"]
        for field in fields:
            val1 = current_data.get(field)
            val2 = initial_data.get(field)
            # Compare list of numpy arrays
            if isinstance(val1, list) and all(isinstance(x, np.ndarray) for x in val1):
                if len(val1) != len(val2):
                    return True
                for arr1, arr2 in zip(val1, val2):
                    if not np.array_equal(arr1, arr2, equal_nan=True):
                        return True
            # Compare dict
            elif isinstance(val1, dict):
                if val1.keys() != val2.keys():
                    return True
                for k in val1:
                    if not np.array_equal(val1[k], val2[k], equal_nan=True):
                        return True
            # Compare numpy array
            elif isinstance(val1, np.ndarray):
                if not np.array_equal(val1, val2, equal_nan=True):
                    return True
            # Compare others
            else:
                if val1 != val2:
                    return True
        return False

    def update_save_button(self, on_save=0):
        if on_save == 1:
            self._on_save = on_save
            self.floating_save_btn.setEnabled(False)
            self.floating_save_btn.setText("")
            self.floating_save_btn.setIcon("hourglass_half", (36, 36))
            self.floating_save_btn.setStyleSheet("""
                QPushButton{background:#fff;color:#fff;border:none;border-radius:4px;padding:8px 15px;}
                QPushButton:hover{background:#2383ff;}
            """)
            return
        elif on_save == 2:
            self._on_save = 0

        if self._on_save == 1:
            return

        save_flag = self.check_current_data_save_by_dirty()
        if save_flag == self._save_flag and save_flag == False:
            return
        else:
            self._save_flag = save_flag

        if save_flag:
            self.floating_save_btn.setEnabled(True)
            self.floating_save_btn.setStyleSheet("""
                QPushButton{background:#333333;color:#fff;border:none;border-radius:4px;padding:8px 15px;}
                QPushButton:hover{background:#555555;}
            """)
            self.floating_save_btn.setText("Save")
            self.floating_save_btn.clearIcon()

        else:
            self.floating_save_btn.setText("")
            self.floating_save_btn.setIcon("success_icon.png", (36, 36))
            self.floating_save_btn.setStyleSheet("""
                QPushButton{background:#bbf795;color:#bbf795;border:none;border-radius:4px;}
            """)
            QTimer.singleShot(1000, lambda: (
                self.floating_save_btn.setEnabled(False),
                self.floating_save_btn.setText("Save"),
                self.floating_save_btn.clearIcon(),
                self.floating_save_btn.setStyleSheet("""
                    QPushButton{background:#c0c0c0;color:#f2f2f2;border:none;border-radius:4px;padding:8px 15px;}
                """),
            ))


    def _push_undo(self, array_idx: int, mu_idx: int): # moy
        """Push the current MU state into the undo stack and clear the redo stack."""
        self.undo_stack.append({
            "array": array_idx,
            "mu":    mu_idx,
            "pulse": copy.deepcopy( self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]),
            "times": copy.deepcopy( self.MUedition["edition"]["Dischargetimes"][(array_idx, mu_idx)]),
        })
        self.redo_stack.clear() # Any new edits will invalidate the redo history
        self.dirty_depth += 1
        self.update_save_button()

    def _run_with_progress(self, title, task_fn): # add pop-up window moy

        dlg = QProgressDialog("Working…", None, 0, 0, self)
        dlg.setWindowTitle(title)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setCancelButton(None)
        dlg.setAutoClose(True)
        dlg.show()
        QApplication.processEvents()

        try:
            task_fn()
            dlg.setLabelText("Done!")
        except Exception as e:
            dlg.setLabelText(f"Error: {e}")
            raise
        finally:
            dlg.setRange(0, 1)
            dlg.setValue(1)
            QApplication.processEvents()

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

    def exit_edit_mode(self):
        """Exit spike editing mode and reset selection state."""

        if hasattr(self, "add_spikes_btn") and self.add_spikes_btn.get_active():
            print("ESC: deactivating add_spikes button")
            self.add_spikes_button_pushed()
            return

        elif hasattr(self, "delete_spikes_btn") and self.delete_spikes_btn.get_active():
            print("ESC: deactivating delete_spikes button")
            self.delete_spikes_button_pushed()
            return

        if hasattr(self, "selection_tool") and self.selection_tool:
            self.selection_tool.disable()
            self.selection_tool.cleanup()
            self.selection_tool = None

        print("Exited editing mode (via ESC)")

    def _create_shortcuts(self):
        # Short cut
        mapping = {
            "Ctrl+S":       self.save_btn.click,
            Qt.Key_Left:    self.scroll_left_button_pushed,
            Qt.Key_Right:   self.scroll_right_button_pushed,
            Qt.Key_Up:      self.zoom_slider.slider_increase,
            Qt.Key_Down:    self.zoom_slider.slider_decrease,
            "A":            self.add_spikes_btn.click,
            "D":            self.delete_spikes_btn.click,
            "S":            self.delete_dr_btn.click,
            "R":            self.remove_outliers_single_btn.click,
            "Space":        self.update_mu_filter_btn.click,
            "L":            self.lock_spikes_btn.click,
            "E":            self.extend_mu_filter_btn.click,
            "Z":            self.undo_title_btn.click,
            "X":            self.redo_title_btn.click,
            "Esc":          self.exit_edit_mode,
            Qt.Key_0:       self.exit_edit_mode,
        }

        for seq, slot in mapping.items():

            ks = QKeySequence(seq) if isinstance(seq, str) else QKeySequence(seq)
            sc = QShortcut(ks, self)
            sc.setContext(Qt.WindowShortcut)
            sc.activated.connect(slot)


    # Event handlers
    def select_file_button_pushed(self):
        """Open file dialog to select file for editing and automatically import it."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select file", "", "MAT Files (*.mat);;All Files (*.*)")

        if file_path:
            self.pathname = os.path.dirname(file_path) + "/"
            self.filename = os.path.basename(file_path)
            self.file_path_field.setText(self.filename)
            self.select_file_title_btn.setText(self.filename)

            import_data(self)
                    
    def update_action_button_states(self):
        enabled = self.plot_display_mode == 0
        self.add_spikes_btn.setEnabled(enabled)
        self.add_spikes_btn.set_active(False)
        self.delete_spikes_btn.setEnabled(enabled)
        self.delete_spikes_btn.set_active(False)
        self.delete_dr_btn.setEnabled(enabled)
        self.delete_dr_btn.set_active(False)
        self.remove_outliers_single_btn.setEnabled(True)
        self.update_mu_filter_btn.setEnabled(enabled)
        self.extend_mu_filter_btn.setEnabled(enabled)
        self.lock_spikes_btn.setEnabled(enabled)
        self.action_buttons["lock_spikes_button_pushed"].set_active(self.Backup["lock"] == 1 and enabled)
        self.sil_switch.setEnabled(enabled)

        if hasattr(self, "selection_tool"): self.selection_tool.disable()

    def help_button_pushed(self):
        HelpDialog()

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
                checkbox.setStyleSheet("color: #333333; font-family: 'Segoe UI'; font-size: 12pt;")
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

    def mu_checkbox_state_changed(self, _state=None, *, pluse_train_color="#D95535", update_act_btn=True):
        """Handle changes in MU checkbox selection."""
        # Get all checked MUs
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())

        # Update "Check All" checkboxes based on individual selections
        self.update_array_checkboxes()
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
        self.display_selected_mus(checked_mus, pluse_train_color)
        if update_act_btn:
            self.update_action_button_states()

    def update_display_mus(self, pluse_train_color="#D95535"):
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())

        self.display_selected_mus(checked_mus, pluse_train_color)


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
                if state == Qt.CheckState.Checked:
                    self.plot_display_mode = 1
                    self.update_action_button_states()
                else:
                    self.plot_display_mode = 0
                    self.update_action_button_states()

        # Unblock signals
        for checkbox in self.mu_checkboxes:
            checkbox.blockSignals(False)

        self.mu_checkbox_state_changed()

        # Update the display based on selection
        # self.display_selected_mus([cb.objectName() for cb in self.mu_checkboxes if cb.isChecked()])

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

    def aa_checkbox_value_changed(self, checked):
        """Toggle plot anti-aliasing."""
        if not self.MUedition:
            return
        if checked:
            self.aa_fix = True
            pg.setConfigOptions(antialias=True)
            self.spiketrain_plot.removeItem(self.spiketrainCurves[1])
            self.spiketrain_plot.removeItem(self.spiketrainCurves[3])
            self.spiketrain_plot.addItem(self.spiketrainCurves[0])
            self.spiketrain_plot.addItem(self.spiketrainCurves[3])
        else:
            self.aa_fix = False
            self.slider_value_changed(self.zoom_slider.get_slider_value())

    def sps_checkbox_value_changed(self, checked):
        self.spike_train_plot_sort_mode = checked

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
        self._sync_pan_slider() #moy

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
        self._sync_pan_slider()#moy

     # Navigation actions moy
    def slider_value_changed(self, value):
        if (not self.MUedition
                or self.graphstart is None
                or self.graphend   is None):
            return

        full_start = self.MUedition["edition"]["time"][0]
        full_end   = self.MUedition["edition"]["time"][-1]
        full_len   = full_end - full_start

        if not self.aa_fix:
            if value > 30:
                if not pg.getConfigOption('antialias'):
                    pg.setConfigOptions(antialias=True)
                    self.spiketrain_plot.removeItem(self.spiketrainCurves[1])
                    self.spiketrain_plot.removeItem(self.spiketrainCurves[3])
                    self.spiketrain_plot.addItem(self.spiketrainCurves[0])
                    self.spiketrain_plot.addItem(self.spiketrainCurves[3])
            else:
                if pg.getConfigOption('antialias'):
                    pg.setConfigOptions(antialias=False)
                    self.spiketrain_plot.removeItem(self.spiketrainCurves[0])
                    self.spiketrain_plot.removeItem(self.spiketrainCurves[3])
                    self.spiketrain_plot.addItem(self.spiketrainCurves[1])
                    self.spiketrain_plot.addItem(self.spiketrainCurves[3])

        if value <= self.zoom_slider.slider.minimum():
            vb = self.spiketrain_plot.getViewBox()
            vb.enableAutoRange(axis='xy')
            self.graphstart, self.graphend = full_start, full_end
            self.update_plot_limits()
            self._sync_pan_slider()
            return

        max_scale = 1000
        center    = (self.graphstart + self.graphend) / 2
        win_len   = (full_len / max_scale) * (max_scale ** ((100 - value) / 100))

        self.graphstart = center - win_len / 2
        self.graphend   = center + win_len / 2

        self.update_plot_limits()
        self._sync_pan_slider()
    # --------------------------------------------------------------moy
    def _sync_pan_slider(self):

        if not hasattr(self, "pan_slider"):
            return
        if not self.MUedition:
            return

        if self.graphstart is None or self.graphend is None:
            # print("Warning: graphstart or graphend not set yet. Skip syncing pan slider.")
            return

        times = self.MUedition["edition"]["time"]
        full_start, full_end = times[0], times[-1]

        win_len = self.graphend - self.graphstart

        span = full_end - full_start - win_len

        if span <= 0:
            self.pan_slider.blockSignals(True)
            self.center_pan_slider()
            self.pan_slider.setEnabled(False)
            self.pan_slider.blockSignals(False)
            return

        pos = int(round((self.graphstart - full_start) / span * 1000))

        self.pan_slider.blockSignals(True)
        self.pan_slider.setEnabled(True)
        self.pan_slider.setSliderPosition(pos)
        self.pan_slider.blockSignals(False)

    #moy
    def pan_slider_changed(self, value: int):
        if (not self.MUedition
                or self.graphstart is None
                or self.graphend   is None):
            return

        full_start = self.MUedition["edition"]["time"][0]
        full_end   = self.MUedition["edition"]["time"][-1]
        window_len = self.graphend - self.graphstart

        if full_end - full_start <= window_len:
            return

        left  = full_start + (full_end - full_start - window_len) * (value / 1000.0)
        right = left + window_len

        self.graphstart, self.graphend = left, right
        self.update_plot_limits()
        self._sync_pan_slider()#moy

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
        self._sync_pan_slider()#moy

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
        self._sync_pan_slider()#moy

    def update_plot_limits(self):
        """Update the limits of all plots to match the current view."""
        if self.graphstart is None or self.graphend is None:
            return

        if self.plot_display_mode == 0:
            # For single MU view (standard plots)
            safe_set_range(self, self.spiketrain_plot, xrange=[self.graphstart, self.graphend])
            # self.spiketrain_plot.setXRange(self.graphstart, self.graphend)
            # self.dr_plot.setXRange(self.graphstart, self.graphend)

            if self.sil_checkbox.isChecked():
                self.sil_plot.setXRange(self.graphstart, self.graphend)
        else:
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
        print("disable_action_buttons")
        self.add_spikes_btn.setEnabled(False)
        self.delete_spikes_btn.setEnabled(False)
        self.delete_dr_btn.setEnabled(False)
        self.update_mu_filter_btn.setEnabled(False)
        self.extend_mu_filter_btn.setEnabled(False)
        self.lock_spikes_btn.setEnabled(False)

    def enable_action_buttons(self):
        """Re-enable action buttons after selection is complete."""
        print("enable_action_buttons")
        self.add_spikes_btn.setEnabled(True)
        self.delete_spikes_btn.setEnabled(True)
        self.delete_dr_btn.setEnabled(True)
        self.update_mu_filter_btn.setEnabled(True)
        self.extend_mu_filter_btn.setEnabled(True)
        self.lock_spikes_btn.setEnabled(True)

    @smart_button_pushed
    def add_spikes_button_pushed(self):
        """Add spikes by drawing a selection rectangle."""

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
        # self._push_undo(array_idx, mu_idx)

        self.selection_tool = SelectionTool(
            self.spiketrain_plot,
            "add_spikes",
            lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
                "add_spikes", array_idx, mu_idx, x_min, x_max, y_min, y_max
            ),
            lambda: self._push_undo(array_idx, mu_idx),
        )


    @smart_button_pushed
    def delete_spikes_button_pushed(self):
        """Delete spikes by drawing a selection rectangle."""

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
        # self._push_undo(array_idx, mu_idx)

        # Create selection tool
        self.selection_tool = SelectionTool(
            self.spiketrain_plot,
            "delete_spikes",
            lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
                "delete_spikes", array_idx, mu_idx, x_min, x_max, y_min, y_max
            ),
            lambda: self._push_undo(array_idx, mu_idx),
        )

    @smart_button_pushed
    def delete_dr_button_pushed(self):
        """Delete discharge rates by drawing a selection rectangle in the DR plot."""

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
        # self._push_undo(array_idx, mu_idx)

        # Create selection tool
        self.selection_tool = SelectionTool(
            self.dr_plot,
            "delete_dr",
            lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
                "delete_dr", array_idx, mu_idx, x_min, x_max, y_min, y_max
            ),
            lambda: self._push_undo(array_idx, mu_idx),
        )

    def handle_selection_complete(self, action_type, array_idx, mu_idx, x_min, x_max, y_min, y_max):
        """Handle the completion of a selection and process it."""
        # Process the selection
        process_selection(self.MUedition, action_type, array_idx, mu_idx, x_min, x_max, y_min, y_max)

        # Update the display
        # for checkbox in self.mu_checkboxes:
        #     if checkbox.objectName() == f"Array_{array_idx+1}_MU_{mu_idx+1}":
        #         if checkbox.isChecked():
        #             # If the MU is currently checked, update the display
        #             self.mu_checkbox_state_changed()
        #         break
                    # Get the correct pulse train for this MU
        pulse_train_array = self.MUedition["edition"]["Pulsetrain"][array_idx]
        pulse_train = pulse_train_array[mu_idx, :]  # Use 2D indexing to get the full row
        discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))
        self.update_save_button()
        update_dr_plot(self, discharge_times)
        update_spike_train_plot(self, array_idx, mu_idx, pulse_train)

    def lock_spikes_button_pushed(self):
        """Lock the current spikes to keep them during filter updates."""
        print("push lock spikes")
        if self.action_buttons["lock_spikes_button_pushed"].get_active():
            self.Backup["lock"] = 0
            self.action_buttons["lock_spikes_button_pushed"].set_active(False)
        else:
            self.Backup["lock"] = 1
            self.action_buttons["lock_spikes_button_pushed"].set_active(True)

    def remove_outliers_button_pushed(self):
        """Remove outliers from the current motor unit."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())

        if not checked_mus:
            ErrorDialog(text="Please select a MU first!")
            return
        removal_summary = {}
        for mu_text in checked_mus:
            parts = mu_text.split("_")
            if len(parts) < 4:
                continue

            array_idx = int(parts[1]) - 1
            mu_idx = int(parts[3]) - 1

            # Store state for undo
            self._push_undo(array_idx, mu_idx)

            if (array_idx, mu_idx) not in self.MUedition["edition"]["Dischargetimes"] or len(
                self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]) <= 1:
                continue

            # Prepare input for remove_outliers
            pulse_trains = np.zeros((1, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[1]))
            pulse_trains[0, :] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]
            distime_list = [self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]]

            # Call the function
            filtered_distime, removal_dict = remove_outliers(
                self, pulse_trains, distime_list, self.MUedition["signal"]["fsamp"], [mu_text]
            )

            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = filtered_distime[0]
            self.mu_checkbox_state_changed()
            self.update_save_button()
            removal_summary.update(removal_dict)
        if removal_summary:
            summary_lines = [f"{mu}: Removed {cnt} outliers" for mu, cnt in removal_summary.items()]
            self.show_tip("Remove outlier successfully!".join(summary_lines), duration_ms=4000)
            #SuccessDialog(text="Remove outlier successfully!\n\n" + "\n".join(summary_lines))
        else:
            self.show_tip("No outliers were removed.", duration_ms=4000)
            #SuccessDialog(text="No outliers were removed.")

    def undo_button_pushed(self): # moy
        if not self.undo_stack:
            WarningDialog(
                text="Nothing left to undo.",
                enableCheckBox=False,
                enableHelpButton=False
            )
            return

        last = self.undo_stack.pop()
        a, m = last["array"], last["mu"]

        # push the status quo "before undo" into the redo stack
        self.redo_stack.append({
            "array": a,
            "mu":    m,
            "pulse": copy.deepcopy( self.MUedition["edition"]["Pulsetrain"][a][m, :]),
            "times": copy.deepcopy( self.MUedition["edition"]["Dischargetimes"][(a, m)]),
        })

        # Applying undo snapshots
        self.MUedition["edition"]["Pulsetrain"][a][m, :] = last["pulse"]
        self.MUedition["edition"]["Dischargetimes"][(a, m)] = last["times"]

        # Refresh Display
        self.calculate_silval(a, m)
        self.mu_checkbox_state_changed(update_act_btn=False)
        if self.dirty_depth > 0:
            self.dirty_depth -= 1
        self.update_save_button()

    def redo_button_pushed(self):
        if not self.redo_stack:
            WarningDialog(
                text="Nothing left to redo.",
                enableCheckBox=False,
                enableHelpButton=False
            )
            return

        action = self.redo_stack.pop()
        a, m = action["array"], action["mu"]

        # The current state is pushed back onto the undo stack
        self.undo_stack.append({
            "array": a,
            "mu":    m,
            "pulse": copy.deepcopy( self.MUedition["edition"]["Pulsetrain"][a][m, :]),
            "times": copy.deepcopy( self.MUedition["edition"]["Dischargetimes"][(a, m)]),
        })

        # ② Applying redo snapshots
        self.MUedition["edition"]["Pulsetrain"][a][m, :] = action["pulse"]
        self.MUedition["edition"]["Dischargetimes"][(a, m)] = action["times"]

        # Refresh Display
        self.calculate_silval(a, m)
        self.mu_checkbox_state_changed(update_act_btn=False)
        self.dirty_depth += 1
        self.update_save_button()

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

                # # Set pulse train to zeros and minimal discharge times
                # self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = 0
                # self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = np.array([1, fsamp])

                # # Update SIL in checkbox text
                sil_value = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)

                # Flag MU for deletion
                self.MUedition["edition"]["Flag"][array_idx][mu_idx] = 1

                origin_name = "_".join(mu_text.split("_")[-2:])
                checkbox.setText(f"FLAGGED - {origin_name} (SIL: {sil_value:.4f})")

        self.update_save_button()
        # Update the display
        self.mu_checkbox_state_changed()

    def unflag_mu_for_deletion_button_pushed(self):
        """UnFlag the selected motor units for deletion."""
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

                # # Set pulse train to zeros and minimal discharge times
                # self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = 0
                # self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = np.array([1, fsamp])

                # # Update SIL in checkbox text
                sil_value = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)

                # Flag MU for deletion
                self.MUedition["edition"]["Flag"][array_idx][mu_idx] = 0
                origin_name = "_".join(mu_text.split("_")[-2:])

                checkbox.setText(f"{origin_name} (SIL: {sil_value:.4f})")

        # Update the display
        self.update_save_button()
        self.mu_checkbox_state_changed()

    # Visualization methods
    def plot_mu_spiketrains_button_pushed(self):
        """Plot all motor unit spike trains in a new window."""
        if not self.MUedition:
            return

        # Create a new window for the plot
        dialog = PlotDialog("")

        # Create a figure with subplots for each array
        # Some arrays might be empty
        mu_array_length = len(self.MUedition["edition"]["Pulsetrain"])
        for mu_array in self.MUedition["edition"]["Pulsetrain"]:
            if mu_array.shape[0] == 0:
                mu_array_length -= 1
        fig, axes = plt.subplots(1, mu_array_length,
                                 figsize=(15, 8),
                                 constrained_layout=True)

        if len(self.MUedition["edition"]["Pulsetrain"]) == 1:
            axes = [axes]

        # Set figure background color
        fig.patch.set_facecolor("#ffffff")


        # Plot each array
        for array_idx, ax in enumerate(axes):
            # Set axes properties
            ax.set_facecolor("#ffffff")
            ax.tick_params(colors=CleanTheme.TEXT_PRIMARY)
            ax.spines["bottom"].set_color(CleanTheme.TEXT_PRIMARY)
            ax.spines["top"].set_color(CleanTheme.TEXT_PRIMARY)
            ax.spines["left"].set_color(CleanTheme.TEXT_PRIMARY)
            ax.spines["right"].set_color(CleanTheme.TEXT_PRIMARY)

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
                        zorder=10 # change it to the top layer moy
                    )

            arr_sorted_index = list(range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]))

            def quicksort(arr, low, high, discharge_times):
                if low >= high:
                    return

                pivot = arr[high]
                i = low
                for j in range(low, high):
                    if min(discharge_times[array_idx, arr[j]]) < min(discharge_times[array_idx, pivot]):
                        arr[j], arr[i] = arr[i], arr[j]
                        i += 1

                arr[i], arr[high] = arr[high], arr[i]

                quicksort(arr, low, i-1, self.MUedition["edition"]["Dischargetimes"])
                quicksort(arr, i+1, high, self.MUedition["edition"]["Dischargetimes"])

            quicksort(arr_sorted_index, 0, len(arr_sorted_index)-1, self.MUedition["edition"]["Dischargetimes"])

            if not self.spike_train_plot_sort_mode:
                arr_sorted_index = arr_sorted_index[::-1]
            # for idx in arr_sorted_index:
            #     dis = min(self.MUedition["edition"]["Dischargetimes"][array_idx, idx])
            #     print(f"{array_idx} + {idx}: {dis}")

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
            # MU has different color with jet scheme
            cmap = cm.get_cmap("jet", len(arr_sorted_index))

            for plot_idx, mu_idx in enumerate(arr_sorted_index):
                # Looks like time_indices is the same as ["Dischargetimes"][array_idx, mu_idx], don't know why use this
                time_indices = np.where(~np.isnan(firings[mu_idx]))[0]
                ax.plot(
                    self.MUedition["edition"]["time"][time_indices],
                    np.ones_like(time_indices) * (plot_idx + 1),
                    "|",
                    markersize=10,
                    color=cmap(plot_idx)
                )

            # Set labels
            ax.set_title(
                f'Array #{array_idx+1} with {self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]} MUs',
                color=CleanTheme.TEXT_PRIMARY,
                fontsize=12
            )
            ax.set_xlabel("Time (s)", color=CleanTheme.TEXT_PRIMARY)
            if array_idx == 0:
                ax.set_ylabel("MU #", color=CleanTheme.TEXT_PRIMARY)

            # Set y-axis limits with margin
            ax.set_ylim(0, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0] + 1)

        # Add a overall title
        dialog.set_title(f'Raster plots for {mu_array_length} arrays')

        # Add the figure to the dialog
        canvas = FigureCanvas(fig)

        dialog.set_canvas(canvas)

        dialog.show()
        if self.RasterPlotDialog:
            self.RasterPlotDialog.deleteLater()
        self.RasterPlotDialog = dialog


    def plot_mu_firingrates_button_pushed(self):
        """Plot all motor unit firing rates in a new window."""
        if not self.MUedition:
            return

        dialog = PlotDialog("")

        # Create a figure with subplots for each array
        # Some arrays might be empty
        mu_array_length = len(self.MUedition["edition"]["Pulsetrain"])
        for mu_array in self.MUedition["edition"]["Pulsetrain"]:
            if mu_array.shape[0] == 0:
                mu_array_length -= 1
        if mu_array_length == 0:
            ErrorDialog("You don't have any MU, Please Check Your Data!")
        fig, axes = plt.subplots(1, mu_array_length,
                                 figsize=(15, 8),
                                 constrained_layout=True)
        if len(self.MUedition["edition"]["Pulsetrain"]) == 1:
            axes = [axes]

        # Set figure background color
        fig.patch.set_facecolor("#ffffff")

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
            ax.set_facecolor("#ffffff")
            ax.tick_params(colors=CleanTheme.TEXT_PRIMARY)
            ax.spines["bottom"].set_color(CleanTheme.TEXT_PRIMARY)
            ax.spines["top"].set_color(CleanTheme.TEXT_PRIMARY)
            ax.spines["left"].set_color(CleanTheme.TEXT_PRIMARY)
            ax.spines["right"].set_color(CleanTheme.TEXT_PRIMARY)

            # MU has different color with jet scheme
            cmap = cm.get_cmap("jet", self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0])
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
                    ax.plot(self.MUedition["edition"]["time"], smoothed_dr, color=cmap(mu_idx), linewidth=3)
                else:
                    ax.plot(self.MUedition["edition"]["time"], smoothed_dr, color=cmap(mu_idx), linewidth=1, alpha=0.7)

            # Set labels
            ax.set_title(
                f'Array #{array_idx+1} with {self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]} MUs',
                color=CleanTheme.TEXT_PRIMARY,
                fontsize=12,
            )
            ax.set_xlabel("Time (s)", color=CleanTheme.TEXT_PRIMARY)
            if array_idx == 0:
                ax.set_ylabel("Smoothed discharge rates", color=CleanTheme.TEXT_PRIMARY)

        # Add the figure to the dialog
        canvas = FigureCanvas(fig)
        dialog.set_canvas(canvas)

        # Add a overall title
        dialog.set_title(f'Smoothed discharge rates for {mu_array_length} arrays')

        dialog.show()
        if self.DischagePlotDialog:
            self.DischagePlotDialog.deleteLater()
        self.DischagePlotDialog = dialog

    def saveas_button_pushed(self):
        """Save the edited motor units to a selected file."""
        """Open file dialog to select file for editing and automatically save it."""
        if not self.MUedition:
            return
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Save as", "", "MAT Files (*.mat);;All Files (*.*)")

        if file_path:
            self.pathname = os.path.dirname(file_path) + "/"
            self.filename = os.path.basename(file_path)
            self.file_path_field.setText(self.filename)
            self.select_file_title_btn.setText(self.filename)
            self.save_file(file_path)
            SuccessDialog(title_label="Save Complete", text=f"Data saved to:\n{file_path}")


    def save_button_pushed(self):
        """Save the edited motor units to a file."""
        # Determine the save filename
        if self.filename is None:
            return

        if os.path.splitext(self.filename)[0].endswith("_pyedited"):
            savename = os.path.join(self.pathname or "", self.filename)
        else:
            savename = os.path.join(self.pathname or "", os.path.splitext(self.filename)[0] + "_pyedited.mat")
            self.filename = os.path.splitext(self.filename)[0] + "_pyedited.mat"

        self.file_path_field.setText(self.filename)
        self.select_file_title_btn.setText(self.filename)

        self.save_file(savename)

    def save_file(self, filepath):
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
        progress.setValue(50)
        import time

        # Prepare data for saving
        signal = self.MUedition["signal"]
        parameters = copy.deepcopy(self.MUedition.get("parameters", {}))
        edition = copy.deepcopy(self.MUedition["edition"])


        for array_idx, pt in enumerate(edition["Pulsetrain"]):
            n_mu = pt.shape[0]
            flag_arr = edition["Flag"][array_idx]
            for i in range(n_mu):
                flag_arr[i] = 0


        # Convert Pulsetrain to MATLAB-compatible 1xN cell array
        pulsetrain_list = self.MUedition["edition"]["Pulsetrain"]
        pulsetrain_matlab_cell = np.empty((1, len(pulsetrain_list)), dtype=object)
        for i, pt in enumerate(pulsetrain_list):
            pulsetrain_matlab_cell[0, i] = pt
        edition["Pulsetrain"] = pulsetrain_matlab_cell  # overwrite with proper format

        # flag_list = self.MUedition["edition"]["Flag"]
        # flag_matlab_cell = np.empty((1, len(flag_list)), dtype=object)
        # for i, pt in enumerate(flag_list):
        #     flag_matlab_cell[0, i] = pt
        # edition["Flag"] = flag_matlab_cell  # overwrite with proper format

        # Store as string，Fix .mat can not store dict
        for field in ("Dischargetimes", "silval", "silvalcon"):
            if field in edition and isinstance(edition[field], dict):
                # tuple key to str
                safe_dict = {}
                for k, v in edition[field].items():
                    # key: (i,j) -> "[i,j]"
                    k_str = str(list(k))
                    # value: ndarray/list/float
                    if isinstance(v, np.ndarray):
                        v_ = v.tolist()
                    else:
                        v_ = v
                    safe_dict[k_str] = v_
                edition[field] = json.dumps(safe_dict)

        signal["Pulsetrain"] = edition["Pulsetrain"]
        del edition["Pulsetrain"]

        progress.setValue(100)
        # Save the data

        data = {
            "signal":     signal,
            "parameters": parameters,
            "edition":    edition
        }
        self.update_save_button(on_save=1)
        self.select_file_title_btn.setEnabled(False)
        self._save_thread = Save_worker(
            filepath, data,
            on_finished=lambda: (
                self.update_save_button(on_save=2),
                self.show_tip(f"Save Complete! Data saved to: {filepath}", duration_ms=8000),
                self.select_file_title_btn.setEnabled(True)
            ),
            on_error=lambda errmsg: ErrorDialog(
                title_label="Save File Error",
                text=errmsg
            )
        )

        self._save_thread.start()

        self.dirty_depth = 0 #shr

        # Set current data as clear data
        self.initial_data = copy.deepcopy(self.MUedition["edition"])

        # Show a confirmation message
        from PyQt5.QtWidgets import QMessageBox
        #QMessageBox.information(self, "Save Complete", f"Data saved to {savename}", QMessageBox.Ok)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
            elif item.spacerItem():
                pass

    def showEvent(self, event):
        """Event triggered when the widget is shown."""
        self.sub_panel.show()

        # Call the parent method
        super().showEvent(event)

    def hideEvent(self, event):
        """Event triggered when the widget is hidden."""
        self.sub_panel.hide()

        # Call the parent method
        super().hideEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MUeditManual()
    window.show()
    sys.exit(app.exec_())
