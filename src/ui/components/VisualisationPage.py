# app/gui/pages/VisualisationPage.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from .VisualizationPanel import VisualizationPanel
from .ChannelViewer import ChannelViewer


class VisualisationPage(QWidget):
    def __init__(self, emg_data, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        viewer = ChannelViewer(emg_data)
        vis_panel = VisualizationPanel(title="EMG Channel Viewer", plot_widget=viewer)
        layout.addWidget(vis_panel)
        self.setLayout(layout)
