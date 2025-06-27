# app/gui/pages/VisualisationPage.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from ui.components import ActionButton
from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDropdown import FormDropdown
from .VisualizationPanel import VisualizationPanel
from .ChannelViewer import ChannelViewer


class VisualisationPage(QWidget):
    def __init__(self, emg_data, parent=None):
        super().__init__(parent)
        self.emg_data = emg_data
        self.channel_group_index = 0
        self.max_index = 0

        # left panel
        left_container = QWidget()
        left_container.setMinimumWidth(250)
        left_container.setMaximumWidth(300)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # signal range dropdown panel (in groups of 8)
        signal_range_group = CollapsiblePanel("Select Signal Range")
        self.range_dropdown = FormDropdown("Select Reference Signal", self.generate_channel_groups())
        signal_range_group.add_widget(self.range_dropdown)
        signal_range_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        lrbuttons = QWidget()
        button_layout = QHBoxLayout()
        self.left_button = QPushButton("←")
        self.left_button.setEnabled(False)
        self.right_button = QPushButton("→")
        self.left_button.clicked.connect(self.leftClicked)
        self.right_button.clicked.connect(self.rightClicked)
        button_layout.addWidget(self.left_button)
        button_layout.addWidget(self.right_button)
        lrbuttons.setLayout(button_layout)
        signal_range_group.add_widget(lrbuttons)

        left_layout.addWidget(signal_range_group)

        # add gap between controls and done button
        left_layout.addStretch()

        # done button
        done_button = ActionButton("Done", primary=True)
        done_button.clicked.connect(self.doneClicked)
        left_layout.addWidget(done_button)

        # main panel (signal graphs)
        self.viewer = ChannelViewer(emg_data)
        self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        vis_panel = VisualizationPanel(title="EMG Channel Viewer", plot_widget=self.viewer)
        vis_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Setup main alyout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Add title
        page_title = QLabel("Channel Viewer")
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

        self.range_dropdown.dropdown.currentIndexChanged.connect(self.channel_group_change)
        self.channel_group_change(0)

    def generate_channel_groups(self):
        total_num_channels = self.emg_data.shape[0]
        if total_num_channels == 0:
            self.right_button.setEnabled(False)
        groups = []
        for start in range(0, total_num_channels + 1, 8):
            end = min(start + 8, total_num_channels)
            groups.append(f"Channels {start + 1}-{end}")
        self.max_index = int((total_num_channels - (total_num_channels % 8)) / 8)
        return groups

    def channel_group_change(self, index):
        self.channel_group_index = index

        if index == 0:
            self.left_button.setEnabled(False)
        else:
            self.left_button.setEnabled(True)

        if index == self.max_index:
            self.right_button.setEnabled(False)
        else:
            self.right_button.setEnabled(True)

        self.range_dropdown.dropdown.setCurrentIndex(index)

        start = index * 8
        end = min(start + 8, self.emg_data.shape[0])
        indices = list(range(start, end))
        self.viewer.set_channel_range(indices)

    def leftClicked(self):
        self.channel_group_change(max(self.channel_group_index - 1, 0))

    def rightClicked(self):
        self.channel_group_change(min(self.channel_group_index + 1, self.max_index))

    def doneClicked(self):
        # TODO: Update data with omitted data removed
        self.close()

    def keyPressEvent(self, a0):
        if a0 is None:
            return

        if a0.key() == Qt.Key.Key_Left:
            self.leftClicked()
        elif a0.key() == Qt.Key.Key_Right:
            self.rightClicked()
        elif a0.key() == Qt.Key.Key_Return:
            self.doneClicked()
        else:
            super().keyPressEvent(a0)
