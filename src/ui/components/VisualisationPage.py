# app/gui/pages/VisualisationPage.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy

from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDropdown import FormDropdown
from ui.components.FormSpinBox import FormSpinBox
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

        # main panel (signal graphs)
        self.viewer = ChannelViewer(emg_data)
        self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # signal range dropdown panel
        signal_range_group = SettingsGroup("Select Signal Range")
        self.range_dropdown = FormDropdown("Select Reference Signal", self.generate_channel_groups())
        signal_range_group.add_field(self.range_dropdown)
        left_layout.addWidget(signal_range_group)

        # number of signals dropdown panel
        self.num_signals_input_box = FormSpinBox("Number of Signals to Display", 8, 1, 16)
        left_layout.addWidget(self.num_signals_input_box)

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

        # connect the range input change to the channel_group_change function
        self.range_dropdown.dropdown.currentIndexChanged.connect(self.channel_group_change)
        self.channel_group_change(0)

        # connect the num signals input change to the num_signal_display_change function
        self.num_signals_input_box.spinbox.valueChanged.connect(self.num_signal_display_change)

    # Create the dropdown channel range options
    def generate_channel_groups(self):
        total_num_channels = self.emg_data.shape[0]
        groups = []
        increment = self.viewer.num_indices
        for start in range(0, total_num_channels + 1, increment):
            end = min(start + increment, total_num_channels)
            groups.append(f"Channels {start + 1}-{end}")

        return groups

    # Update the channel viewer based on channel range option selected
    def channel_group_change(self, index):
        increment = self.viewer.num_indices
        start = index * increment
        end = min(start + increment, self.emg_data.shape[0])
        indices = list(range(start, end))
        self.viewer.set_channel_range(indices)

    # Update the number of plots displayed depending on input
    def num_signal_display_change(self, n):
        self.viewer.num_indices = n

        # Save current index
        cur_index = self.range_dropdown.dropdown.currentIndex()

        # Update the dropdown to reflect new index ranges
        new_ranges = self.generate_channel_groups()
        self.range_dropdown.dropdown.clear()
        self.range_dropdown.dropdown.addItems(new_ranges)

        # Reset index to the first range index
        self.range_dropdown.dropdown.setCurrentIndex(0)
        self.channel_group_change(0)
