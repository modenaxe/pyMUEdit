# app/gui/pages/VisualisationPage.py
import math

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QSizePolicy, QVBoxLayout, QWidget)

from ui.components import ActionButton
from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDropdown import FormDropdown
from ui.components.FormSpinBox import FormSpinBox

from .ChannelViewer import ChannelViewer
from .VisualizationPanel import VisualizationPanel


class VisualisationPage(QWidget):
    def __init__(self, emg_obj, import_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.emg_obj = emg_obj
        self.emg_data = emg_obj.signal_dict["data"]
        self.channel_group_index = 0
        self.max_index = 0

        self.import_window = import_window

        self.setMinimumSize(1024, 700)

        # define left sidebar
        left_sidebar = QFrame()
        left_sidebar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)
        left_sidebar.setMinimumWidth(250)
        left_sidebar.setMaximumWidth(300)

        left_sidebar_layout = QVBoxLayout(left_sidebar)
        left_sidebar_layout.setContentsMargins(10, 10, 10, 10)
        left_sidebar_layout.setSpacing(10)

        # main panel (signal graphs)
        self.viewer = ChannelViewer(self.emg_obj, self.channel_group_change)
        self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # left sidebar title
        left_sidebar_title = QLabel("Select Signal Range")
        left_sidebar_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        left_sidebar_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        left_sidebar_layout.addWidget(left_sidebar_title)

        # number of signals dropdown panel
        self.num_signals_input_box = FormSpinBox(
            "Number of Signals to Display", 8, 1, 16)
        left_sidebar_layout.addWidget(self.num_signals_input_box)

        signals_limit_label = QLabel("(Max: 16)")
        signals_limit_label.setStyleSheet("color: gray; font-size: 11px;")
        left_sidebar_layout.addWidget(signals_limit_label)

        left_sidebar_layout.addSpacing(5)

        # signal range dropdown panel
        self.range_dropdown = FormDropdown(
            "Select Reference Signal",
            self.generate_channel_groups())
        left_sidebar_layout.addWidget(self.range_dropdown)

        # left and right buttons
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
        left_sidebar_layout.addWidget(lrbuttons)

        # add gap between controls and done button
        left_sidebar_layout.addStretch()

        # done button
        done_button = ActionButton("Done", primary=True)
        done_button.clicked.connect(self.doneClicked)
        left_sidebar_layout.addWidget(done_button)

        vis_panel = VisualizationPanel(plot_widget=self.viewer)
        vis_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Setup main layout
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
        # previously left_container
        content_layout.addWidget(left_sidebar, stretch=0)
        content_layout.addWidget(vis_panel, stretch=1)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # connect the range input change to the channel_group_change function
        self.range_dropdown.dropdown.currentIndexChanged.connect(
            self.channel_group_change)

        # connect the num signals input change to the num_signal_display_change
        # function
        self.num_signals_input_box.spinbox.valueChanged.connect(
            self.num_signal_display_change)

        self.setFocus()

    # Create the dropdown channel range options
    def generate_channel_groups(self):
        total_num_channels = self.emg_data.shape[0]
        if total_num_channels == 0:
            self.right_button.setEnabled(False)
        groups = []
        increment = self.viewer.num_indices
        index = 0
        for start in range(0, total_num_channels, increment):
            end = min(start + increment, total_num_channels)
            groups.append(f"Channels {start + 1}-{end}")
            index += 1

        self.max_index = index - 1
        return groups

    # Update the channel viewer based on channel range option selected
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

        increment = self.viewer.num_indices
        start = index * increment
        end = min(start + increment, self.emg_data.shape[0])
        indices = list(range(start, end))
        self.viewer.set_channel_range(indices)

    # Update the number of plots displayed depending on input
    def num_signal_display_change(self, n):
        self.viewer.num_indices = n

        # Update the dropdown to reflect new index ranges
        new_ranges = self.generate_channel_groups()
        self.range_dropdown.dropdown.clear()
        self.range_dropdown.dropdown.addItems(new_ranges)

        # Reset index to the first range index
        self.range_dropdown.dropdown.setCurrentIndex(0)
        self.channel_group_change(0)

    def leftClicked(self):
        self.channel_group_change(max(self.channel_group_index - 1, 0))

    def rightClicked(self):
        self.channel_group_change(
            min(self.channel_group_index + 1, self.max_index))

    def doneClicked(self):
        # Update the omitted channels
        self.emg_obj.rejected_channel_indices = self.viewer.rejected_channels
        # Update preview plot in case of any changes
        self.import_window.update_preview_plot()
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
