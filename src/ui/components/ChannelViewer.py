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

        self.update_plot()  # Display initial plot

    def set_channel_range(self, indices):
        self.channel_indices = indices
        self.update_plot()

    def update_plot(self):
        self.figure.clear()

        # create one subplot for each channel in the index range
        n = len(self.channel_indices)
        for i, index in enumerate(self.channel_indices):
            ax = self.figure.add_subplot(n, 1, i + 1)
            ax.plot(self.entire_emg_data[index], linewidth=0.8)
            ax.set_ylabel(f"Ch {index + 1}")
            ax.grid(True)
            if i < n - 1:
                # hide x-axis label (except for the last one)
                ax.set_xticklabels([])

        ax.set_title(f"Channels {self.channel_indices[0]}-{self.channel_indices[len(self.channel_indices) - 1]}")
        ax.set_xlabel("Time")
        self.canvas.draw()
