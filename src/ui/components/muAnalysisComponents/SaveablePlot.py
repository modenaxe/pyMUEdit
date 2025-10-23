import sys

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout,
                             QLabel, QPushButton, QVBoxLayout, QWidget)

# legacy code
class SaveablePlot(QWidget):

    """
    A widget that wraps a matplotlib figure with a floating save button in the top right corner.
    """

    def __init__(self, figure=None, parent=None):
        super().__init__(parent)

        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Create canvas container with relative positioning for the save button
        self.canvas_container = QFrame()
        self.canvas_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
            }
        """)

        # Use a layout that allows absolute positioning
        self.canvas_container.setLayout(QVBoxLayout())
        self.canvas_container.layout().setContentsMargins(0, 0, 0, 0)

        # Set the figure
        if figure is not None:
            self.set_figure(figure)
        else:
            # Create a placeholder
            self.canvas = None
            placeholder = QLabel("No plot data available")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet(
                "color: #6c757d; font-size: 14px; padding: 40px;")
            self.canvas_container.layout().addWidget(placeholder)

        self.layout.addWidget(self.canvas_container)

    def _get_save_icon(self):
        """Get a save icon using standard system icons."""
        try:
            # Try to get a standard save icon
            return QApplication.style().standardIcon(
                QApplication.style().SP_DialogSaveButton)
        except BaseException:
            # Fallback to text if icon not available
            return QIcon()

    def set_figure(self, figure):
        """Set the matplotlib figure to display."""
        # Clear existing canvas
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.canvas_container.layout().removeWidget(self.canvas)
            self.canvas.deleteLater()

        # Create new canvas
        self.canvas = FigureCanvas(figure)
        self.canvas_container.layout().addWidget(self.canvas)

        # Update the figure reference
        self.figure = figure

        # Create and position the save button
        self._create_save_button()

    def _create_save_button(self):
        """Create a floating save button positioned in the top right corner."""
        # Create save button
        self.save_button = QPushButton()
        self.save_button.setIcon(self._get_save_icon())
        self.save_button.setIconSize(QSize(18, 18))
        self.save_button.setFixedSize(36, 36)
        self.save_button.setToolTip("Save plot as image")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 1.0);
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: rgba(222, 226, 230, 1.0);
            }
        """)
        self.save_button.clicked.connect(self.save_plot)

        # Position the button in the top right corner
        self.save_button.setParent(self.canvas_container)
        self.save_button.raise_()  # Bring to front

        # Set position (top right corner with small margin)
        self.save_button.move(self.canvas_container.width() - 42, 8)

        # Make sure button stays visible when canvas is resized
        self.canvas_container.resizeEvent = self._on_canvas_resize

    def _on_canvas_resize(self, event):
        """Handle canvas resize to keep save button in correct position."""
        if hasattr(self, 'save_button'):
            self.save_button.move(self.canvas_container.width() - 42, 8)
        event.accept()

    def save_plot(self):
        """Open file dialog to save the plot as an image."""
        if not hasattr(self, 'figure') or self.figure is None:
            return

        # Open file dialog
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "Save Plot As",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*.*)"
        )

        if file_path:
            try:
                # Save the figure
                self.figure.savefig(
                    file_path,
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='white')
                print(f"Plot saved successfully to: {file_path}")
            except Exception as e:
                print(f"Error saving plot: {e}")
                # Could add a proper error dialog here
