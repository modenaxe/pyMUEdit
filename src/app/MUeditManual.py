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
from core.logger import logger
from types import MethodType
import datetime
from pathlib import Path

import h5py

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from types import MethodType

from ui.MUeditManualUI import setup_ui
from core.utils.manual_editing.getsil import getsil
from core.utils.manual_editing.refinesil import refinesil
from core.utils.manual_editing.h5_import import h5py_convert
from core.utils.manual_editing.save_worker import Save_worker
from core.utils.manual_editing.extendfilter import extendfilter
from core.utils.manual_editing.selection_tools import SelectionTool, process_selection

from core.utils.postprocessing.remove_duplicates import remove_duplicates
from core.utils.postprocessing.remove_duplicates_between_arrays import remove_duplicates_between_arrays
from core.utils.preprocessing.extend_emg import extend_emg
from core.utils.preprocessing.whiten_emg import whiten_emg

from core.utils.manual_editing.smart_button_pushed import smart_button_pushed
from core.utils.manual_editing.batch_filter_worker import batch_filter_worker
from core.utils.manual_editing.duplicates_within_grids_worker import duplicates_within_grids_worker
from core.utils.manual_editing.duplicates_between_grids_worker import duplicates_between_grids_worker

from core.utils.io.filesize_formatter import filesize_formatter

