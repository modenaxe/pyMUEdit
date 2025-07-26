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


class ResizeFunc:
    """Static interface for resize functionality"""

    @staticmethod
    def get_range(analysis_plot, callback):
        if FileUploadFunc.file is None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        SelectRange(analysis_plot, callback)


class Resize:
    """Class to handle resizing file functionality"""

    def __init__(self, mu, analysis_plot):
        self.mu = mu
        self.analysis_plot = analysis_plot

    def resize(self, x):
        if FileUploadFunc.file == None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return
        SelectRange(self.analysis_plot, self.two_point)

    def two_point(self, x, y):
        self.resize_emgfile(FileUploadFunc.file, x, y)
        self.mu.plot_idr(FileUploadFunc.file, self.analysis_plot)
        self.analysis_plot.revert()

    # AC
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

        # select points
        # Create the object to store the resized emgfile.
        rs_emgfile = copy.deepcopy(emgfile)

        if emgfile["SOURCE"] in ["DEMUSE", "OTB", "CUSTOMCSV", "DELSYS"]:

            # Double check that start_, end_ are within the real range.
            if end_ > emgfile["RAW_SIGNAL"].shape[0]:
                end_ = emgfile["RAW_SIGNAL"].shape[0]

            # Resize the reference signal and identify the first value of the
            # index to resize the mupulses. Then, reset the index.
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
                # Mask the array based on a filter and return the values in an
                # array. However, make sure that all the numbers are int32 to
                # prevent falling to int16 when small sections are resized.
                # This may cause overflow.
                rs_emgfile["MUPULSES"][mu] = rs_emgfile["MUPULSES"][mu].astype(np.int32)

                rs_emgfile["MUPULSES"][mu] = (
                    rs_emgfile["MUPULSES"][mu][
                        (rs_emgfile["MUPULSES"][mu] >= start_)
                        & (rs_emgfile["MUPULSES"][mu] < end_)
                    ]
                    - first_idx
                )

            # Compute SIL or leave original ACCURACY
            if accuracy == "recalculate":
                if rs_emgfile["NUMBER_OF_MUS"] > 0:
                    if not rs_emgfile["IPTS"].empty:
                        # Calculate SIL
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
                # rs_emgfile["ACCURACY"] = rs_emgfile["ACCURACY"]
                pass

            else:
                raise ValueError(
                    f"Accuracy can only be 'recalculate' or 'maintain'. {accuracy} was passed instead."
                )

            FileUploadFunc.file = rs_emgfile

        elif emgfile["SOURCE"] in ["OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"]:
            # Double check that start_, end_ are within the real range.
            if end_ > emgfile["REF_SIGNAL"].shape[0]:
                end_ = emgfile["REF_SIGNAL"].shape[0]

            rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].loc[start_:end_]
            rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].reset_index(drop=True)
            FileUploadFunc.file = rs_emgfile

        else:
            raise ValueError("\nFile source not recognised\n")
