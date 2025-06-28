from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ChannelViewer(QWidget):
    def __init__(self, emg_data, parent=None):
        super().__init__(parent)
        self.entire_emg_data = emg_data  # Expecting a 2D NumPy array [channels x time]
        self.channel_indices = list(range(0, 8))

        self.layout = QVBoxLayout()

        # Matplotlib canvas for plotting
        self.figure = Figure(figsize=(8, 3))
        self.canvas = FigureCanvas(self.figure)

        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

        # display initial plot
        self.update_plot()

    def set_channel_range(self, indices):
        self.channel_indices = indices
        self.update_plot()

    def update_plot(self):
        self.figure.clear()
        colours = ["red", "sienna", "olive", "limegreen", "lightseagreen", "royalblue", "blueviolet", "mediumorchid"]

        # create one subplot for each channel in the index range
        n = len(self.channel_indices)
        for i, index in enumerate(self.channel_indices):
            ax = self.figure.add_subplot(n, 1, i + 1)
            ax.plot(self.entire_emg_data[index], linewidth=0.8, color=colours[i])
            ax.set_ylabel(f"Ch {index + 1}", fontsize=14, labelpad=15)
            ax.grid(True)
            ax.set_yticklabels([])
            # hide x-axis label (except for last plot)
            if i < n - 1:
                ax.set_xticklabels([])

            # add title for first plot only
            if i == 0:
                ax.set_title(f"Channels {self.channel_indices[0]}-{self.channel_indices[7]}", fontsize=20, pad=15)

        ax.set_xlabel("Time", fontsize=20, labelpad=15)
        self.canvas.draw()
