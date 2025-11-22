import os

import matplotlib.cm as cm
import numpy as np
import pandas as pd
import pyqtgraph as pg
import scipy.io as sio
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                             QWidget)

from core.database.database import upsert_file_versions
from core.utils.data_processing.segmenttargets import segmenttargets
from core.utils.session.convert_h5 import save_as_h5
from ui.components import ActionButton
from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDoubleSpinBox import FormDoubleSpinBox
from ui.components.FormDropdown import FormDropdown
from ui.components.FormSpinBox import FormSpinBox

from .VisualizationPanel import VisualizationPanel


class SegmentSessionPage(QWidget):
    def __init__(
            self,
            filename,
            on_new_segment,
            on_done_clicked,
            raw_fileid,
            parent=None):
        super().__init__(parent)
        self.rois = []
        self.coordinates = []
        self.data = {"data": [], "auxiliary": [], "target": [], "path": []}
        self.filename = filename
        self.file = sio.loadmat(filename)
        self.setMinimumSize(1024, 700)
        self.on_new_segment = on_new_segment
        self.on_done_clicked = on_done_clicked

        self.raw_fileid = raw_fileid

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

        # segmentation options dropdown panel
        segmentation_options_panel = CollapsiblePanel("Segmentation Options")
        self.reference_dropdown = FormDropdown(
            "Select Reference Signal",
            self.generate_signal_reference_options())
        segmentation_options_panel.add_widget(self.reference_dropdown)
        self.reference_dropdown.dropdown.currentIndexChanged.connect(
            self.on_reference_signal_change)

        # segmentation_options_panel.addSpacing(5)

        self.threshold_dropdown = FormDoubleSpinBox("Automatic (Select Threshold)", 0, 0, 1, 0.1)
        self.threshold_dropdown.spinbox.valueChanged.connect(
            self.threshold_edit_field_value_changed)
        segmentation_options_panel.add_widget(self.threshold_dropdown)

        # segmentation_options_panel.addSpacing(5)

        self.windows_dropdown = FormSpinBox("Manual (Select Windows)", 0, 0, 10)
        self.windows_dropdown.spinbox.valueChanged.connect(
            self.windows_edit_field_value_changed)
        segmentation_options_panel.add_widget(self.windows_dropdown)

        segmentation_options_panel.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed)

        # segmentation parameters dropdown panel
        # segmentation_param_panel = CollapsiblePanel("Segmentation Parameters")
        # self.threshold_dropdown = FormDoubleSpinBox("Threshold", 0, 0, 1, 0.1)
        # self.threshold_dropdown.spinbox.valueChanged.connect(
        #     self.threshold_edit_field_value_changed)
        # segmentation_param_panel.add_widget(self.threshold_dropdown)
        # self.windows_dropdown = FormSpinBox("Windows", 0, 0, 10)
        # self.windows_dropdown.spinbox.valueChanged.connect(
        #     self.windows_edit_field_value_changed)
        # segmentation_param_panel.add_widget(self.windows_dropdown)
        # segmentation_param_panel.setSizePolicy(
        #     QSizePolicy.Preferred, QSizePolicy.Fixed)

        left_layout.addWidget(segmentation_options_panel)
        # left_layout.addWidget(segmentation_param_panel)

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
        for name in self.file["signal"]["auxiliaryname"][0, 0]:
            options.append(name.strip())

        return options

    def on_reference_signal_change(self):
        self.vis_plot.clear()
        if self.reference_dropdown.dropdown.currentText() == "EMG amplitude":
            self.threshold_dropdown.setEnabled(False)
            data = self.file["signal"][0, 0]["data"]
            fsamp = self.file["signal"][0, 0]["fsamp"][0, 0]

            n_rows = data.shape[0] // 2
            tmp = np.zeros((n_rows, data.shape[1]))

            for i in range(n_rows):
                abs_signal = np.abs(data[i, :])
                abs_df = pd.DataFrame(abs_signal)
                tmp[i, :] = abs_df.rolling(
                    window=fsamp).mean().to_numpy().flatten()

            self.file["signal"][0, 0]["target"] = np.mean(tmp, axis=0)
            self.file["signal"][0, 0]["path"] = np.mean(tmp, axis=0)

            # Plot each row of the data
            for row in tmp:
                self.vis_plot.plot(
                    row,
                    pen=pg.mkPen(
                        color=(
                            128,
                            128,
                            128),
                        width=0.25))

            # Plot the mean/target
            self.vis_plot.plot(self.file["signal"][0, 0]["target"], pen=pg.mkPen(
                color=(217, 84, 26), width=2))
        else:
            self.threshold_dropdown.setEnabled(True)
            index = 0
            for i, name in enumerate(
                    self.file["signal"][0, 0]["auxiliaryname"]):
                # Find which auxiliary channel corresponding to the selected
                # reference signal
                if self.reference_dropdown.dropdown.currentText() == name.strip():
                    index = i

            self.file["signal"][0,
                                0]["target"] = self.file["signal"][0,
                                                                   0]["auxiliary"][index,
                                                                                   :]
            # Plot the data
            self.vis_plot.plot(self.file["signal"][0, 0]["target"], pen=pg.mkPen(
                color=(0.95, 0.95, 0.95), width=2))

    def threshold_edit_field_value_changed(self):
        threshold = self.threshold_dropdown.spinbox.value()
        target = self.file["signal"][0, 0]["target"]
        if self.reference_dropdown.dropdown.currentText() != "EMG amplitude":
            # Segment target using threshold
            self.coordinates = segmenttargets(target, 1, threshold)
            fsamp = self.file["signal"][0, 0]["fsamp"][0, 0]

            for i in range(len(self.coordinates) // 2):
                self.coordinates[i * 2] -= fsamp
                self.coordinates[i * 2 + 1] += fsamp

            # Clamp coordinates to valid range
            self.coordinates = np.clip(self.coordinates, 1, len(target))

            # Update plot
            self.vis_plot.clear()
            self.vis_plot.plot(
                target,
                pen=pg.mkPen(
                    color=(
                        0.95,
                        0.95,
                        0.95),
                    width=2))

            # Add vertical lines for segments
            for i in range(len(self.coordinates) // 2):
                # Blue-ish hues
                hue = 0.6 - (i / (len(self.coordinates) // 2) * 0.3)
                colour = pg.hsvColor(hue, 0.8, 0.9)
                self.vis_plot.addLine(
                    x=self.coordinates[i * 2], pen=pg.mkPen(color=colour, width=2))
                self.vis_plot.addLine(
                    x=self.coordinates[i * 2 + 1], pen=pg.mkPen(color=colour, width=2))

            self.vis_plot.enableAutoRange(axis='y')

    def windows_edit_field_value_changed(self):
        num_windows = self.windows_dropdown.spinbox.value()
        target = self.file["signal"][0, 0]["target"]

        # Update plot
        self.vis_plot.clear()
        self.vis_plot.plot(
            target,
            pen=pg.mkPen(
                color=(
                    0.95,
                    0.95,
                    0.95),
                width=2))

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
            roi = pg.LinearRegionItem(values=[i * 3000, i * 3000 + 1500])
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

        num_segments = len(self.coordinates) // 2
        for i in range(num_segments):
            start = self.coordinates[i * 2]
            end = self.coordinates[i * 2 + 1]
            self.data["data"].append(
                self.file["signal"][0, 0]["data"][:, start:end])
            self.data["auxiliary"].append(
                self.file["signal"][0, 0]["auxiliary"][:, start:end])
            self.data["target"].append(
                self.file["signal"][0, 0]["target"][start:end])

        self.data["data"] = np.hstack(self.data["data"])
        self.data["auxiliary"] = np.hstack(self.data["auxiliary"])
        self.data["target"] = np.hstack(self.data["target"])

        self.file["signal"][0, 0]["data"] = self.data["data"]
        self.file["signal"][0, 0]["auxiliary"] = self.data["auxiliary"]
        self.file["signal"][0, 0]["target"] = self.data["target"]
        self.file["signal"][0, 0]["path"] = self.file["signal"][0, 0]["target"]

        self.vis_plot.clear()
        # Update plot
        self.vis_plot.plot(self.file["signal"][0, 0]["target"], pen=pg.mkPen(
            color=(0.95, 0.95, 0.95), width=2))

        # Disable split and concat buttons
        self.concat_button.setEnabled(False)
        self.split_button.setEnabled(False)

        # Save updated file
        signal = self.file["signal"][0, 0]
        save_filename = f"{self.filename.split('.')[0]}_concatenated.mat"
        sio.savemat(save_filename, {"signal": signal}, do_compression=True)

        # save as .h5 file
        savename_h5 = f"{self.filename.split('.')[0]}_concatenated.h5"
        save_as_h5(
            {"signal": signal},
            savename_h5,
            raw_filepath=save_filename
        )

        versionid = upsert_file_versions(
            savename_h5, self.raw_fileid, "segmented")
        self.on_new_segment(save_filename)

    def split_clicked(self):
        num_segments = len(self.coordinates) // 2

        for i in range(num_segments):
            start = self.coordinates[i * 2]
            end = self.coordinates[i * 2 + 1]

            # Extract segments
            self.data["data"].append(
                self.file["signal"][0, 0]["data"][:, start:end])
            self.data["auxiliary"].append(
                self.file["signal"][0, 0]["auxiliary"][:, start:end])
            self.data["target"].append(
                self.file["signal"][0, 0]["target"][start:end])
            self.data["path"].append(self.file["signal"][0, 0]["target"][i])

        for i in range(num_segments):
            self.file["signal"][0, 0]["data"] = self.data["data"][i]
            self.file["signal"][0, 0]["auxiliary"] = self.data["auxiliary"][i]
            self.file["signal"][0, 0]["target"] = self.data["target"][i]
            self.file["signal"][0,
                                0]["path"] = self.file["signal"][0,
                                                                 0]["target"]

            # Save the segment into a .mat file
            save_filename = f"{self.filename.split('.')[0]}_split_segment_{i + 1}.mat"
            signal = self.file["signal"][0, 0]
            sio.savemat(save_filename, {"signal": signal}, do_compression=True)

            # save as .h5 file
            savename_h5 = f"{self.filename.split('.')[0]}_split_segment_{i + 1}.h5"
            save_as_h5(
                {"signal": signal},
                savename_h5,
                raw_filepath=save_filename
            )

            versionid = upsert_file_versions(
                savename_h5, self.raw_fileid, "segmented")
            self.on_new_segment(save_filename)

        self.vis_plot.clear()
        # Update plot to be the first segment
        self.vis_plot.plot(
            self.data["target"][0],
            pen=pg.mkPen(
                color=(
                    0.95,
                    0.95,
                    0.95),
                width=2))

        # Disable split and concat buttons
        self.concat_button.setEnabled(False)
        self.split_button.setEnabled(False)

    def done_clicked(self):
        self.on_done_clicked()
        self.close()
