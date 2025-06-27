# app/gui/pages/VisualisationPage.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy

from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDropdown import FormDropdown
from ui.components.SettingsGroup import SettingsGroup
from .VisualizationPanel import VisualizationPanel
from .ChannelViewer import ChannelViewer


class VisualisationPage(QWidget):
    def __init__(self, emg_data, parent=None):
        super().__init__(parent)

        # left panel
        left_container = QWidget()
        left_container.setMinimumWidth(250)
        left_container.setMaximumWidth(300)
        left_container.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)

        # signal range panel
        signal_range_group = SettingsGroup("Select Signal Range")
        signal_range_field = FormDropdown("Select Reference Signal", ["EMG Signals 1-8", "EMG Signals 9-16", "EMG Signals 17-24"])
        signal_range_group.add_field(signal_range_field)
        left_layout.addWidget(signal_range_group)

        # main plot panel
        viewer = ChannelViewer(emg_data)
        viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vis_panel = VisualizationPanel(title="EMG Channel Viewer", plot_widget=viewer)
        vis_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # combine panels in layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        main_layout.addWidget(left_container, stretch=0)
        main_layout.addWidget(vis_panel, stretch=1)
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
