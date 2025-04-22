from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget, QGraphicsDropShadowEffect, QSizePolicy

from .CleanTheme import CleanTheme


class CleanCard(QFrame):
    """A clean, minimalist card component with light background and subtle shadow"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up styling
        self.setObjectName("cleanCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Apply styling
        self.setStyleSheet(
            f"""
            QFrame#cleanCard {{
                background-color: {CleanTheme.BG_CARD};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 8px;
            }}
        """
        )

        # Add very subtle shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(CleanTheme.SHADOW)
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Set up layout
        self.layout = QVBoxLayout(self)  # type:ignore
        self.layout.setContentsMargins(15, 5, 15, 15)
        self.layout.setSpacing(10)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.content_widget)

    def add_content(self, widget):
        """Adds a widget to the card's content area"""
        self.content_layout.addWidget(widget)
