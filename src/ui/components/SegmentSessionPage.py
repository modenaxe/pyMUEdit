from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QLabel
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ui.components import ActionButton
from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDoubleSpinBox import FormDoubleSpinBox
from ui.components.FormDropdown import FormDropdown
from ui.components.FormSpinBox import FormSpinBox
from .VisualizationPanel import VisualizationPanel

import math

class SegmentSessionPage(QWidget):
    def __init__(self, emg_obj, parent=None):
        super().__init__(parent)
        self.emg_obj = emg_obj
        self.file = None
        self.coordinates = []
        self.data = {"data": [], "auxiliary": [], "target": [], "path": []}
        self.emg_amplitude_cache = None
        self.roi = None
        self.current_window = 0

        self.setMinimumSize(1024, 700)

        # left panel
        left_container = QWidget()
        left_container.setMinimumWidth(250)
        left_container.setMaximumWidth(300)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # signal visualisation plot
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.figure.tight_layout()

        # reference signal dropdown panel
        reference_signal_panel = CollapsiblePanel("Reference Signal")
        self.reference_dropdown = FormDropdown("Select Reference Signal", ["EMG Amplitude", "Path", "Target"])
        reference_signal_panel.add_widget(self.reference_dropdown)
        reference_signal_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # segmentation parameters dropdown panel
        segmentation_param_panel = CollapsiblePanel("Segmentation Parameters")
        self.seg_param_dropdown = FormDoubleSpinBox("Threshold", 0.80, 0, 1)
        segmentation_param_panel.add_widget(self.seg_param_dropdown)
        self.windows_dropdown = FormSpinBox("Windows", 1, 0, 10)
        segmentation_param_panel.add_widget(self.windows_dropdown)
        segmentation_param_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        left_layout.addWidget(reference_signal_panel)
        left_layout.addWidget(segmentation_param_panel)

        # add gap between controls and done button
        left_layout.addStretch()

        # done button
        done_button = ActionButton("Done", primary=True)
        done_button.clicked.connect(self.doneClicked)
        left_layout.addWidget(done_button)

        vis_panel = VisualizationPanel(plot_widget=self.canvas)
        vis_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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

    def doneClicked(self):
        self.close()
