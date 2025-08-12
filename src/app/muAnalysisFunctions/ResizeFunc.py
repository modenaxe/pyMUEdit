import sys
import numpy as np
import matplotlib.pyplot as plt
import os
import copy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from core.muAnalysisCore.SelectRange import SelectRange
from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from PyQt5.QtCore import Qt


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
        if FileUploadFunc.file == None:
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
        self.resize_emgfile(FileUploadFunc.file, x, y)
        self.mu.plot_idr(FileUploadFunc.file, self.analysis_plot)
        self.analysis_plot.revert()

    def resize_emgfile(
        self,
        emgfile,
        start_,
        end_,
        area=None,
        how="ref_signal",
        accuracy="recalculate",
        ignore_negative_ipts=False,
    ):
        """Resize EMG file data to specified sample range (from openHDEMG).

        Args:
            emgfile: EMG file dictionary containing all signal data
            start_: Starting sample index for resized data
            end_: Ending sample index for resized data
            area: Area parameter (not used in current implementation)
            how: Method for resizing ("ref_signal" - default)
            accuracy: How to handle accuracy recalculation ("recalculate" or "maintain")
            ignore_negative_ipts: Whether to ignore negative IPTS values in accuracy calculation

        Trims all data arrays (RAW_SIGNAL, REF_SIGNAL, IPTS, etc.) to the specified range,
        adjusts MUPULSES indices accordingly, and optionally recalculates accuracy metrics.
        Updates the global FileUploadFunc.file with the resized data.
        """
        rs_emgfile = copy.deepcopy(emgfile)
        if emgfile["SOURCE"] in ["DEMUSE", "OTB", "CUSTOMCSV", "DELSYS"]:
            if end_ > emgfile["RAW_SIGNAL"].shape[0]:
                end_ = emgfile["RAW_SIGNAL"].shape[0]
            rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].loc[start_:end_]
            rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].reset_index(drop=True)
            rs_emgfile["RAW_SIGNAL"] = rs_emgfile["RAW_SIGNAL"].loc[start_:end_]
            first_idx = rs_emgfile["RAW_SIGNAL"].index[0]
            rs_emgfile["RAW_SIGNAL"] = rs_emgfile["RAW_SIGNAL"].reset_index(drop=True)
            rs_emgfile["IPTS"] = (
                rs_emgfile["IPTS"].loc[start_:end_].reset_index(drop=True)
            )
            rs_emgfile["EMG_LENGTH"] = int(len(rs_emgfile["RAW_SIGNAL"].index))
            rs_emgfile["BINARY_MUS_FIRING"] = (
                rs_emgfile["BINARY_MUS_FIRING"].loc[start_:end_].reset_index(drop=True)
            )
            for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
                rs_emgfile["MUPULSES"][mu] = rs_emgfile["MUPULSES"][mu].astype(np.int32)
                rs_emgfile["MUPULSES"][mu] = (
                    rs_emgfile["MUPULSES"][mu][
                        (rs_emgfile["MUPULSES"][mu] >= start_)
                        & (rs_emgfile["MUPULSES"][mu] < end_)
                    ]
                    - first_idx
                )
            if accuracy == "recalculate":
                if rs_emgfile["NUMBER_OF_MUS"] > 0:
                    if not rs_emgfile["IPTS"].empty:
                        for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
                            func = CommonOpenFunc()
                            res = func.compute_sil(
                                ipts=rs_emgfile["IPTS"][mu],
                                mupulses=rs_emgfile["MUPULSES"][mu],
                                ignore_negative_ipts=ignore_negative_ipts,
                            )
                            rs_emgfile["ACCURACY"].iloc[mu] = res
                    else:
                        raise ValueError(
                            "Impossible to calculate ACCURACY (SIL). IPTS not "
                            + "found. If IPTS is not present or empty, set "
                            + "accuracy='maintain'"
                        )
            elif accuracy == "maintain":
                pass
            else:
                raise ValueError(
                    f"Accuracy can only be 'recalculate' or 'maintain'. {accuracy} was passed instead."
                )
            FileUploadFunc.file = rs_emgfile
        elif emgfile["SOURCE"] in ["OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"]:
            if end_ > emgfile["REF_SIGNAL"].shape[0]:
                end_ = emgfile["REF_SIGNAL"].shape[0]
            rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].loc[start_:end_]
            rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].reset_index(drop=True)
            FileUploadFunc.file = rs_emgfile
        else:
            raise ValueError("\nFile source not recognised\n")
