import math

import matplotlib.cm as cm
import numpy as np
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ui.components.ElectrodeGrid import ElectrodeGrid


class ChannelViewer(QWidget):
    def __init__(self, emg_obj, channel_group_change, parent=None):
        super().__init__(parent)
        # Expecting a 2D NumPy array [channels x time]
        self.entire_emg_data = emg_obj.signal_dict["data"]
        self.emg_obj = emg_obj
        self.channel_indices = list(range(0, 8))
        # Default number of channels to display is 8
        self.num_indices = 8
        self.rejected_channels = []
        self.channel_group_change = channel_group_change

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(40, 0, 50, 30)

        # Use PyQt graph for plotting
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground("w")
        self.layout.addWidget(self.plot_widget, stretch=5)

        # Electrode grid
        self.electrode_grid = ElectrodeGrid(
            self.emg_obj,
            self.channel_indices,
            self.set_channel_range_from_index)
        self.layout.addWidget(self.electrode_grid)

        self.setLayout(self.layout)

        # Display initial plot
        self.update_plot()

    def set_channel_range(self, indices):
        self.channel_indices = indices
        self.update_plot()
        self.electrode_grid.update_indices(indices)

    def set_channel_range_from_index(self, index):
        self.channel_group_change(math.floor(index / self.num_indices))

    def update_plot(self):
        self.plot_widget.clear()

        n = len(self.channel_indices)
        colours = get_n_colours(n)

        self.curves = []
        self.plot_items = []

        fs = self.emg_obj.signal_dict.get("fsamp") # Sampling frequency in Hz, number of samples per second, default is 2048 Hz

        for i, index in enumerate(self.channel_indices):
            p = self.plot_widget.addPlot(row=i, col=0)
            # Show x axis grid lines only
            p.showGrid(x=True, y=False, alpha=5.0)
            # Channel numbers as y axis label
            p.setLabel('left', f"{index + 1}", **
                       {"color": "black", "font-size": "12pt"})
            p.getAxis('left').setTicks([])  # Hide y axis ticks
            
            # Plot data
            y = self.entire_emg_data[index]
            x = np.arange(len(y)) / fs # Time in seconds

            # Subsample every nth point to improve performance
            subsample_step = 10 # Change this value as needed

            y_sub = y[::subsample_step] # Use splicing to keep every nth sample
            x_sub = x[::subsample_step]

            curve = p.plot(x_sub, y_sub, pen=pg.mkPen(color=colours[i], width=1))
            self.curves.append(curve)
            self.plot_items.append(p)

            # Hide x axis labels for all but last plot
            if i < n - 1:
                p.getAxis("bottom").setStyle(showValues=False)
            else:
                p.setLabel('bottom', "Time", **
                           {"color": "black", "font-size": "12pt"})

        # Place 'Channels Title' above the first plot
        first_plot = self.plot_items[0]
        first_plot.setTitle(
            f"Channels {self.channel_indices[0] + 1}-{self.channel_indices[-1] + 1}", )


def get_n_colours(n):
    cmap = pg.colormap.get("hsv", source="matplotlib")
    return [cmap.map(i / n)[:3] for i in range(n)]
