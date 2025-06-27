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
        self.emg_data = emg_data

        # left panel
        left_container = QWidget()
        left_container.setMinimumWidth(250)
        left_container.setMaximumWidth(300)
        left_container.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)

        # signal range dropdown panel (in groups of 8)
        signal_range_group = SettingsGroup("Select Signal Range")
        self.range_dropdown = FormDropdown("Select Reference Signal", self.generate_channel_groups())
        signal_range_group.add_field(self.range_dropdown)
        left_layout.addWidget(signal_range_group)

        # main panel (signal graphs)
        self.viewer = ChannelViewer(emg_data)
        self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        vis_panel = VisualizationPanel(title="EMG Channel Viewer", plot_widget=self.viewer)
        vis_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # combine panels in layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        main_layout.addWidget(left_container, stretch=0)
        main_layout.addWidget(vis_panel, stretch=1)
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.range_dropdown.dropdown.currentIndexChanged.connect(self.channel_group_change)
        self.channel_group_change(0)

    def generate_channel_groups(self):
        total_num_channels = self.emg_data.shape[0]
        groups = []
        for start in range(0, total_num_channels + 1, 8):
            end = min(start + 8, total_num_channels)
            groups.append(f"Channels {start + 1}-{end}")

        return groups

    def channel_group_change(self, index):
        start = index * 8
        end = min(start + 8, self.emg_data.shape[0])
        indices = list(range(start, end))
        self.viewer.set_channel_range(indices)