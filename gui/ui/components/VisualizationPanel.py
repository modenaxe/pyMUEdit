from PyQt5.QtWidgets import QVBoxLayout
from .CleanTheme import CleanTheme
from .CleanCard import CleanCard
from .SectionHeader import SectionHeader


class VisualizationPanel(CleanCard):
    """
    A panel for visualizations with a header and plot area

    This component provides a clean card with a header and area for plots
    or other visualization widgets.
    """

    def __init__(self, title, plot_widget=None, parent=None):
        """
        Initialize a visualization panel

        Args:
            title (str): The title for the panel
            plot_widget (QWidget, optional): The plot widget to add
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        # Create layout
        self.panel_layout = QVBoxLayout()
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(10)

        # Create header
        self.header = SectionHeader(title)
        self.panel_layout.addWidget(self.header)

        # Add plot widget if provided
        if plot_widget:
            self.plot_widget = plot_widget
            self.panel_layout.addWidget(self.plot_widget)

        # Add to card content
        self.content_layout.addLayout(self.panel_layout)

    def set_plot_widget(self, plot_widget):
        """
        Set or replace the plot widget

        Args:
            plot_widget (QWidget): The plot widget to set
        """
        if hasattr(self, "plot_widget"):
            # Remove existing plot widget
            self.panel_layout.removeWidget(self.plot_widget)
            self.plot_widget.deleteLater()

        self.plot_widget = plot_widget
        self.panel_layout.addWidget(self.plot_widget)
