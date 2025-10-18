import math

import matplotlib.cm as cm
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
import numpy as np
import pyqtgraph as pg
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
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w") 
        self.plot_widget.setLabel("bottom", "Time")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.hideAxis("left")
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
        x = np.arange(self.entire_emg_data.shape[1])

        for i, index in enumerate(self.channel_indices):
            signal = self.entire_emg_data[index]
            # Scaling the signal for each channel
            scaling_signal = signal / (np.max(np.abs(signal)))
            spacing = 2.0
            y_offset = -i * spacing
            
            # Plot the colours
            curve = pg.PlotCurveItem(
                x,
                scaling_signal + y_offset,
                pen=pg.mkPen(color=colours[i], width=1.2)
            )

            self.plot_widget.addItem(curve)
                
            text = pg.TextItem(text=f"{index + 1}", color="black", anchor=(1, 0.5))
            text.setPos(x[0], y_offset)
            self.plot_widget.addItem(text)

        self.plot_widget.setTitle(
            f"Channels {self.channel_indices[0] + 1}-{self.channel_indices[-1] + 1}",
            fontsize=20,
            pad=15
        )

def get_n_colours(n):
    cmap = pg.colormap.get("hsv", source="matplotlib")
    return [cmap.map(i / n)[:3] for i in range(n)]
