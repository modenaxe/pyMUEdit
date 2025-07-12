import sys
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.components.SaveablePlot import SaveablePlot
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc

class SelectRange:

    def __init__(self, analysis_plot):
        emgfile = FileUploadFunc.file
        self.drag = True
        self.analysis_plot = analysis_plot
        plt.close()
        data_to_plot = emgfile["REF_SIGNAL"][0]
        fig, ax = plt.subplots()
        self.ax = ax
        ax.plot(data_to_plot)
        ax.set_xlabel("Samples")
        ax.set_ylabel('Reference signal')
        ax.set_title('Click start and end range')
        # fig.set_figheight(5)
        # fig.set_figwidth(5)
        self.s = None
        val = ax.xaxis.get_view_interval()
        upper = val[1] - abs(val[0])
        self.canvas = FigureCanvas(fig)
        self.line = [ax.axvline(x=0, color='r', picker=1), ax.axvline(x=upper, color='r', picker=1)]
        self.canvas.mpl_connect('pick_event', lambda event: self.clickOnLine(event))
        analysis_plot.display_plot(self.canvas)

    def clickOnLine(self, event):
        if event.artist in self.line:
            x = self.line.index(event.artist)
            if self.drag:
                follow = self.canvas.mpl_connect("motion_notify_event", lambda event: self.followmouse(event, x))
                release = self.canvas.mpl_connect("button_press_event", lambda event: self.releaseonclick(follow, release))
                self.drag = False
            else:
                self.drag = True

    def followmouse(self, event, index):
        if event.xdata:
            if (index == 0 and event.xdata <= self.line[1].get_xdata()[0]) or (index == 1 and event.xdata >= self.line[0].get_xdata()[0]):
                self.line[index].set_xdata([event.xdata, event.xdata])
                # max = ax.xaxis.get_view_interval()
                if self.s:
                    self.s.remove()
                self.s = self.ax.axvspan(0, event.xdata, alpha=0.1, color='red')
                self.canvas.draw()


    def releaseonclick(self, follow, release):
        print(self.line[0].get_xdata()[0])
        self.canvas.mpl_disconnect(follow)
        self.canvas.mpl_disconnect(release)

