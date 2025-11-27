from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from core.muAnalysisCore.AnalysisResultsHist import store

from openhdemg.library import basic_mus_properties, compute_thresholds

class MUPropertiesFunc:
    """Motor Unit Properties functionality"""

    def __init__(self):
        # MVC value for calculations
        self.mvc_value = None
        self.results = store
        self.basic = []
        self.over = None

    # MVC value management
    def set_mvc(self, mvc_value):
        """Set the Maximum Voluntary Contraction value for threshold calculations.

        Args:
            mvc_value: QLineEdit widget containing the MVC value input
        """
        self.mvc_value = mvc_value

    # turns mcv input text into a string to be used
    def get_mvc(self):
        """Get the current MVC value as a string from the input widget.

        Returns:
            String representation of the MVC value from the text input
        """
        return str(self.mvc_value.text())

    def convert(self, value):
        """Convert input widget text to usable string format.

        Args:
            value: QLineEdit widget containing text input

        Returns:
            String representation of the widget's text content
        """
        return str(value.text())

    def basic_prop(self, rec, start):
        """Set up for basic property select range functionality
        Param: analysis_plot: centre plot instance, rec: firing_rec input, start: firing_start input, over: dialog instance
        Return: None
        """
        file = FileUploadFunc.file
        if file == None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        if (
            len(self.convert(self.mvc_value)) == 0
            or len(self.convert(rec)) == 0
            or len(self.convert(start)) == 0
        ):
            ErrorDialog("You are missing Inputs", "Error").exec_()
            return
        self.basic = [self.convert(rec), self.convert(start)]
        try:
            self.basic[0] = int(self.basic[0])
            self.basic[1] = int(self.basic[1])
        except:
            ErrorDialog("incorrect input form", "Error").exec_()
            return

        value = float(self.get_mvc())
        exportable_df = basic_mus_properties(
            FileUploadFunc.file,
            n_firings_RecDerec=int(self.basic[0]),
            n_firings_steady=int(self.basic[1]),
            mvc=value,
        )
        self.results.append_analysis_hist(
            "Basic Properties", exportable_df.to_dict("records")
        )

    def compute_thresh(self, event_, type_):
        """
        Validate required inputs and compute thresholds.

        Parameters
        ----------
        event_ : any
            The event data or selection to be used in threshold computation.
        type_ : any
            The type/category selection to be used in threshold computation.

        This function:
        1. Checks if a file has been loaded.
        2. Validates that all required user inputs are provided.
        3. Calls `compute_thresholds` with the validated inputs.
        """
        file = FileUploadFunc.file
        if file == None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        if (
            len(self.convert(self.mvc_value)) == 0
            or len(event_) == 0
            or len(type_) == 0
        ):
            ErrorDialog("You are missing Inputs", "Error").exec_()
            return

        mus_thresholds = compute_thresholds(
            file, event_, type_, mvc=float(self.get_mvc())
        )

        self.results.append_analysis_hist(
            "MUs Thresholds", mus_thresholds.to_dict("records")
        )