from app.muEditFunctions.importer import import_data
from app.muEditFunctions.plotting import *
from app.muEditFunctions.mu_selection import (
    mu_checkbox_state_changed,
    calculate_silval
)
from app.muEditFunctions.edit_actions import (
    add_spikes_button_pushed,
    delete_spikes_button_pushed,
    delete_dr_button_pushed,
    remove_outliers_button_pushed,
    lock_spikes_button_pushed
)
from app.muEditFunctions.mu_filter_actions import (
    update_mu_filter_button_pushed,
    extend_mu_filter_button_pushed,
)
from app.muEditFunctions.mu_selection import update_display_mus

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

    def __init__(self, filename=None, pathname=None, raw_fileid=None, parent=None):
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
        self.overlay_data = None
        self.action_logs = []
        self.raw_fileid = raw_fileid

        # Connected methods to class
        self.add_spikes_button_pushed = MethodType(add_spikes_button_pushed, self)
        self.delete_spikes_button_pushed = MethodType(delete_spikes_button_pushed, self)
        self.delete_dr_button_pushed = MethodType(delete_dr_button_pushed, self)
        self.remove_outliers_button_pushed = MethodType(remove_outliers_button_pushed, self)
        self.lock_spikes_button_pushed = MethodType(lock_spikes_button_pushed, self)
        self.update_mu_filter_button_pushed = MethodType(update_mu_filter_button_pushed, self)
        self.extend_mu_filter_button_pushed = MethodType(extend_mu_filter_button_pushed, self)
        self.update_display_mus = MethodType(update_display_mus, self)

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

    def log_action(self, message):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": message
        }
        self.action_logs.append(log_entry)
        logger.info(message)

    def get_action_logs(self):
        return self.action_logs

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
            logger.debug("ESC: deactivating add_spikes button")
            add_spikes_button_pushed(self)
            return

        elif hasattr(self, "delete_spikes_btn") and self.delete_spikes_btn.get_active():
            logger.debug("ESC: deactivating delete_spikes button")
            delete_spikes_button_pushed(self)
            return

        if hasattr(self, "selection_tool") and self.selection_tool:
            self.selection_tool.disable()
            self.selection_tool.cleanup()
            self.selection_tool = None

        logger.debug("Exited editing mode (via ESC)")

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

    def update_footer_file_info(self, file_path):
        if not file_path:
            self.footer.footer_file_info.setText("No file selected")
            self.footer.size_info.setText("Size: --")
            self.footer.format_info.setText("Format: --")
            return
    
        file_name = Path(file_path).name
        file_ext = Path(file_path).suffix
        try:
            file_size = filesize_formatter(file_path)
            size_str = f"{file_size}"
        except Exception:
            size_str = "--"
    
        self.footer.footer_file_info.setText(f"File: {file_name}")
        self.footer.size_info.setText(f"Size: {size_str}")
        self.footer.format_info.setText(f"Format: {file_ext}")

    # Event handlers
    def select_file_button_pushed(self):
        """Open file dialog to select file for editing and automatically import it."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select file",
            "",
            "MAT Files (*.mat);;HDF5 Files (*.h5);;All Files (*.*)"
        )

        if not file_path:
            return 
        
        self.pathname = os.path.dirname(file_path) + "/"
        self.filename = os.path.basename(file_path)
        self.file_path_field.setText(self.filename)
        self.select_file_title_btn.setText(self.filename)
        
        valid = import_data(self)

        if not valid:
            return 

        # Update footer file info only if file imported successfully
        file_info = os.path.join(self.pathname, self.filename)
        if hasattr(self, "update_footer_file_info"):
            self.update_footer_file_info(file_info)

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
        self.action_buttons["lock_spikes_btn"].set_active(self.Backup["lock"] == 1 and enabled)
        self.sil_switch.setEnabled(enabled)

        if hasattr(self, "selection_tool"): self.selection_tool.disable()

    def help_button_pushed(self):
        HelpDialog()

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
        if array_idx is not None:
            self.log_action(f"Array {array_idx+1} checkbox changed to {'checked' if state == Qt.Checked else 'unchecked'}.")
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
            mu_checkbox_state_changed(self)
        except Exception as e:
            logger.exception(f"Error setting reference: {e}")

    def sil_checkbox_value_changed(self):
        """Toggle SIL plot visibility."""
        # Update the plots (visibility of SIL plot will be handled in display_selected_mus)
        mu_checkbox_state_changed(self)

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
        logger.debug("disable_action_buttons")
        self.add_spikes_btn.setEnabled(False)
        self.delete_spikes_btn.setEnabled(False)
        self.delete_dr_btn.setEnabled(False)
        self.update_mu_filter_btn.setEnabled(False)
        self.extend_mu_filter_btn.setEnabled(False)
        self.lock_spikes_btn.setEnabled(False)

    def enable_action_buttons(self):
        """Re-enable action buttons after selection is complete."""
        logger.debug("enable_action_buttons")
        self.add_spikes_btn.setEnabled(True)
        self.delete_spikes_btn.setEnabled(True)
        self.delete_dr_btn.setEnabled(True)
        self.update_mu_filter_btn.setEnabled(True)
        self.extend_mu_filter_btn.setEnabled(True)
        self.lock_spikes_btn.setEnabled(True)

    def handle_selection_complete(self, action_type, array_idx, mu_idx, x_min, x_max, y_min, y_max):
        """Handle the completion of a selection and process it."""
            # ==== 1. Save old discharge times BEFORE modification ====
        old_times = np.array(
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), []),
            copy=True
        )

        # ==== 2. Perform the actual selection action ====
        process_selection(self.MUedition, action_type, array_idx, mu_idx, x_min, x_max, y_min, y_max)

        # ==== 3. Retrieve new discharge times AFTER modification ====
        new_times = np.array(
            self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), [])
        )

        # ==== 4. Compute delta ====
        delta = len(new_times) - len(old_times)

        # ==== 5. Show user feedback ====
        if action_type == "add_spikes" and delta > 0:
            self.show_tip(f"Added {delta} spike(s)", duration_ms=4000)
            logger.info(f"Added {delta} spike(s)")
            self.log_action(f"Selection completed: action={action_type}, array={array_idx+1}, MU={mu_idx+1}, "f"X=({x_min},{x_max}), Y=({y_min},{y_max})")

        elif action_type == "delete_spikes" and delta < 0:
            self.show_tip(f"Deleted {-delta} spike(s)", duration_ms=4000)
            logger.info(f"Deleted {-delta} spike(s)")
            self.log_action(f"Selection completed: action={action_type}, array={array_idx+1}, MU={mu_idx+1}, "f"X=({x_min},{x_max}), Y=({y_min},{y_max})")

        elif action_type == "delete_dr":
            self.show_tip("Deleted discharge rate points", duration_ms=4000)
            logger.info("Deleted discharge rate points")
            self.log_action(f"Selection completed: action={action_type}, array={array_idx+1}, MU={mu_idx+1}, "f"X=({x_min},{x_max}), Y=({y_min},{y_max})")

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

        self.log_action(f"Undo: array {last['array']+1}, MU {last['mu']+1}")

        # Refresh Display
        calculate_silval(self, a, m)
        mu_checkbox_state_changed(self, update_act_btn=False)
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

        self.MUedition["edition"]["Pulsetrain"][a][m, :] = action["pulse"]
        self.MUedition["edition"]["Dischargetimes"][(a, m)] = action["times"]

        self.log_action(f"Redo: array {action['array']+1}, MU {action['mu']+1}")

        # Refresh Display
        calculate_silval(self, a, m)
        mu_checkbox_state_changed(self, update_act_btn=False)
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

                self.log_action(f"Flagged MU (Array {array_idx+1}, MU {mu_idx+1}) for deletion.")

        self.update_save_button()
        # Update the display
        mu_checkbox_state_changed(self)

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

                self.log_action(f"Unflagged MU (Array {array_idx+1}, MU {mu_idx+1}) for deletion.")

        # Update the display
        self.update_save_button()
        mu_checkbox_state_changed(self)

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
                logger.exception(f"Error calculating SIL for array {array_idx}, MU {mu_idx}: {e}")
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MUeditManual()
    window.show()
    sys.exit(app.exec_())
