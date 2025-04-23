import os
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal


class CleanTheme:
    """Color and style constants for a clean, modern UI."""
    # Basic colors
    BG_MAIN = "#f5f5f5"
    BG_CARD = "#ffffff"
    BORDER = "#e0e0e0"
    
    # Text colors
    TEXT_PRIMARY = "#333333"
    TEXT_SECONDARY = "#6c757d"
    
    # Accent colors
    ACCENT_PRIMARY = "#1a73e8"  # Blue
    ACCENT_SUCCESS = "#0f9d58"  # Green
    ACCENT_WARNING = "#f4b400"  # Yellow
    ACCENT_DANGER = "#db4437"   # Red
    
    # Card types
    CARD_HDEMG = "#1a73e8"   # Blue
    CARD_NEURO = "#7cb342"   # Green
    CARD_EMG = "#e91e63"     # Pink
    CARD_EEG = "#9c27b0"     # Purple
    CARD_DEFAULT = "#607d8b" # Blue-gray


class VisualizationCard(QWidget):
    """
    A modern card component to display visualizations with a colored header,
    title, date, and icon.
    """
    # Signal emitted when the card is clicked
    clicked = pyqtSignal()
    
    def __init__(self, title="", date="", icon=None, viz_type="hdemg", parent=None):
        super().__init__(parent)
        self.setObjectName("visualizationCard")
        self.setMinimumSize(280, 180)
        self.setMaximumWidth(350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Store properties
        self.title = title
        self.date = date
        self.icon_path = icon
        self.viz_type = viz_type
        
        # Set up styling
        self.setup_styling()
        
        # Create layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create card frame with shadow
        self.card = QFrame(self)
        self.card.setObjectName("cardFrame")
        self.card.setStyleSheet("""
            #cardFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.card.setGraphicsEffect(shadow)
        
        # Card layout
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        # Create colored header with the visualization type's associated color
        color = self.get_color_for_type(viz_type)
        self.header = QFrame()
        self.header.setObjectName("cardHeader")
        self.header.setStyleSheet(f"""
            #cardHeader {{
                background-color: {color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-height: 12px;
            }}
        """)
        self.header.setMinimumHeight(8)
        self.header.setMaximumHeight(8)
        card_layout.addWidget(self.header)
        
        # Content container
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(8)
        
        # Title and date
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        
        self.date_label = QLabel(date)
        self.date_label.setObjectName("cardDate")
        self.date_label.setFont(QFont("Segoe UI", 9))
        self.date_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.date_label)
        content_layout.addStretch(1)
        
        # Footer with icon
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 10, 0, 0)
        
        icon_label = QLabel()
        
        # Choose appropriate icon based on visualization type
        icon_path = self.get_icon_for_type(viz_type)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(QSize(20, 20), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Use a fallback
            icon_label.setText("📊")
            icon_label.setFont(QFont("Segoe UI", 12))
        
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        footer_layout.addWidget(icon_label)
        footer_layout.addStretch(1)
        
        content_layout.addWidget(footer)
        card_layout.addWidget(content)
        
        # Add the card to the main layout
        self.main_layout.addWidget(self.card)
    
    def setup_styling(self):
        """Apply style to the card widget."""
        self.setStyleSheet("""
            QWidget#visualizationCard {
                background-color: transparent;
            }
            QWidget#visualizationCard:hover {
                background-color: rgba(0, 0, 0, 0.03);
            }
        """)
    
    def get_color_for_type(self, viz_type):
        """Return appropriate color based on visualization type."""
        type_map = {
            "hdemg": CleanTheme.CARD_HDEMG,
            "neuro": CleanTheme.CARD_NEURO,
            "emg": CleanTheme.CARD_EMG,
            "eeg": CleanTheme.CARD_EEG,
        }
        return type_map.get(viz_type.lower(), CleanTheme.CARD_DEFAULT)
    
    def get_icon_for_type(self, viz_type):
        """Return appropriate icon path based on visualization type."""
        # You would replace these with actual paths to your icon files
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        os.makedirs(icon_dir, exist_ok=True)
        
        type_map = {
            "hdemg": os.path.join(icon_dir, "hdemg_icon.svg"),
            "neuro": os.path.join(icon_dir, "neuro_icon.svg"),
            "emg": os.path.join(icon_dir, "emg_icon.svg"),
            "eeg": os.path.join(icon_dir, "eeg_icon.svg"),
        }
        
        # In this implementation, we'll just return a string path
        # even if the file doesn't exist - we handle the fallback in the constructor
        return type_map.get(viz_type.lower(), os.path.join(icon_dir, "visualization_icon.svg"))
    
    def mousePressEvent(self, event):
        """Handle mouse press events to emit clicked signal."""
        self.clicked.emit()
        super().mousePressEvent(event)


class CleanCard(QFrame):
    """A clean, styled card container with shadow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cleanCard")
        self.setStyleSheet(f"""
            #cleanCard {{
                background-color: {CleanTheme.BG_CARD};
                border-radius: 8px;
                border: 1px solid {CleanTheme.BORDER};
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)