from PyQt5.QtWidgets import QWidget, QVBoxLayout
from app.gui.components.VisualizationPanel import VisualizationPanel
from app.gui.components.ChannelViewer import ChannelViewer
from app.data.session_manager import get_current_emg_matrix

class VisualisationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        # Retrieve EMG data matrix from session manager
        emg_data = get_current_emg_matrix()

        # Create channel viewer and pass it into the visualization panel
        viewer = ChannelViewer(emg_data)
        vis_panel = VisualizationPanel(title="EMG Channel Viewer", plot_widget=viewer)

        layout.addWidget(vis_panel)
        self.setLayout(layout)
