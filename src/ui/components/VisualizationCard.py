from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget, QLabel, QApplication, QSizePolicy, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QCursor
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtSvg import QSvgWidget
import os

from .CleanTheme import CleanTheme


class VisualizationCard(QFrame):
    """A card specifically for visualizations with icon and text below"""

    def __init__(self, title=None, icon=None, date=None, state_path=None, index=0, parent=None):
        super().__init__(parent)

        # Set up styling for the entire card
        self.setObjectName("visualizationCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumSize(150, 200)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Store properties for state persistence
        self.title = title
        self.date = date
        self.icon = icon
        self.state_path = state_path
        self.card_index = index

        # Apply styling - light gray background for the entire card
        self.setStyleSheet(
            f"""
            QFrame#visualizationCard {{
                background-color: #F2F2F2;
                border-radius: 8px;
                border: none;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """
        )

        # Set up layout
        self.layout = QVBoxLayout(self)  # type:ignore
        self.layout.setContentsMargins(13, 13, 13, 13)
        self.layout.setSpacing(8)  # Space between icon area and text

        # Create the icon area (darker gray box)
        self.icon_area = QFrame()
        self.icon_area.setObjectName("iconArea")
        self.icon_area.setMinimumHeight(100)
        self.icon_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.icon_area.setStyleSheet(
            f"""
            QFrame#iconArea {{
                background-color: #D3D3D3;
                border-radius: 6px;
                border: none;
            }}
        """
        )

        # Layout for the icon area to center the icon
        icon_layout = QVBoxLayout(self.icon_area)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add icon if provided
        if icon:
            icon = os.path.join("public", f"{icon}.svg")
            if not os.path.exists(icon):
                print(f"Warning: Icon {icon} not found")
                icon = None

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
                icon_label.setStyleSheet("font-size: 32px; color: white;")
                icon_layout.addWidget(icon_label)
        else:
            # Default icon
            default_icon = QLabel("📊")
            default_icon.setStyleSheet("font-size: 32px; color: white;")
            default_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(default_icon)

        # Add icon area to main layout
        self.layout.addWidget(self.icon_area)

        # Add title if provided
        if title:
            self.title_label = QLabel(title)
            self.title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.layout.addWidget(self.title_label)

        # Add date if provided
        if date:
            self.date_label = QLabel(date)
            self.date_label.setFont(QFont("Segoe UI", 9))
            self.date_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
            self.date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.layout.addWidget(self.date_label)

        # Make card interactive
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Store original mousePressEvent and override
        self._original_mouse_press = self.mousePressEvent
        self.mousePressEvent = self.on_card_click

    def set_title(self, title):
        """Set card title."""
        self.title = title
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)

    def set_date(self, date):
        """Set card date."""
        self.date = date
        if hasattr(self, 'date_label'):
            self.date_label.setText(date)
            
    def set_state_path(self, state_path):
        """Set the state path for loading the visualization."""
        self.state_path = state_path

    def on_card_click(self, event):
        """Handle card clicks by finding parent dashboard and signaling."""
        # Find parent dashboard
        parent = self.parent()
        while parent is not None:
            try:
                from app.HDEMGDashboard import HDEMGDashboard
                if isinstance(parent, HDEMGDashboard):
                    # Call dashboard's handler
                    if hasattr(parent, 'on_visualization_card_clicked'):
                        parent.on_visualization_card_clicked(self.card_index)
                    elif hasattr(parent, 'open_visualization'):  # Fallback to existing method
                        parent.open_visualization(self.title)
                    break
                parent = parent.parent()
            except ImportError:
                # If we can't import HDEMGDashboard (likely due to circular imports)
                # Just go up the parent chain
                parent = parent.parent()
        
        # Call original mousePressEvent if it exists
        if hasattr(self, '_original_mouse_press') and callable(self._original_mouse_press):
            self._original_mouse_press(event)
