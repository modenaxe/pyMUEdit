from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtCore import Qt


class CleanScrollBar:
    """
    A utility class to apply clean, modern scrollbar styling to QScrollAreas.
    """

    @staticmethod
    def apply(
        scroll_area: QScrollArea, with_padding=True, width=8, handle_color="#BBBBBB", handle_hover_color="#999999"
    ):
        """
        Apply clean scrollbar styling to a QScrollArea

        Args:
            scroll_area (QScrollArea): The scroll area to style
            with_padding (bool): Whether to add top/bottom padding
            width (int): Width of the scrollbar in pixels
            handle_color (str): Color of the scrollbar handle
            handle_hover_color (str): Color of the scrollbar handle on hover
        """
        # Set scrollbar visibility policies
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Create padding margin if requested
        padding_margin = "25px 0 25px 0" if with_padding else "0px"

        # Apply styling
        scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #F0F0F0;
                width: {width}px;
                margin: {padding_margin}; /* Top and bottom padding */
                border-radius: {width//2}px;
            }}
            QScrollBar::handle:vertical {{
                background: {handle_color};
                min-height: 20px;
                border-radius: {width//2}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {handle_hover_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
        )

        return scroll_area
