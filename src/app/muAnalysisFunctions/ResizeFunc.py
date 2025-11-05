from core.muAnalysisCore.SelectRange import SelectRange
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog

from openhdemg.library import resize_emgfile

class Resize:
    """Class to handle resizing EMG file functionality.

    Provides functionality to resize (trim) EMG data to a specified time range
    by allowing user to select start and end points on the analysis plot.
    """

    def __init__(self, mu, analysis_plot):
        """Initialize the Resize class instance.

        Args:
            mu: Instance of MU analysis functionality handler
            analysis_plot: Centre plot instance for range selection visualization
        """
        self.mu = mu
        self.analysis_plot = analysis_plot

    def resize(self):
        """Set up screen for selecting start/end range of resize operation.

        Initiates the range selection interface that allows user to click
        two points on the plot to define the resize boundaries.
        Shows error if no file is loaded.
        """
        if not self.mu.data_loaded():
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        SelectRange(self.analysis_plot, self.two_point, False)

    def two_point(self, x, y):
        """Callback function for range selection completion.

        Args:
            x: Start point (sample index) selected by user
            y: End point (sample index) selected by user

        Performs the actual resize operation, updates the plot display,
        and reverts the plot to normal interaction mode.
        """
        FileUploadFunc.file, start_, end_ = resize_emgfile(FileUploadFunc.file, area=[x, y])
        self.mu.plot_idr(FileUploadFunc.file, self.analysis_plot)
        self.analysis_plot.revert()
