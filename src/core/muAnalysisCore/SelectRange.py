import sys
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.components.SaveablePlot import SaveablePlot
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from PyQt5.QtCore import Qt

class SelectRange:

    """Class to handle selecting range of points with clamping mechanism"""

    def __init__(self, analysis_plot, func):
        self.drag = True
        self.func = func
        self.analysis_plot = analysis_plot
        self.ax = None
        self.canvas = None
        self.shade_one = None
        self.shade_two = None
        self.set_up_plot()
        val = self.ax.xaxis.get_view_interval()
        self.max = val[1]
        self.line = [self.ax.axvline(x=0, color='r', picker=1), self.ax.axvline(x=self.max, color='r', picker=1)]
        self.ax.axvspan(self.max, self.max, alpha=0.1, color='red')
        self.canvas.mpl_connect('key_press_event', lambda event: self.on_press(event))
        self.canvas.mpl_connect('pick_event', lambda event: self.click_on_line(event))

        analysis_plot.display_plot(self.canvas)

    # after pressing enter the graph returns to original view
    def on_press(self, event):
        if event.key == 'enter':
            self.func(round(self.line[0].get_xdata()[0]),round(self.line[1].get_xdata()[0]))

    # creates intervative canvas for the centre panel
    def set_up_plot(self):
        emgfile = FileUploadFunc.file
        plt.close()
        data_to_plot = emgfile["REF_SIGNAL"][0]
        fig, ax = plt.subplots()
        ax.plot(data_to_plot)
        ax.set_xlabel("Samples")
        plt.rcParams["axes.titlesize"] = 8
        title = 'Click red lines to select/release range, drag to adjust. Press enter once satisfied'
        ax.set_title(title, wrap=True)
        self.canvas = FigureCanvas(fig)
        self.ax = ax
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()

    # after a line is clicked it can be moved until clicked again
    def click_on_line(self, event):
        if event.artist in self.line:
            x = self.line.index(event.artist)
            if self.drag:
                follow = self.canvas.mpl_connect("motion_notify_event", lambda event: self.follow_mouse(event, x))
                release = self.canvas.mpl_connect("button_press_event", lambda event: self.release_on_click(follow, release))
                self.drag = False
            else:
                self.drag = True

    # following moving line
    def follow_mouse(self, event, index):
        if event.xdata:
            if (index == 0):
                self.line_one(event)
            else:
                self.line_two(event)
            self.canvas.draw()

    # prevents starting line from going past axes or past ending line and shades non selected region 
    def line_one(self, event):
        if event.xdata >= 0 and event.xdata <= self.line[1].get_xdata()[0]:
            self.line[0].set_xdata([event.xdata, event.xdata])
            if self.shade_one:
                self.shade_one.remove()
            self.shade_one = self.ax.axvspan(0, event.xdata, alpha=0.1, color='red')

    # prevents ending line from going past axes or past starting line and shades non selected region
    def line_two(self, event):
        if event.xdata <= self.max and event.xdata >= self.line[0].get_xdata()[0]:
            self.line[1].set_xdata([event.xdata, event.xdata])
            if self.shade_two:
                self.shade_two.remove()
            self.shade_two = self.ax.axvspan(event.xdata, self.max, alpha=0.1, color='red')

    # line is dropped on click
    def release_on_click(self, follow, release):
        self.canvas.mpl_disconnect(follow)
        self.canvas.mpl_disconnect(release)

