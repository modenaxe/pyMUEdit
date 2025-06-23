from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ChannelViewer(QWidget):
    def __init__(self, emg_data, parent=None):
        super().__init__(parent)
        self.emg_data = emg_data  # Expecting a 2D NumPy array [channels x time]

        self.layout = QVBoxLayout()

        # Channel selector dropdown
        self.selector_label = QLabel("Select EMG Channel:")
        self.layout.addWidget(self.selector_label)

        self.channel_selector = QComboBox()
        self.channel_selector.addItems([f"Channel {i+1}" for i in range(self.emg_data.shape[0])])
        self.channel_selector.currentIndexChanged.connect(self.update_plot)
        self.layout.addWidget(self.channel_selector)

        # Matplotlib canvas for plotting
        self.figure = Figure(figsize=(8, 3))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)
        self.update_plot(0)  # Display initial plot

    def update_plot(self, index):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(self.emg_data[index], linewidth=0.8)
        ax.set_title(f"Channel {index + 1}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Amplitude")
        ax.grid(True)
        self.canvas.draw()
