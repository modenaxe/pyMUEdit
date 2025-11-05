import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc

class SelectRange:

    """Class to handle selecting range of points with clamping mechanism"""

    def __init__(self, analysis_plot, func, single):
        """Initialises class instance
        Params: analysis_plot: centre plot instance, func: function for points to be passed into, single: number of points required
        Returns: None
        """
        if FileUploadFunc.file is None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

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
        self.line = [self.ax.axvline(x=0, color='r', picker=5, linewidth=1), self.ax.axvline(x=self.max, color='r', picker=5, linewidth=1)]
        if single:
            self.line[1].set_picker(False)
            self.line[1].set_linewidth(0)
            self.ax.axvspan(self.max, self.max, alpha=0, color='red')
        else:
            self.ax.axvspan(self.max, self.max, alpha=0.1, color='red')
        self.canvas.mpl_connect('key_press_event', lambda event: self.on_press(event))
        self.canvas.mpl_connect('pick_event', lambda event: self.click_on_line(event))

        analysis_plot.display_plot(self.canvas)
        self.canvas.setFocus()

    def on_press(self, event):
        """After pressing enter the graph returns to original view and function is carried out with line x coords
        Params: event: type of key pressed
        Returns: None
        """
        if event.key == 'enter':
            try:
                self.func(round(self.line[0].get_xdata()[0]),round(self.line[1].get_xdata()[0]))
            except:
                ErrorDialog("Bad range of values", "Error").exec_()
                self.analysis_plot.revert()
                return
            else:
                self.analysis_plot.revert()

    def set_up_plot(self):
        """Creates intervative canvas for the centre panel
        Params: None
        Returns: None
        """
        emgfile = FileUploadFunc.file
        plt.close()
        data_to_plot = emgfile["REF_SIGNAL"][0]
        fig, ax = plt.subplots()
        ax.plot(data_to_plot, color='#555555')
        ax.set_xlabel("Samples")
        plt.rcParams["axes.titlesize"] = 8
        title = 'Click red lines to select/release range, drag to adjust. Press enter once satisfied'
        ax.set_title(title, wrap=True)
        self.canvas = FigureCanvas(fig)
        self.ax = ax

    def click_on_line(self, event):
        """After a line is clicked it can't be moved until clicked again
        Params: event: type of object that has been 'picked' on centre graph
        Returns: None
        """
        if event.artist in self.line:
            x = self.line.index(event.artist)
            if self.drag:
                follow = self.canvas.mpl_connect("motion_notify_event", lambda event: self.follow_mouse(event, x))
                release = self.canvas.mpl_connect("button_press_event", lambda event: self.release_on_click(follow, release))
                self.drag = False
            else:
                self.drag = True

    def follow_mouse(self, event, index):
        """Following moving line with mouse
        Params: event: data of follow mouse object, index: whether start or end line is being followed
        Returns: None
        """
        if event.xdata:
            if (index == 0):
                self.line_one(event)
            else:
                self.line_two(event)
            self.canvas.draw()

    def line_one(self, event):
        """Prevents starting line from going past axes or past ending line and shades non selected region
        Params: event: data of follow mouse object
        Returns: None
        """
        if event.xdata >= 0 and event.xdata <= self.line[1].get_xdata()[0]:
            self.line[0].set_xdata([event.xdata, event.xdata])
            if self.shade_one:
                self.shade_one.remove()
            self.shade_one = self.ax.axvspan(0, event.xdata, alpha=0.1, color='red')

    def line_two(self, event):
        """Prevents ending line from going past axes or past ending line and shades non selected region
        Params: event: data of follow mouse object
        Returns: None
        """
        if event.xdata <= self.max and event.xdata >= self.line[0].get_xdata()[0]:
            self.line[1].set_xdata([event.xdata, event.xdata])
            if self.shade_two:
                self.shade_two.remove()
            self.shade_two = self.ax.axvspan(event.xdata, self.max, alpha=0.1, color='red')

    def release_on_click(self, follow, release):
        """Line is dropped on click 
        Params: follow: drag event to be disconnected, release: drop event to be disconnected
        Returns: None
        """
        self.canvas.mpl_disconnect(follow)
        self.canvas.mpl_disconnect(release)
