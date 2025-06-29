from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.cm as cm

class ChannelViewer(QWidget):
    def __init__(self, emg_data, parent=None):
        super().__init__(parent)
        # Expecting a 2D NumPy array [channels x time]
        self.entire_emg_data = emg_data
        self.channel_indices = list(range(0, 8))
        # Default number of channels to display is 8
        self.num_indices = 8

        self.layout = QVBoxLayout()

        # Matplotlib canvas for plotting
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.figure.tight_layout()

        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

        # Display initial plot
        self.update_plot()

    def set_channel_range(self, indices):
        self.channel_indices = indices
        self.update_plot()

    def update_plot(self):
        self.figure.clear()
        colours = get_n_colours(self.num_indices)

        # Create one subplot for each channel in the index range
        n = len(self.channel_indices)
        for i, index in enumerate(self.channel_indices):
            ax = self.figure.add_subplot(n, 1, i + 1)
            ax.plot(self.entire_emg_data[index], linewidth=0.8, color=colours[i])
            ax.set_ylabel(f"{index + 1}", fontsize=20, labelpad=25, rotation=0, va='center')
            ax.grid(True)
            ax.set_yticklabels([])
            # Hide x-axis label (except for last plot)
            if i < n - 1:
                ax.set_xticklabels([])

            # Add title for first plot only
            if i == 0:
                ax.set_title(f"Channels {self.channel_indices[0] + 1}-{self.channel_indices[len(self.channel_indices) - 1] + 1}", fontsize=20, pad=15)

        ax.set_xlabel("Time", fontsize=20, labelpad=15)
        self.canvas.draw()

def get_n_colours(n):
    cmap = cm.get_cmap('hsv')
    return [cmap(i / n) for i in range(n)]
