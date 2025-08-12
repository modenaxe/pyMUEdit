import sys
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
)
from scipy.io import loadmat
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
import warnings
import os
import math
import copy
import itertools
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.components.SaveablePlot import SaveablePlot
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
from core.muAnalysisCore.SelectRange import SelectRange
from core.muAnalysisCore.AnalysisResultsHist import store


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

    def basic_prop(self, analysis_plot, rec, start, over):
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
        over.hide()
        self.over = over
        self.analysis_plot = analysis_plot
        SelectRange(analysis_plot, self.two_point, False)

    def compute_thresh(self, event_, type_):
        """Compute motor unit recruitment/derecruitment thresholds.

        Args:
            event_: Event type string for threshold calculation (e.g., 'rt_dert', 'rt', 'dert')
            type_: Type of threshold calculation ('abs_rel', 'abs', 'rel')

        Validates inputs and calls compute_thresholds with the loaded EMG file.
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
        self.compute_thresholds(
            FileUploadFunc.file, event_, type_, mvc=float(self.get_mvc())
        )

    def two_point(self, x, y):
        """Function to be passed for select range and reverts plot with basic properties
        Params: x,y: coords from select range
        Returns: None
        """
        value = int(self.get_mvc())
        self.basic_mus_properties(
            FileUploadFunc.file,
            n_firings_RecDerec=int(self.basic[0]),
            n_firings_steady=int(self.basic[1]),
            start_steady=x,
            end_steady=y,
            mvc=value,
        )
        self.over.close()

    def basic_mus_properties(
        self,
        emgfile,
        n_firings_rt_dert=1,
        n_firings_RecDerec=4,
        n_firings_steady=10,
        start_steady=-1,
        end_steady=-1,
        idr_range=None,
        accuracy="default",
        ignore_negative_ipts=False,
        constrain_pulses=[True, 3],
        mvc=0,
    ):
        """from openHDEMG to get basic properties but edited to be sent to results table with dataframes
        Params (relevant for us): emgfile, n_firings_RecDerec: user input, n_firings_steady: user input, start_steady: from select range, end_steady: from select range
        Returns: Dataframe
        """
        exportable_df = []
        exportable_df.append({"MVC": mvc})
        exportable_df = pd.DataFrame(exportable_df)
        toappend = []
        for i in range(emgfile["NUMBER_OF_MUS"]):
            toappend.append({"MU_number": i})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)
        if accuracy == "default":
            toappend = emgfile["ACCURACY"]
            toappend.columns = ["Accuracy"]
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
            avg_accuracy = exportable_df["Accuracy"].mean()
            toappend = pd.DataFrame([{"avg_Accuracy": avg_accuracy}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
        elif accuracy == "SIL":
            toappend = []
            for mu in range(emgfile["NUMBER_OF_MUS"]):
                sil = compute_sil(
                    ipts=emgfile["IPTS"][mu],
                    mupulses=emgfile["MUPULSES"][mu],
                    ignore_negative_ipts=ignore_negative_ipts,
                )
                toappend.append({"SIL": sil})
            toappend = pd.DataFrame(toappend)
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
            avg_sil = exportable_df["SIL"].mean()
            toappend = pd.DataFrame([{"avg_SIL": avg_sil}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
        elif accuracy == "PNR":
            toappend = []
            for mu in range(emgfile["NUMBER_OF_MUS"]):
                pnr = compute_pnr(
                    ipts=emgfile["IPTS"][mu],
                    mupulses=emgfile["MUPULSES"][mu],
                    fsamp=emgfile["FSAMP"],
                    constrain_pulses=constrain_pulses,
                )
                toappend.append({"PNR": pnr})
            toappend = pd.DataFrame(toappend)
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
            avg_pnr = exportable_df["PNR"].mean()
            toappend = pd.DataFrame([{"avg_PNR": avg_pnr}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
        elif accuracy == "SIL_PNR":
            toappend = []
            for mu in range(emgfile["NUMBER_OF_MUS"]):
                sil = compute_sil(
                    ipts=emgfile["IPTS"][mu],
                    mupulses=emgfile["MUPULSES"][mu],
                    ignore_negative_ipts=ignore_negative_ipts,
                )
                toappend.append({"SIL": sil})
            toappend = pd.DataFrame(toappend)
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
            avg_sil = exportable_df["SIL"].mean()
            toappend = pd.DataFrame([{"avg_SIL": avg_sil}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
            toappend = []
            for mu in range(emgfile["NUMBER_OF_MUS"]):
                pnr = compute_pnr(
                    ipts=emgfile["IPTS"][mu],
                    mupulses=emgfile["MUPULSES"][mu],
                    fsamp=emgfile["FSAMP"],
                    constrain_pulses=constrain_pulses,
                )
                toappend.append({"PNR": pnr})
            toappend = pd.DataFrame(toappend)
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
            avg_pnr = exportable_df["PNR"].mean()
            toappend = pd.DataFrame([{"avg_PNR": avg_pnr}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)
        else:
            raise ValueError(
                f"accuracy must be one of 'default', 'SIL', 'PNR', 'SIL_PNR'. {accuracy} was passed instead"
            )
        mus_thresholds = self.compute_thresholds(
            emgfile=emgfile,
            n_firings=n_firings_rt_dert,
            mvc=mvc,
        )
        exportable_df = pd.concat([exportable_df, mus_thresholds], axis=1)
        mus_dr = self.compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=n_firings_RecDerec,
            n_firings_steady=n_firings_steady,
            start_steady=start_steady,
            end_steady=end_steady,
            idr_range=idr_range,
        )
        exportable_df = pd.concat([exportable_df, mus_dr], axis=1)
        covisi = self.compute_covisi(
            emgfile=emgfile,
            n_firings_RecDerec=n_firings_RecDerec,
            start_steady=start_steady,
            end_steady=end_steady,
            event_="steady",
            idr_range=idr_range,
        )
        exportable_df = pd.concat([exportable_df, covisi], axis=1)
        covsteady = self.compute_covsteady(
            emgfile=emgfile,
            start_steady=start_steady,
            end_steady=end_steady,
        )
        covsteady = pd.DataFrame([{"COV_steady": covsteady}])
        exportable_df = pd.concat([exportable_df, covsteady], axis=1)
        self.results.append_analysis_hist(
            "Basic Properties", exportable_df.to_dict("records")
        )
        return exportable_df

    def compute_thresholds(
        self,
        emgfile,
        event_="rt_dert",
        type_="abs_rel",
        n_firings=1,
        mvc=0,
    ):
        """from openHDEMG to get threshold
        Params (relevant for us): emgfile, mvc
        Returns: threhold dataframe
        """
        NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"]
        MUPULSES = emgfile["MUPULSES"]
        REF_SIGNAL = emgfile["REF_SIGNAL"]
        toappend = []
        for mu in range(NUMBER_OF_MUS):
            if len(MUPULSES[mu]) > 0:
                mup_rec = MUPULSES[mu][0:n_firings]
                mup_derec = MUPULSES[mu][-n_firings:]
                abs_RT = (float(REF_SIGNAL.iloc[mup_rec, 0].mean()) * mvc) / 100
                abs_DERT = (float(REF_SIGNAL.iloc[mup_derec, 0].mean()) * mvc) / 100
                rel_RT = float(REF_SIGNAL.iloc[mup_rec, 0].mean())
                rel_DERT = float(REF_SIGNAL.iloc[mup_derec, 0].mean())
            else:
                abs_RT = np.nan
                abs_DERT = np.nan
                rel_RT = np.nan
                rel_DERT = np.nan
            if event_ == "rt_dert" and type_ == "abs_rel":
                toappend.append(
                    {
                        "abs_RT": abs_RT,
                        "abs_DERT": abs_DERT,
                        "rel_RT": rel_RT,
                        "rel_DERT": rel_DERT,
                    }
                )
            elif event_ == "rt" and type_ == "abs_rel":
                toappend.append({"abs_RT": abs_RT, "rel_RT": rel_RT})
            elif event_ == "dert" and type_ == "abs_rel":
                toappend.append({"abs_DERT": abs_DERT, "rel_DERT": rel_DERT})
            elif event_ == "rt_dert" and type_ == "abs":
                toappend.append({"abs_RT": abs_RT, "abs_DERT": abs_DERT})
            elif event_ == "rt" and type_ == "abs":
                toappend.append({"abs_RT": abs_RT})
            elif event_ == "dert" and type_ == "abs":
                toappend.append({"abs_DERT": abs_DERT})
            elif event_ == "rt_dert" and type_ == "rel":
                toappend.append({"rel_RT": rel_RT, "rel_DERT": rel_DERT})
            elif event_ == "rt" and type_ == "rel":
                toappend.append({"rel_RT": rel_RT})
            elif event_ == "dert" and type_ == "rel":
                toappend.append({"rel_DERT": rel_DERT})
        mus_thresholds = pd.DataFrame(toappend)
        self.results.append_analysis_hist(
            "MUs Thresholds", mus_thresholds.to_dict("records")
        )
        return mus_thresholds

    def compute_dr(
        self,
        emgfile,
        n_firings_RecDerec=4,
        n_firings_steady=10,
        start_steady=-1,
        end_steady=-1,
        event_="rec_derec_steady",
        idr_range=None,
        time_range=None,
    ):
        """from openHDEMG to get discharge rate
        Params (relevant for us): emgfile, mvc, n_firings_RecDerec(user input), n_firings_steady(user input),
        start_steady(from select range), end_steady(from select range), event(user dropdwown)
        Returns: dr dataframe
        """
        errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
        if time_range is not None and event_ in ["steady", "rec_derec_steady"]:
            start_steady, end_steady = time_range
        if event_ not in [
            "rec",
            "derec",
            "rec_derec",
            "steady",
            "rec_derec_steady",
        ]:
            raise ValueError(errormessage)
        if not isinstance(n_firings_RecDerec, int):
            raise TypeError(
                f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
            )
        if not isinstance(n_firings_steady, int):
            raise TypeError(
                f"n_firings_steady must be an integer. {type(n_firings_steady)} was passed instead."
            )
        common = CommonOpenFunc()
        idr = common.compute_idr(emgfile=emgfile)
        if idr_range is not None:
            if not isinstance(idr_range, list):
                raise ValueError(
                    "idr_range can be None or a list of 2 numbers. "
                    + f"A{type(idr_range)} was passed instead."
                )
            else:
                if len(idr_range) != 2:
                    raise ValueError(
                        "idr_range can be None or a list of 2 numbers. "
                        + f"The list contains {len(idr_range)} numbers instead."
                    )
            for mu in idr.keys():
                idr[mu]["idr"] = idr[mu]["idr"][idr[mu]["idr"] > idr_range[0]]
                idr[mu]["idr"] = idr[mu]["idr"][idr[mu]["idr"] < idr_range[1]]
        toappend_dr = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            if len(idr[mu]["idr"]) >= n_firings_RecDerec:
                selected_idr = idr[mu]["idr"].iloc[0:n_firings_RecDerec]
                drrec = selected_idr.mean()

                length = len(idr[mu]["idr"])
                selected_idr = idr[mu]["idr"].iloc[
                    length - n_firings_RecDerec + 1 : length
                ]
                drderec = selected_idr.mean()
            else:
                drrec = np.nan
                drderec = np.nan

                warnings.warn(
                    "Calculation of DR at rec/derec failed, not enough firings"
                )
            index_startsteady = np.nan
            index_endsteady = np.nan
            for pos, pulse in enumerate(idr[mu]["mupulses"]):
                if pulse >= start_steady and pulse <= end_steady:
                    index_startsteady = pos
                    break
            if not math.isnan(index_startsteady):
                for pos, pulse in enumerate(idr[mu]["mupulses"]):
                    if pulse >= end_steady:
                        index_endsteady = pos
                        break
                    else:
                        index_endsteady = pos
            c1 = math.isnan(index_startsteady)
            c2 = math.isnan(index_endsteady)
            if not c1 and not c2:
                selected_idr = idr[mu]["idr"].loc[
                    index_startsteady + 1 : index_startsteady + n_firings_steady
                ]
                drstartsteady = selected_idr.mean()
                selected_idr = idr[mu]["idr"].loc[
                    index_endsteady + 1 - n_firings_steady : index_endsteady
                ]
                drendsteady = selected_idr.mean()
                selected_idr = idr[mu]["idr"].loc[
                    index_startsteady + 1 : index_endsteady
                ]
                drsteady = selected_idr.mean()
            else:
                drstartsteady = np.nan
                drendsteady = np.nan
                drsteady = np.nan
            selected_idr = idr[mu]["idr"]
            drall = selected_idr.mean()
            if event_ == "rec":
                toappend_dr.append({"DR_rec": drrec, "DR_all": drall})
            elif event_ == "derec":
                toappend_dr.append({"DR_derec": drderec, "DR_all": drall})
            elif event_ == "rec_derec":
                toappend_dr.append(
                    {"DR_rec": drrec, "DR_derec": drderec, "DR_all": drall}
                )
            elif event_ == "steady":
                toappend_dr.append(
                    {
                        "DR_start_steady": drstartsteady,
                        "DR_end_steady": drendsteady,
                        "DR_all_steady": drsteady,
                        "DR_all": drall,
                    }
                )
            elif event_ == "rec_derec_steady":
                toappend_dr.append(
                    {
                        "DR_rec": drrec,
                        "DR_derec": drderec,
                        "DR_start_steady": drstartsteady,
                        "DR_end_steady": drendsteady,
                        "DR_all_steady": drsteady,
                        "DR_all": drall,
                    }
                )
        mus_dr = pd.DataFrame(toappend_dr)
        return mus_dr

    def compute_covisi(
        self,
        emgfile,
        n_firings_RecDerec=4,
        start_steady=-1,
        end_steady=-1,
        event_="rec_derec_steady",
        idr_range=None,
        single_mu_number=-1,
    ):
        """from openHDEMG to get covisi for basic properties
        Params (relevant for us): emgfile, n_firings_RecDerec(user input), start_steady(from select range), end_steady(from select range)
        Returns: covisi dataframe
        """
        errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
        if not isinstance(n_firings_RecDerec, int):
            raise TypeError(
                f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
            )
        common = CommonOpenFunc()
        idr = common.compute_idr(emgfile=emgfile)
        if idr_range is not None:
            if not isinstance(idr_range, list):
                raise ValueError(
                    "idr_range can be None or a list of 2 numbers. "
                    + f"A{type(idr_range)} was passed instead."
                )
            else:
                if len(idr_range) != 2:
                    raise ValueError(
                        "idr_range can be None or a list of 2 numbers. "
                        + f"The list contains {len(idr_range)} numbers instead."
                    )
            idr_range[0] = emgfile["FSAMP"] / idr_range[0]
            idr_range[1] = emgfile["FSAMP"] / idr_range[1]
            for mu in idr.keys():
                idr[mu]["diff_mupulses"] = idr[mu]["diff_mupulses"][
                    idr[mu]["diff_mupulses"] < idr_range[0]
                ]
                idr[mu]["diff_mupulses"] = idr[mu]["diff_mupulses"][
                    idr[mu]["diff_mupulses"] > idr_range[1]
                ]
        if single_mu_number < 0:
            toappend_covisi = []
            for mu in range(emgfile["NUMBER_OF_MUS"]):
                selected_idr = idr[mu]["diff_mupulses"].iloc[0:n_firings_RecDerec]
                covisirec = (selected_idr.std() / selected_idr.mean()) * 100
                length = len(idr[mu]["diff_mupulses"])
                selected_idr = idr[mu]["diff_mupulses"].iloc[
                    length - n_firings_RecDerec + 1 : length
                ]
                covisiderec = (selected_idr.std() / selected_idr.mean()) * 100
                if event_ == "rec_derec_steady" or event_ == "steady":
                    idr_indexed = idr[mu].set_index("mupulses")
                    selected_idr = idr_indexed["diff_mupulses"].loc[
                        start_steady:end_steady
                    ]
                    covisisteady = (selected_idr.std() / selected_idr.mean()) * 100
                selected_idr = idr[mu]["diff_mupulses"]
                covisiall = (selected_idr.std() / selected_idr.mean()) * 100
                if event_ == "rec":
                    toappend_covisi.append(
                        {"COVisi_rec": covisirec, "COVisi_all": covisiall}
                    )
                elif event_ == "derec":
                    toappend_covisi.append(
                        {"COVisi_derec": covisiderec, "COVisi_all": covisiall}
                    )
                elif event_ == "rec_derec":
                    toappend_covisi.append(
                        {
                            "COVisi_rec": covisirec,
                            "COVisi_derec": covisiderec,
                            "COVisi_all": covisiall,
                        }
                    )
                elif event_ == "steady":
                    toappend_covisi.append(
                        {"COVisi_steady": covisisteady, "COVisi_all": covisiall}
                    )
                elif event_ == "rec_derec_steady":
                    toappend_covisi.append(
                        {
                            "COVisi_rec": covisirec,
                            "COVisi_derec": covisiderec,
                            "COVisi_steady": covisisteady,
                            "COVisi_all": covisiall,
                        }
                    )
            covisi = pd.DataFrame(toappend_covisi)
        else:
            selected_idr = idr[single_mu_number]["diff_mupulses"]
            covisiall = (selected_idr.std() / selected_idr.mean()) * 100
            toappend_covisi = []
            toappend_covisi.append({"COVisi_all": covisiall})
            covisi = pd.DataFrame(toappend_covisi)
        return covisi

    def compute_covsteady(self, emgfile, start_steady=-1, end_steady=-1):
        """from openHDEMG to get covsteady for basic properties
        Params (relevant for us): emgfile, start_steady(from select range), end_steady(from select range)
        Returns: covsteady
        """
        ref = emgfile["REF_SIGNAL"].loc[start_steady:end_steady]
        covsteady = (ref.std() / ref.mean()) * 100
        return covsteady[0]
