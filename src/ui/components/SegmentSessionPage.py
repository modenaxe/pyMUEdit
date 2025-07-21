from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QLabel
from PyQt5.QtGui import QFont
import numpy as np
import pandas as pd
from core.utils.config_and_input.segmenttargets import segmenttargets
import pyqtgraph as pg
import matplotlib.cm as cm
import scipy.io as sio

from ui.components import ActionButton
from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDoubleSpinBox import FormDoubleSpinBox
from ui.components.FormDropdown import FormDropdown
from ui.components.FormSpinBox import FormSpinBox
from .VisualizationPanel import VisualizationPanel

class SegmentSessionPage(QWidget):
    def __init__(self, emg_obj, filename, parent=None):
        super().__init__(parent)
        self.emg_obj = emg_obj
        self.rois = []
        self.coordinates = []
        self.data = {"data": [], "auxiliary": [], "target": [], "path": []}
        self.filename = filename
        self.file = sio.loadmat(filename)
        self.setMinimumSize(1024, 700)

        # left panel
        left_container = QWidget()
        left_container.setMinimumWidth(250)
        left_container.setMaximumWidth(300)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # signal visualisation plot
        self.vis_plot = pg.PlotWidget()
        self.vis_plot.setBackground("w")
        self.vis_plot.setLabel("left", "Amplitude")
        self.vis_plot.setLabel("bottom", "Time (s)")
        self.vis_plot.showGrid(x=True, y=True)
        self.vis_plot.setMinimumHeight(250)

        vis_panel = VisualizationPanel(plot_widget=self.vis_plot)
        vis_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # reference signal dropdown panel
        reference_signal_panel = CollapsiblePanel("Reference Signal")
        self.reference_dropdown = FormDropdown("Select Reference Signal", self.generate_signal_reference_options())
        reference_signal_panel.add_widget(self.reference_dropdown)
        reference_signal_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.reference_dropdown.dropdown.currentIndexChanged.connect(self.on_reference_signal_change)

        # segmentation parameters dropdown panel
        segmentation_param_panel = CollapsiblePanel("Segmentation Parameters")
        self.threshold_dropdown = FormDoubleSpinBox("Threshold", 0, 0, 1, 0.1)
        self.threshold_dropdown.spinbox.valueChanged.connect(self.threshold_edit_field_value_changed)
        segmentation_param_panel.add_widget(self.threshold_dropdown)
        self.windows_dropdown = FormSpinBox("Windows", 0, 0, 10)
        self.windows_dropdown.spinbox.valueChanged.connect(self.windows_edit_field_value_changed)
        segmentation_param_panel.add_widget(self.windows_dropdown)
        segmentation_param_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        left_layout.addWidget(reference_signal_panel)
        left_layout.addWidget(segmentation_param_panel)

        # concatenate button
        self.concat_button = ActionButton("Concatenate", primary=False)
        self.concat_button.clicked.connect(self.concat_clicked)
        left_layout.addWidget(self.concat_button)

        # split button
        self.split_button = ActionButton("Split", primary=False)
        self.split_button.clicked.connect(self.split_clicked)
        left_layout.addWidget(self.split_button)

        # add gap between controls and done button
        left_layout.addStretch()

        # done button
        done_button = ActionButton("Done", primary=True)
        done_button.clicked.connect(self.done_clicked)
        left_layout.addWidget(done_button)

        # Setup main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Add title
        page_title = QLabel("Segment Session")
        page_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        page_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        main_layout.addWidget(page_title)

        # combine panels in layout
        content_layout = QHBoxLayout()
        content_layout.addWidget(left_container, stretch=0)
        content_layout.addWidget(vis_panel, stretch=1)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setFocus()

        self.on_reference_signal_change()

    # Create the dropdown signal reference options
    def generate_signal_reference_options(self):
        options = ["EMG amplitude"]
        for name in self.emg_obj.signal_dict["auxiliaryname"]:
            options.append(name)
        return options

    def on_reference_signal_change(self):
        self.vis_plot.clear()
        if self.reference_dropdown.dropdown.currentText() == "EMG amplitude":
            self.threshold_dropdown.setEnabled(False)
            data = self.emg_obj.signal_dict["data"]
            fsamp = self.emg_obj.signal_dict["fsamp"]

            n_rows = data.shape[0] // 2
            tmp = np.zeros((n_rows, data.shape[1]))

            for i in range(n_rows):
                abs_signal = np.abs(data[i, :])
                abs_df = pd.DataFrame(abs_signal)
                tmp[i, :] = abs_df.rolling(window=fsamp).mean().to_numpy().flatten()

            target = np.mean(tmp, axis=0)
            self.emg_obj.signal_dict["target"] = target
            self.emg_obj.signal_dict["path"] = target

            # Plot each row of the data
            for row in tmp:
                self.vis_plot.plot(row, pen=pg.mkPen(color=(128, 128, 128), width=0.25))

            # Plot the mean/target
            self.vis_plot.plot(target, pen=pg.mkPen(color=(217, 84, 26), width=2))
        else:
            self.threshold_dropdown.setEnabled(True)
            index = 0
            for i, name in enumerate(self.emg_obj.signal_dict["auxiliaryname"]):
                # Find which auxiliary channel corresponding to the selected reference signal
                if self.reference_dropdown.dropdown.currentText() == name:
                    index = i

            target = self.emg_obj.signal_dict["auxiliary"][index, :]
            # Plot the data
            self.vis_plot.plot(target, pen=pg.mkPen(color=(0.95, 0.95, 0.95), width=2))

    def threshold_edit_field_value_changed(self):
        threshold = self.threshold_dropdown.spinbox.value()
        target = self.emg_obj.signal_dict["target"]
        if self.reference_dropdown.dropdown.currentText() != "EMG amplitude":
            # Segment target using threshold
            self.coordinates = segmenttargets(target, 1, threshold)
            fsamp = self.emg_obj.signal_dict["fsamp"]

            for i in range(len(self.coordinates) // 2):
                self.coordinates[i * 2] -= fsamp
                self.coordinates[i * 2 + 1] += fsamp

            # Clamp coordinates to valid range
            self.coordinates = np.clip(self.coordinates, 1, len(target))

            # Update plot
            self.vis_plot.clear()
            self.vis_plot.plot(target, pen=pg.mkPen(color=(0.95, 0.95, 0.95), width=2))

            # Add vertical lines for segments
            for i in range(len(self.coordinates) // 2):
                # Blue-ish hues
                hue = 0.6 - (i / (len(self.coordinates) // 2) * 0.3)
                colour = pg.hsvColor(hue, 0.8, 0.9)
                self.vis_plot.addLine(x=self.coordinates[i * 2], pen=pg.mkPen(color=colour, width=2))
                self.vis_plot.addLine(x=self.coordinates[i * 2 + 1], pen=pg.mkPen(color=colour, width=2))

            self.vis_plot.enableAutoRange(axis='y')

    def windows_edit_field_value_changed(self):
        num_windows = self.windows_dropdown.spinbox.value()
        target = self.emg_obj.signal_dict["target"]

        # Update plot
        self.vis_plot.clear()
        self.vis_plot.plot(target, pen=pg.mkPen(color=(0.95, 0.95, 0.95), width=2))

        self.rois = []
        self.coordinates = [0] * (num_windows * 2)

        def on_roi_change():
            for i, roi in enumerate(self.rois):
                region = roi.getRegion()
                x1 = max(int(region[0]), 1)
                x2 = min(int(region[1]), len(target))
                self.coordinates[i * 2] = x1
                self.coordinates[i * 2 + 1] = x2

        cmap = cm.get_cmap('hsv')
        colours = [cmap(i / num_windows) for i in range(num_windows)]

        for i in range(num_windows):
            # Create semi-transparent colour to distinguish each roi
            rgba = colours[i]
            rgb = tuple(int(c * 255) for c in rgba[:3])
            alpha = 127
            colour = pg.mkColor(rgb + (alpha,))

            # Create new ROI region
            roi = pg.LinearRegionItem(values=[i * 1000, i * 1000 + 500])
            roi.setZValue(10)
            roi.setBrush(pg.mkBrush(colour))
            # Allow it to be scaled and moved
            roi.setMovable(True)
            roi.sigRegionChangeFinished.connect(on_roi_change)

            self.vis_plot.addItem(roi)
            self.rois.append(roi)

        on_roi_change()

    def concat_clicked(self):
        self.data["data"] = []
        self.data["auxiliary"] = []
        self.data["target"] = []
        self.data["path"] = []

        signal = self.emg_obj.signal_dict
        num_segments = len(self.coordinates) // 2
        for i in range(num_segments):
            start = self.coordinates[i * 2]
            end = self.coordinates[i * 2 + 1]
            self.data["data"].append(signal["data"][:, start:end])
            self.data["auxiliary"].append(signal["auxiliary"][:, start:end])
            self.data["target"].append(signal["target"][start:end])

        self.data["data"] = np.hstack(self.data["data"])
        self.data["auxiliary"] = np.hstack(self.data["auxiliary"])
        self.data["target"] = np.hstack(self.data["target"])

        signal["data"] = self.data["data"]
        signal["auxiliary"] = self.data["auxiliary"]
        signal["target"] = self.data["target"]
        signal["path"] = signal["target"]

        self.vis_plot.clear()
        # Update plot
        self.vis_plot.plot(signal["target"], pen=pg.mkPen(color=(0.95, 0.95, 0.95), width=2))

        # Disable split and concat buttons
        self.concat_button.setEnabled(False)
        self.split_button.setEnabled(False)

        # Save updated file
        sio.savemat(self.filename, {"signal": signal}, do_compression=True)

    def split_clicked(self):
        signal = self.emg_obj.signal_dict
        num_segments = len(self.coordinates) // 2

        for i in range(num_segments):
            start = self.coordinates[i * 2]
            end = self.coordinates[i * 2 + 1]

            # Extract segments
            self.data["data"].append(signal["data"][:, start:end])
            self.data["auxiliary"].append(signal["auxiliary"][:, start:end])
            self.data["target"].append(signal["target"][start:end])
            self.data["path"].append(signal["target"][i])

            signal["data"] = self.data["data"][i]
            signal["auxiliary"] = self.data["auxiliary"][i]
            signal["target"] = self.data["target"][i]
            signal["path"] = self.data["path"][i]

            # Save the segment into a .mat file
            save_filename = f"{self.filename}_{i + 1}.mat"
            sio.savemat(save_filename, {"signal": signal}, do_compression=True)

        self.vis_plot.clear()
        # Update plot to be the first segment
        self.vis_plot.plot(self.data["target"][0], pen=pg.mkPen(color=(0.95, 0.95, 0.95), width=2))

        # Disable split and concat buttons
        self.concat_button.setEnabled(False)
        self.split_button.setEnabled(False)


    def done_clicked(self):
        self.close()
