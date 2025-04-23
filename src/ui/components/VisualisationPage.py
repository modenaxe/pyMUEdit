# app/gui/pages/VisualisationPage.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from app.gui.components.VisualizationPanel import VisualizationPanel
from app.gui.components.ChannelViewer import ChannelViewer

class VisualisationPage(QWidget):
    def __init__(self, emg_obj, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        # Get matrix from loaded signal dict
        emg_data = emg_obj.signal_dict["data"]

        viewer = ChannelViewer(emg_data)
        vis_panel = VisualizationPanel(title="EMG Channel Viewer", plot_widget=viewer)

        layout.addWidget(vis_panel)
        self.setLayout(layout)
