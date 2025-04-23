from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QWidget, QLabel, QApplication, 
                          QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
import os

from .CleanTheme import CleanTheme


class VisualizationCard(QFrame):
    """
    An interactive card component for visualization items with enhanced styling 
    and support for visualization types.
    """
    # Signal emitted when the card is clicked
    clicked = pyqtSignal(object)  # Will emit the visualization data when clicked
    
    def __init__(self, title=None, icon=None, date=None, viz_type="hdemg", viz_data=None, parent=None):
        super().__init__(parent)
        
        # Store associated data
        self.viz_data = viz_data if viz_data is not None else title  # Use title as fallback
        self.viz_type = viz_type.lower() if viz_type else "hdemg"

        # Set up styling for the entire card
        self.setObjectName("visualizationCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumSize(150, 200)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Apply shadow effect for modern look
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Apply styling with type-specific header colors
        header_color = self.get_color_for_type(self.viz_type)
        self.setStyleSheet(
            f"""
            QFrame#visualizationCard {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            QLabel {{
                background-color: transparent;
            }}
            QFrame#headerStrip {{
                background-color: {header_color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
            QFrame#iconArea {{
                background-color: #f5f5f5;
                border-radius: 6px;
                border: none;
            }}
        """
        )

        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Add colored header strip
        self.header_strip = QFrame()
        self.header_strip.setObjectName("headerStrip")
        self.header_strip.setFixedHeight(8)
        self.layout.addWidget(self.header_strip)
        
        # Create content container
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(8)

        # Create the icon area
        self.icon_area = QFrame()
        self.icon_area.setObjectName("iconArea")
        self.icon_area.setMinimumHeight(100)
        self.icon_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Layout for the icon area to center the icon
        icon_layout = QVBoxLayout(self.icon_area)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Get icon based on visualization type if not explicitly provided
        if not icon:
            icon = self.get_icon_for_type(self.viz_type)

        # Add icon if provided
        if icon:
            icon_path = icon
            if isinstance(icon, str) and not os.path.exists(icon) and not icon.startswith("/"):
                # Try to find in public folder
                icon_path = os.path.join("public", f"{icon}.svg")
                if not os.path.exists(icon_path):
                    icon_path = None

            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Handle different icon types
            if isinstance(icon, QIcon):
                pixmap = icon.pixmap(QSize(48, 48))
                icon_label.setPixmap(pixmap)
                icon_layout.addWidget(icon_label)
            elif isinstance(icon_path, str) and os.path.exists(icon_path):
                if icon_path.endswith(".svg"):
                    # Use QSvgWidget for SVG files
                    svg_widget = QSvgWidget(icon_path)
                    svg_widget.setFixedSize(48, 48)
                    icon_layout.addWidget(svg_widget)
                else:
                    icon_label.setPixmap(
                        QPixmap(icon_path).scaled(
                            48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                        )
                    )
                    icon_layout.addWidget(icon_label)
            elif isinstance(icon, int) or (hasattr(icon, "__int__") and not isinstance(icon, bool)):
                std_icon = QApplication.style().standardIcon(icon)
                pixmap = std_icon.pixmap(QSize(48, 48))
                icon_label.setPixmap(pixmap)
                icon_layout.addWidget(icon_label)
            else:
                # Default icon based on visualization type
                icon_text = self.get_emoji_for_type(self.viz_type)
                icon_label.setText(icon_text)
                icon_label.setStyleSheet("font-size: 32px;")
                icon_layout.addWidget(icon_label)
        else:
            # Default icon based on visualization type
            default_icon = QLabel(self.get_emoji_for_type(self.viz_type))
            default_icon.setStyleSheet("font-size: 32px;")
            default_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(default_icon)

        # Add icon area to content layout
        content_layout.addWidget(self.icon_area)

        # Add title if provided
        self.title_label = None
        if title:
            self.title_label = QLabel(title)
            self.title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.title_label.setWordWrap(True)
            content_layout.addWidget(self.title_label)

        # Add date if provided
        self.date_label = None
        if date:
            self.date_label = QLabel(date)
            self.date_label.setFont(QFont("Segoe UI", 9))
            self.date_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
            self.date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            content_layout.addWidget(self.date_label)

        # Add content container to main layout
        self.layout.addWidget(content_container)

        # Make card interactive
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event):
        """Handle mouse press events to emit clicked signal."""
        # Emit the visualization data when clicked
        self.clicked.emit(self.viz_data)
        super().mousePressEvent(event)
        
    def get_color_for_type(self, viz_type):
        """Return appropriate color based on visualization type."""
        type_map = {
            "hdemg": "#1a73e8",   # Blue
            "neuro": "#7cb342",   # Green
            "emg": "#e91e63",     # Pink
            "eeg": "#9c27b0",     # Purple
        }
        return type_map.get(viz_type.lower(), "#607d8b")  # Default to blue-gray
    
    def get_icon_for_type(self, viz_type):
        """Return appropriate icon path based on visualization type."""
        # You would replace these with actual paths to your icon files
        icon_dir = os.path.join("public", "icons")
        
        type_map = {
            "hdemg": os.path.join(icon_dir, "hdemg_icon.svg"),
            "neuro": os.path.join(icon_dir, "neuro_icon.svg"),
            "emg": os.path.join(icon_dir, "emg_icon.svg"),
            "eeg": os.path.join(icon_dir, "eeg_icon.svg"),
        }
        
        icon_path = type_map.get(viz_type.lower(), os.path.join(icon_dir, "visualization_icon.svg"))
        
        if os.path.exists(icon_path):
            return icon_path
        else:
            return None  # Will use emoji fallback
            
    def get_emoji_for_type(self, viz_type):
        """Return appropriate emoji based on visualization type."""
        type_map = {
            "hdemg": "📊",  # Chart
            "neuro": "🧠",  # Brain
            "emg": "💪",    # Muscle
            "eeg": "⚡",     # Lightning
        }
        return type_map.get(viz_type.lower(), "📈")  # Default to chart
        
    def set_visualization_data(self, viz_data):
        """Set or update the visualization data associated with this card."""
        self.viz_data = viz_data
        
        # Update title and date if provided in viz_data
        if viz_data:
            if "title" in viz_data and self.title_label:
                self.title_label.setText(viz_data["title"])
                
            if "date" in viz_data and self.date_label:
                self.date_label.setText(viz_data["date"])
                
            if "type" in viz_data:
                self.viz_type = viz_data["type"]
                # Update header color
                header_color = self.get_color_for_type(self.viz_type)
                self.header_strip.setStyleSheet(f"background-color: {header_color};")