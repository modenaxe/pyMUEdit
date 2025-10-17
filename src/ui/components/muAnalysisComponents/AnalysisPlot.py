from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
                             QLabel, QMainWindow, QPushButton, QStyle,
                             QVBoxLayout, QWidget)

from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton


class AnalysisPlot(QWidget):

    """Widget that manages the revert and resize button, and what's displayed
    in the centre.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Setting up the buttons
        self.resize = None
        self.toggle_btn = GeneralButton(
            "Revert", lambda: self.revert(), parent=self)
        self.toggle_btn.set_width(100)
        self.toggle_btn.hide()
        self.layout.addWidget(self.toggle_btn)

        # Setting up the prompt and the canvas
        self.plot = None
        self.canvas = None
        self.load_file_prompt()

    def load_file_prompt(self):
        """Loads in the 'upload file' prompt onto the canvas
        Params: None
        Returns: None
        """
        self.canvas = AnalysisText.create_prompt(
            "Select a file to begin the analysis")
        self.layout.addWidget(self.canvas, alignment=Qt.AlignCenter)

    def set_resize(self, button):
        """Stores the instance of the resize button
        Params:
            - button: instance of a button
        Returns: None
        """
        self.resize = button

    def focus(self):
        """Focuses the canvas so that it can be interacted with
        Params: None
        Returns: None
        """
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.canvas.setFocus()

    def remove_canvas(self):
        """Removes the current figure/plot in the canvas
        Params: None
        Returns: None
        """
        if (self.layout.count() <= 1):
            return

        # Removing last widget in layout, which should always be the canvas
        c = self.layout.itemAt(self.layout.count() - 1)
        cw = c.widget()
        self.layout.removeWidget(cw)
        cw.setParent(None)

    def revert(self):
        """Reverts the current plot to the last figure displayed
        Params: None
        Returns: None
        """
        self.remove_canvas()

        # Restoring old canvas
        self.layout.addWidget(self.canvas)

        self.toggle_btn.hide()
        self.resize.show()

    def display_fig(self, fig=None):
        """Displays a figure in the canvas. A figure is defined as primary results.
        Revert will not appear above a recently displayed fig. Revert, when displayed,
        will restore the canvas to the most recently generated figure.
        Params:
            - fig: in the form of a SaveablePlot()
        Returns: None
        """
        self.remove_canvas()

        # Adding the figure to the canvas
        self.canvas = fig
        self.layout.addWidget(self.canvas)
        self.resize.show()

        self.toggle_btn.hide()

    def display_plot(self, plot=None):
        """Displays a plot in the canvas. A plot is defined as secondary results.
        For example, SelectRange or remove_offset. When a figure is displayed, the
        revert button appears above the canvas.
        Params:
            - plot: in the form of a SaveablePlot()
        Returns: None
        """
        self.remove_canvas()

        self.plot = plot
        self.layout.addWidget(self.plot)

        self.focus()

        self.resize.hide()
        self.toggle_btn.show()
