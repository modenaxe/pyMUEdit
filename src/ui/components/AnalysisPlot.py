from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QStyle,
    QMainWindow,
    QComboBox,
)
from ui.components.AnalysisText import AnalysisText
from ui.components.AnalysisButton import AnalysisButton

"""
If there's no figure/file, a title appears prompting the user to load a file
"""
class AnalysisPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # setting up toggle button  
        self.plot = None
        self.toggle_btn = AnalysisButton("Revert", lambda: self.revert(), parent=self)
        self.toggle_btn.set_width(100)
        self.toggle_btn.hide()
        self.layout.addWidget(self.toggle_btn)

        # setting up the prompt and future plots 
        self.canvas = None
        self.load_file_prompt()

    # loads the prompt into canvas
    def load_file_prompt(self):
        self.canvas = AnalysisText.create_prompt("Press Load File to View Data")
        self.layout.addWidget(self.canvas)

    # removes the canvas, or the last thing in the widget 
    def remove_canvas(self):
        c = self.layout.itemAt(self.layout.count() - 1)
        cw = c.widget()
        self.layout.removeWidget(cw)
        cw.setParent(None)

    # removes the current plot and returns it to the 'original' 
    # it's what happens when you press the toggle button
    def revert(self):
        # removing current 
        self.remove_canvas()

        # restoring old one
        self.layout.addWidget(self.canvas)

        self.toggle_btn.hide()

    ############### DISPLAY FIG/PLOT ##############
    # when calling display_fig or dislay_plot, make sure you first turn it into 
    # a SaveablePlot(fig), then pass it into the fig param


    # used specifically to display figures, and nothing else 
    # e.g. plot_idr or plot_refsig
    def display_fig(self, fig=None):
        # removing current
        self.remove_canvas()

        # generating the new one 
        self.canvas = fig 
        self.layout.addWidget(self.canvas)

        self.toggle_btn.hide()

    # used for displaying plots, not figures
    # in this case, plots refer to anything that isn't the usual MU signal graph
    def display_plot(self, plot=None):
        # removing current 
        self.remove_canvas()

        self.plot = plot 
        self.layout.addWidget(self.plot)

        self.toggle_btn.show()

