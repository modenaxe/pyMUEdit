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


# class for functions required for the MU properties dialog
class MUPropertiesFunc:
    """Motor Unit Properties functionality"""

    def __init__(self):
        # MVC value for calculations
        self.mvc_value = None
        self.results = store
        self.basic = []
        self.over = None
        print(id(self.results))

    # MVC value management
    def set_mvc(self, mvc_value):
        """Set the Maximum Voluntary Contraction value"""
        self.mvc_value = mvc_value

    # turns mcv input text into a string to be used
    def get_mvc(self):
        """Get the current MVC value"""
        return str(self.mvc_value.text())

    # general function to turn input text into usable string
    def convert(self, value):
        return str(value.text())

    # used for basic properties
    # errors if no file or missing inputs
    def basic_prop(self, analysis_plot, rec, start, over):
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
        over.hide()
        self.over = over
        self.basic = [self.convert(rec), self.convert(start)]
        SelectRange(analysis_plot, self.two_point)

    def two_point(self, x, y):
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

    # OPENHDEMG
    # adapted parts labelled with AC
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
        # Collect the information to export
        # First: create a dataframe that contains all the output
        exportable_df = []

        # AC get mvc from dialog
        # AC I removed their version of show select and did it above
        exportable_df.append({"MVC": mvc})
        exportable_df = pd.DataFrame(exportable_df)

        # Basically, we create an empty list, append values, convert the
        # list in a pd.DataFrame and then concatenate to the exportable_df
        toappend = []
        for i in range(emgfile["NUMBER_OF_MUS"]):
            toappend.append({"MU_number": i})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        if accuracy == "default":
            # Report the original accuracy
            toappend = emgfile["ACCURACY"]
            toappend.columns = ["Accuracy"]
            exportable_df = pd.concat([exportable_df, toappend], axis=1)

            # Calculate avrage accuracy
            avg_accuracy = exportable_df["Accuracy"].mean()
            toappend = pd.DataFrame([{"avg_Accuracy": avg_accuracy}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)

        elif accuracy == "SIL":
            # Calculate SIL
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

            # Calculate avrage SIL
            avg_sil = exportable_df["SIL"].mean()
            toappend = pd.DataFrame([{"avg_SIL": avg_sil}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)

        elif accuracy == "PNR":
            # Calculate PNR
            # Repeat the task for every new column to fill and concatenate
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

            # Calculate avrage PNR
            # dropna to avoid nan average.
            avg_pnr = exportable_df["PNR"].mean()
            toappend = pd.DataFrame([{"avg_PNR": avg_pnr}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)

        elif accuracy == "SIL_PNR":
            # Calculate SIL
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

            # Calculate avrage SIL
            avg_sil = exportable_df["SIL"].mean()
            toappend = pd.DataFrame([{"avg_SIL": avg_sil}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)

            # Calculate PNR
            # Repeat the task for every new column to fill and concatenate
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

            # Calculate avrage PNR
            # dropna to avoid nan average.
            avg_pnr = exportable_df["PNR"].mean()
            toappend = pd.DataFrame([{"avg_PNR": avg_pnr}])
            exportable_df = pd.concat([exportable_df, toappend], axis=1)

        else:
            raise ValueError(
                f"accuracy must be one of 'default', 'SIL', 'PNR', 'SIL_PNR'. {accuracy} was passed instead"
            )

        # Calculate RT and DERT
        mus_thresholds = self.compute_thresholds(
            emgfile=emgfile,
            n_firings=n_firings_rt_dert,
            mvc=mvc,
        )
        exportable_df = pd.concat([exportable_df, mus_thresholds], axis=1)

        # Calculate DR at recruitment, derecruitment, all, start, end of the
        # steady-state and on all the contraction.
        mus_dr = self.compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=n_firings_RecDerec,
            n_firings_steady=n_firings_steady,
            start_steady=start_steady,
            end_steady=end_steady,
            idr_range=idr_range,
        )
        exportable_df = pd.concat([exportable_df, mus_dr], axis=1)

        # Calculate COVisi
        covisi = self.compute_covisi(
            emgfile=emgfile,
            n_firings_RecDerec=n_firings_RecDerec,
            start_steady=start_steady,
            end_steady=end_steady,
            event_="steady",
            idr_range=idr_range,
        )
        exportable_df = pd.concat([exportable_df, covisi], axis=1)

        # Calculate COVsteady
        covsteady = self.compute_covsteady(
            emgfile=emgfile,
            start_steady=start_steady,
            end_steady=end_steady,
        )
        covsteady = pd.DataFrame([{"COV_steady": covsteady}])
        exportable_df = pd.concat([exportable_df, covsteady], axis=1)
        print(exportable_df)
        self.results.append_analysis_hist(
            "Basic Properties", exportable_df.to_dict("records")
        )
        return exportable_df

    # OPEN
    # AC: removed their version of show select code
    def compute_thresholds(
        self,
        emgfile,
        event_="rt_dert",
        type_="abs_rel",
        n_firings=1,
        mvc=0,
    ):
        # Extract the variables of interest from the EMG file
        NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"]
        MUPULSES = emgfile["MUPULSES"]
        REF_SIGNAL = emgfile["REF_SIGNAL"]

        # Check that all the inputs are correct
        if event_ not in ["rt_dert", "rt", "dert"]:
            raise ValueError(
                f"event_ must be one of : 'rt_dert', 'rt', 'dert'. {event_} was passed instead."
            )

        if type_ not in ["abs_rel", "rel", "abs"]:
            raise ValueError(
                f"event_ must be one of : 'abs_rel', 'rel', 'abs'. {event_} was passed instead."
            )

        if not isinstance(mvc, (float, int)):
            raise TypeError(
                f"mvc must be one of the following types: float, int. {type(mvc)} was passed instead."
            )

        if type_ != "rel" and mvc == 0:
            # Ask the user to input MVC
            mvc = float(
                input("--------------------------------\nEnter MVC value in newton: ")
            )

        # Create an object to append the results
        toappend = []
        # Loop all the MUs
        for mu in range(NUMBER_OF_MUS):
            # Manage the exception of empty MUs
            if len(MUPULSES[mu]) > 0:
                # Detect the first and last firing of the MU
                mup_rec = MUPULSES[mu][0:n_firings]
                mup_derec = MUPULSES[mu][-n_firings:]
                # Calculate absolute and relative RT and DERT if requested
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
        # Check that all the inputs are correct
        errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."

        # Handle time_range if provided (for steady and rec_derec_steady)
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

        # Filter firings outside the idr_range, if required
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

        # Create an object to append the results
        toappend_dr = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs
            # DR rec/derec
            if len(idr[mu]["idr"]) >= n_firings_RecDerec:
                selected_idr = idr[mu]["idr"].iloc[0:n_firings_RecDerec]
                drrec = selected_idr.mean()

                length = len(idr[mu]["idr"])
                selected_idr = idr[mu]["idr"].iloc[
                    length - n_firings_RecDerec + 1 : length
                ]
                # +1 because len() counts position 0
                drderec = selected_idr.mean()

            else:
                drrec = np.nan
                drderec = np.nan

                warnings.warn(
                    "Calculation of DR at rec/derec failed, not enough firings"
                )

            # Set indexes for the steady-state firings
            index_startsteady = np.nan
            index_endsteady = np.nan

            # Find nex indexes of start and end steady if possible
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
                        # Account for MUs that stop firing before the end of the
                        # steady-state phase
                        index_endsteady = pos

            # Calculate DR at the steady-state phase if there is a steady-state
            c1 = math.isnan(index_startsteady)
            c2 = math.isnan(index_endsteady)

            if not c1 and not c2:
                # DR drstartsteady
                # Use +1 to work only on the steady state (here and after)
                # because the idr is calculated on the previous firing.
                selected_idr = idr[mu]["idr"].loc[
                    index_startsteady + 1 : index_startsteady + n_firings_steady
                ]
                drstartsteady = selected_idr.mean()

                # DR endsteady
                selected_idr = idr[mu]["idr"].loc[
                    index_endsteady + 1 - n_firings_steady : index_endsteady
                ]
                drendsteady = selected_idr.mean()

                # DR steady
                selected_idr = idr[mu]["idr"].loc[
                    index_startsteady + 1 : index_endsteady
                ]
                drsteady = selected_idr.mean()

            else:
                drstartsteady = np.nan
                drendsteady = np.nan
                drsteady = np.nan

            # DR all contraction
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

        # Convert the dictionary in a DataFrame
        mus_dr = pd.DataFrame(toappend_dr)

        return mus_dr

    # OPEN
    # AC: removed their version of show select code
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
        # Check that all the inputs are correct
        errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
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

        # We use the idr pd.DataFrame to calculate the COVisi
        common = CommonOpenFunc()
        idr = common.compute_idr(emgfile=emgfile)

        # Filter firings outside the idr_range, if required
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

        # Check if we need to analyse all the MUs or a single MU
        if single_mu_number < 0:
            # Create an object to append the results
            toappend_covisi = []
            for mu in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs

                # COVisi rec
                selected_idr = idr[mu]["diff_mupulses"].iloc[0:n_firings_RecDerec]
                covisirec = (selected_idr.std() / selected_idr.mean()) * 100

                # COVisi derec
                length = len(idr[mu]["diff_mupulses"])
                selected_idr = idr[mu]["diff_mupulses"].iloc[
                    length - n_firings_RecDerec + 1 : length
                ]  # +1 because len() counts position 0
                covisiderec = (selected_idr.std() / selected_idr.mean()) * 100

                # COVisi all steady
                if event_ == "rec_derec_steady" or event_ == "steady":
                    idr_indexed = idr[mu].set_index("mupulses")
                    selected_idr = idr_indexed["diff_mupulses"].loc[
                        start_steady:end_steady
                    ]
                    covisisteady = (selected_idr.std() / selected_idr.mean()) * 100

                # COVisi all contraction
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

            # Convert the dictionary in a DataFrame
            covisi = pd.DataFrame(toappend_covisi)

        else:
            # COVisi all contraction
            selected_idr = idr[single_mu_number]["diff_mupulses"]
            covisiall = (selected_idr.std() / selected_idr.mean()) * 100
            # Create an object to append the results
            toappend_covisi = []
            toappend_covisi.append({"COVisi_all": covisiall})
            # Convert the dictionary in a DataFrame
            covisi = pd.DataFrame(toappend_covisi)

        return covisi

    # OPEN
    # AC: removed their version of show select code
    def compute_covsteady(self, emgfile, start_steady=-1, end_steady=-1):
        ref = emgfile["REF_SIGNAL"].loc[start_steady:end_steady]
        covsteady = (ref.std() / ref.mean()) * 100

        return covsteady[0]

    # not sure what this for, from Finn's
    # def calculate_mvc_based_statistics(self, force_data):
    #     """Calculate summary statistics based on MVC value"""
    #     if self.mvc_value is None:
    #         print("Warning: MVC value not set. Cannot calculate MVC-based statistics.")
    #         return None

    #     if force_data is None or len(force_data) == 0:
    #         print("Warning: No force data available for MVC-based calculations.")
    #         return None

    #     # Convert force data to percentage of MVC
    #     force_percentage = (force_data / self.mvc_value) * 100

    #     # Calculate summary statistics
    #     stats = {
    #         'mvc_value': self.mvc_value,
    #         'mean_force_percentage': np.mean(force_percentage),
    #         'max_force_percentage': np.max(force_percentage),
    #         'min_force_percentage': np.min(force_percentage),
    #         'std_force_percentage': np.std(force_percentage),
    #         'force_percentage_data': force_percentage
    #     }

    #     return stats
