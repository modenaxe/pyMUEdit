from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget, QLabel, QApplication, QSizePolicy
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtSvg import QSvgWidget

from .CleanTheme import CleanTheme


class VisualizationCard(QFrame):
    """A card specifically for visualizations with icon, title and date"""

    def __init__(self, title=None, icon=None, date=None, parent=None):
        super().__init__(parent)

        # Set up styling
        self.setObjectName("visualizationCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumSize(200, 150)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Apply styling - light gray background with subtle border
        self.setStyleSheet(
            f"""
            QFrame#visualizationCard {{
                background-color: {CleanTheme.BG_VISUALIZATION};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 8px;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """
        )

        # Set up layout
        self.layout = QVBoxLayout(self)  # type:ignore
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create the icon area (centered in the card)
        icon_widget = QWidget()
        icon_widget.setFixedHeight(80)
        icon_layout = QVBoxLayout(icon_widget)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add icon if provided
        if icon:
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Handle different icon types
            if isinstance(icon, QIcon):
                pixmap = icon.pixmap(QSize(32, 32))
                icon_label.setPixmap(pixmap)
            elif isinstance(icon, str):
                if icon.endswith(".svg"):
                    # Use QSvgWidget for SVG files
                    svg_widget = QSvgWidget(icon)
                    svg_widget.setFixedSize(32, 32)
                    icon_layout.addWidget(svg_widget)
                else:
                    icon_label.setPixmap(
                        QPixmap(icon).scaled(
                            32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                        )
                    )
                    icon_layout.addWidget(icon_label)
            elif isinstance(icon, int) or (hasattr(icon, "__int__") and not isinstance(icon, bool)):
                std_icon = QApplication.style().standardIcon(icon)  # type:ignore
                pixmap = std_icon.pixmap(QSize(32, 32))
                icon_label.setPixmap(pixmap)
                icon_layout.addWidget(icon_label)
            else:
                # Default icon
                icon_label.setText("📊")
                icon_label.setStyleSheet("font-size: 32px;")
                icon_layout.addWidget(icon_label)
        else:
            # Default icon
            default_icon = QLabel("📊")
            default_icon.setStyleSheet("font-size: 32px;")
            default_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(default_icon)

        self.layout.addWidget(icon_widget)

        # Info section at the bottom of the card
        info_section = QFrame()
        info_section.setObjectName("infoSection")
        info_section.setStyleSheet(
            f"""
            QFrame#infoSection {{
                border-top: 1px solid {CleanTheme.BORDER};
                background-color: {CleanTheme.BG_CARD};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """
        )
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(15, 10, 15, 10)
        info_layout.setSpacing(5)

        # Add title if provided
        if title:
            title_label = QLabel(title)
            title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
            title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            info_layout.addWidget(title_label)

        # Add date if provided
        if date:
            date_label = QLabel(date)
            date_label.setFont(QFont("Segoe UI", 9))
            date_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
            date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            info_layout.addWidget(date_label)

        self.layout.addWidget(info_section)

        # Make card interactive
        self.setCursor(Qt.CursorShape.PointingHandCursor)
