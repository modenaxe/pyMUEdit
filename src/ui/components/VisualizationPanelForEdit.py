from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QWidget, QGraphicsDropShadowEffect, QSizePolicy
)
from .CleanTheme import CleanTheme
from .SectionHeaderForEdit import SectionHeaderForEdit


class VisualizationPanelForEdit(QWidget):
    """
    A standalone visualization panel with a card style, header, and content_layout.
    """

    def __init__(self, title: str, plot_widget: QWidget = None, parent=None):
        super().__init__(parent)

        # Outer layout of the whole panel
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Card frame
        self.card_frame = QFrame()
        self.card_frame.setObjectName("visualizationCard")
        self.card_frame.setFrameShape(QFrame.StyledPanel)
        self.card_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.card_frame.setStyleSheet(
            f"""
            QFrame#visualizationCard {{
                background-color: {CleanTheme.BG_CARD};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 8px;
            }}
            """
        )

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(self.card_frame)
        shadow.setBlurRadius(8)
        shadow.setColor(CleanTheme.SHADOW)
        shadow.setOffset(0, 2)
        self.card_frame.setGraphicsEffect(shadow)

        outer_layout.addWidget(self.card_frame)

        # Main card layout
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Header
        self.header = SectionHeaderForEdit(title)
        self.header.setStyleSheet(f"background-color: #f0f0f0;")
        card_layout.addWidget(self.header)
        self.title_label = self.header.title_label

        # subHeader
        self.subheader = SectionHeaderForEdit("")
        card_layout.addWidget(self.subheader)

        # Content widget and layout (equivalent to CleanCard's)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 0, 25, 15)
        self.content_layout.setSpacing(0)
        card_layout.addWidget(self.content_widget)

        # Optional: add plot widget
        self.plot_widget = None
        if plot_widget:
            self.set_plot_widget(plot_widget)

    def set_plot_widget(self, plot_widget: QWidget):
        """
        Set or replace the plot widget.
        """
        if self.plot_widget:
            self.content_layout.removeWidget(self.plot_widget)
            self.plot_widget.deleteLater()

        self.plot_widget = plot_widget
        self.content_layout.addWidget(self.plot_widget)

    def add_content(self, widget: QWidget):
        """
        Add any widget to the content layout.
        """
        self.content_layout.addWidget(widget)
