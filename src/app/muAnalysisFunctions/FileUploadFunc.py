import sys
import matplotlib

matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import QFileDialog, QLabel, QMessageBox, QDialog
from scipy.io import loadmat
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
import warnings
import os
import copy
import itertools
import json
import gzip
from io import StringIO
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.components.muAnalysisComponents.ConfirmationDialog import ConfirmationDialog
from ui.components.muAnalysisComponents.SaveablePlot import SaveablePlot
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from app.muAnalysisFunctions.CommonOpenFunc import CommonOpenFunc
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog


class FileUploadFunc:
    """Methods for handling the emgFile and its intital display to centre"""

    # global instance of file
    file = None

    def __init__(self, parent=None):
        """Initialises class instance
        Params: None
        Returns: class instance
        """
        self.parent = parent
        self.original_file_path = None
        self.coords = []
        self.cid = None
        self.error = 1
        self.mvc_value = None
        self.json = False
        self.unsortedFile = None  # store unsorted file version here

    def data_loaded(self):
        """Check if an EMG file is currently loaded.

        Returns:
            Boolean indicating whether FileUploadFunc.file contains valid data
        """
        return FileUploadFunc.file is not None

    def remove_mus_by_range(self, input_text):
        """Remove motor units specified by input text from the loaded EMG file.

        Args:
            input_text: String specifying MUs to remove in format:
                       - Single MU: "5" (removes MU 5)
                       - Range: "3-7" (removes MUs 3,4,5,6,7)
                       - Multiple: "1,3-5,8" (removes MUs 1,3,4,5,8)

        Updates all related data structures including BINARY_MUS_FIRING, IPTS,
        MUPULSES, ACCURACY, and NUMBER_OF_MUS. Indices are 1-based in input
        but converted to 0-based internally for array operations.

        Raises:
            ValueError: If no file is loaded or input format is invalid
        """
        if not self.data_loaded():
            raise ValueError("No file loaded.")

        emgfile = FileUploadFunc.file
        mus_to_remove = []
        parts = input_text.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue

            sub_parts = [p.strip() for p in part.split("-")]

            # In MU Analysis, we don't have arrays, so we expect 'mu' or 'start-end'
            if len(sub_parts) == 1:  # Single MU
                mu_idx = int(sub_parts[0]) - 1
                if mu_idx < 0:
                    raise ValueError("Indices must be positive.")
                mus_to_remove.append(mu_idx)
            elif len(sub_parts) == 2:  # MU range: start-end
                mu_start_idx = int(sub_parts[0]) - 1
                mu_end_idx = int(sub_parts[1]) - 1
                if mu_start_idx < 0 or mu_end_idx < 0:
                    raise ValueError("Indices must be positive.")
                if mu_end_idx < mu_start_idx:
                    raise ValueError("End of range cannot be smaller than start.")
                for mu_idx in range(mu_start_idx, mu_end_idx + 1):
                    mus_to_remove.append(mu_idx)
            else:
                raise ValueError("Each part must be in 'mu' or 'start-end' format.")

        mus_to_remove = sorted(list(set(mus_to_remove)))

        num_mus = emgfile["NUMBER_OF_MUS"]

        valid_mu_indices_to_remove = [i for i in mus_to_remove if i < num_mus]

        indices_to_keep = [
            i for i in range(num_mus) if i not in valid_mu_indices_to_remove
        ]

        if len(indices_to_keep) == num_mus:
            return  # No valid MUs to remove

        # Update BINARY_MUS_FIRING
        emgfile["BINARY_MUS_FIRING"] = emgfile["BINARY_MUS_FIRING"].iloc[
            :, indices_to_keep
        ]
        emgfile["BINARY_MUS_FIRING"].columns = range(len(indices_to_keep))

        # Update IPTS
        emgfile["IPTS"] = emgfile["IPTS"].iloc[:, indices_to_keep]
        emgfile["IPTS"].columns = range(len(indices_to_keep))

        # Update MUPULSES
        emgfile["MUPULSES"] = [emgfile["MUPULSES"][i] for i in indices_to_keep]

        # Update ACCURACY
        if not emgfile["ACCURACY"].empty:
            emgfile["ACCURACY"] = (
                emgfile["ACCURACY"].iloc[indices_to_keep].reset_index(drop=True)
            )

        # Update NUMBER_OF_MUS
        emgfile["NUMBER_OF_MUS"] = len(indices_to_keep)

    def select_file_button_pushed(self, analysis_plot, json):
        """Method trigged on file uplaod button, allowing only valid files and importing the data from a file dialog
        Params: analysis_plot: centre plot instance, json: make true for testing with json files
        Returns: None
        """
        file_dialog = QFileDialog()
        self.error = 1
        if json:
            self.json = True
            file_path, _ = file_dialog.getOpenFileName(
                None, "Select file", "", "JSON Files (*.json);;All Files (*.*)"
            )
        else:
            file_path, _ = file_dialog.getOpenFileName(
                None, "Select file", "", "MAT Files (*.mat);;All Files (*.*)"
            )
        if file_path:
            if json:
                valid = self.emg_from_json(file_path)
                self.original_file_path = file_path
                self.import_data(file_path, analysis_plot, valid)
                if valid:
                    if self.parent and hasattr(self.parent, "update_footer_file_info"):
                        self.parent.update_footer_file_info(file_path)
            else:
                try:
                    valid = self.emg_from_otb(file_path)
                except:
                    self.import_data(None, None, valid)
                else:
                    self.original_file_path = file_path
                    self.import_data(file_path, analysis_plot, valid)
                    if valid:
                        if self.parent and hasattr(self.parent, "update_footer_file_info"):
                            self.parent.update_footer_file_info(file_path)

    def import_data(self, filepath, analysis_plot, valid):
        """Plots files in centre if the file is valid
        Params: filepath, analysis_plot: centre plot instance, valid: if an error should be displayed instead
        Returns: None
        """
        if valid:
            self.plot_idr(self.file, analysis_plot)
        elif self.error:
            ErrorDialog("Loaded File has errors", "Error").exec_()

    def emg_from_json(self, filepath):
        """from openHDEMG but edited to sort and store file (this is for json files for testing)
        Params: filepath
        Returns: emgfile
        """
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            jsonemgfile = json.load(f)
        source = json.loads(jsonemgfile["SOURCE"])
        filename = json.loads(jsonemgfile["FILENAME"])
        if source in ["DEMUSE", "OTB", "CUSTOMCSV", "DELSYS"]:
            raw_signal = pd.read_json(
                StringIO(jsonemgfile["RAW_SIGNAL"]),
                orient="split",
            )
            raw_signal.columns = raw_signal.columns.astype(int)
            raw_signal.index = raw_signal.index.astype(int)
            raw_signal.sort_index(inplace=True)
            ref_signal = pd.read_json(
                StringIO(jsonemgfile["REF_SIGNAL"]),
                orient="split",
            )
            ref_signal.columns = ref_signal.columns.astype(int)
            ref_signal.index = ref_signal.index.astype(int)
            ref_signal.sort_index(inplace=True)
            accuracy = pd.read_json(
                StringIO(jsonemgfile["ACCURACY"]),
                orient="split",
            )
            try:
                accuracy.columns = accuracy.columns.astype(int)
            except Exception:
                accuracy.columns = [*range(len(accuracy.columns))]
                warnings.warn(
                    "Error while loading accuracy, check or recalculate accuracy"
                )
            accuracy.index = accuracy.index.astype(int)
            accuracy.sort_index(inplace=True)
            ipts = pd.read_json(StringIO(jsonemgfile["IPTS"]), orient="split")
            ipts.columns = ipts.columns.astype(int)
            ipts.index = ipts.index.astype(int)
            ipts.sort_index(inplace=True)
            mupulses = json.loads(jsonemgfile["MUPULSES"])
            for num, element in enumerate(mupulses):
                mupulses[num] = np.array(element)
            fsamp = float(json.loads(jsonemgfile["FSAMP"]))
            ied = float(json.loads(jsonemgfile["IED"]))
            emg_length = int(json.loads(jsonemgfile["EMG_LENGTH"]))
            number_of_mus = int(json.loads(jsonemgfile["NUMBER_OF_MUS"]))
            binary_mus_firing = pd.read_json(
                StringIO(jsonemgfile["BINARY_MUS_FIRING"]),
                orient="split",
            )
            binary_mus_firing.columns = binary_mus_firing.columns.astype(int)
            binary_mus_firing.index = binary_mus_firing.index.astype(int)
            binary_mus_firing.sort_index(inplace=True)
            extras = pd.read_json(StringIO(jsonemgfile["EXTRAS"]), orient="split")
            emgfile = {
                "SOURCE": source,
                "FILENAME": filename,
                "RAW_SIGNAL": raw_signal,
                "REF_SIGNAL": ref_signal,
                "ACCURACY": accuracy,
                "IPTS": ipts,
                "MUPULSES": mupulses,
                "FSAMP": fsamp,
                "IED": ied,
                "EMG_LENGTH": emg_length,
                "NUMBER_OF_MUS": number_of_mus,
                "BINARY_MUS_FIRING": binary_mus_firing,
                "EXTRAS": extras,
            }
        elif source in ["OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"]:
            fsamp = float(json.loads(jsonemgfile["FSAMP"]))
            ref_signal = pd.read_json(
                StringIO(jsonemgfile["REF_SIGNAL"]),
                orient="split",
            )
            ref_signal.columns = ref_signal.columns.astype(int)
            ref_signal.index = ref_signal.index.astype(int)
            ref_signal.sort_index(inplace=True)
            extras = pd.read_json(StringIO(jsonemgfile["EXTRAS"]), orient="split")

            emgfile = {
                "SOURCE": source,
                "FILENAME": filename,
                "FSAMP": fsamp,
                "REF_SIGNAL": ref_signal,
                "EXTRAS": extras,
            }
        else:
            raise Exception("\nFile source not recognised\n")
        self.unsortedFile = emgfile
        FileUploadFunc.file = self.sort_MUs(emgfile)
        return emgfile

    def get_otb_refsignal(self, df, refsig):
        """from openHDEMG to get reference signal
        Params (relevant to us): None
        Returns: ref signal data frame
        """
        assert refsig[0] in [
            True,
            False,
        ], f"refsig[0] must be 'true' or 'false'. {refsig[0]} was passed instead."
        assert refsig[1] in [
            "fullsampled",
            "subsampled",
        ], f"refsig[1] must be 'fullsampled' or 'subsampled'. {refsig[1]} was passed instead."

        if refsig[0] is True:
            if refsig[1] == "subsampled":
                REF_SIGNAL_SUBSAMPLED = df.filter(regex="performed path")
                if not REF_SIGNAL_SUBSAMPLED.empty:
                    REF_SIGNAL_SUBSAMPLED = REF_SIGNAL_SUBSAMPLED.rename(
                        columns={REF_SIGNAL_SUBSAMPLED.columns[0]: 0}
                    )
                    if max(REF_SIGNAL_SUBSAMPLED[0]) > 100:
                        warnings.warn(
                            "\nALERT! Ref signal greater than 100, did you use values normalised to the MVC?\n"
                        )
                    return REF_SIGNAL_SUBSAMPLED
                else:
                    warnings.warn(
                        "\nReference signal not found, it might be necessary for some analyses\n"
                    )
                    return pd.DataFrame(columns=[0])
            elif refsig[1] == "fullsampled":
                REF_SIGNAL_FULLSAMPLED = df.filter(regex="acquired data")
                if not REF_SIGNAL_FULLSAMPLED.empty:
                    REF_SIGNAL_FULLSAMPLED = REF_SIGNAL_FULLSAMPLED.rename(
                        columns={REF_SIGNAL_FULLSAMPLED.columns[0]: 0}
                    )
                    if max(REF_SIGNAL_FULLSAMPLED[0]) > 100:
                        warnings.warn(
                            "\nALERT! Ref signal grater than 100, did you use values normalised to the MVC?\n"
                        )
                    return REF_SIGNAL_FULLSAMPLED
                else:
                    warnings.warn(
                        "\nReference signal not found, it might be necessary for some analyses\n"
                    )
                    return pd.DataFrame(columns=[0])
        else:
            warnings.warn(
                "\nNot searched for reference signal, it might be necessary for some analyses\n"
            )
            return pd.DataFrame(columns=[0])

    def get_otb_decomposition(self, df):
        """from openHDEMG to get otb decomp
        Params (relevant to us): None
        Returns: Binary MUs Firing and IPTS from imported data
        """
        IPTS = df.filter(regex="Source for decomposition")
        IPTS.columns = np.arange(len(IPTS.columns))
        if IPTS.empty:
            self.error = 0
            ErrorDialog("(IPTS) not found", "Error").exec_()
            raise ValueError(
                "\nSource for decomposition (IPTS) not found in the .mat file\n"
            )
            return
        BINARY_MUS_FIRING = df.filter(regex="Decomposition of")
        BINARY_MUS_FIRING.columns = np.arange(len(BINARY_MUS_FIRING.columns))
        if BINARY_MUS_FIRING.empty:
            self.error = 0
            ErrorDialog("(BINARY_MUS_FIRING) not found", "Error").exec_()
            raise ValueError(
                "\nDecomposition of (BINARY_MUS_FIRING) not found in the .mat file\n"
            )
            return
        return IPTS, BINARY_MUS_FIRING

    def get_otb_ied(self, df):
        """from openHDEMG to get otb_ied
        Params (relevant to us): None
        Returns: IED (nan on no IED)
        """
        OTBelectrodes_ied = {
            "GR04MM1305": 4,
            "GR08MM1305": 8,
            "GR100ML1305": 2.5,
            "GR10MM0804": 10,
            "GR10MM0808": 10,
            "HD04MM1305": 4,
            "HD08MM1305": 8,
            "HD10MM0804": 10,
            "HD10MM0808": 10,
        }
        for matrix in OTBelectrodes_ied.keys():
            if matrix in str(df.columns):
                IED = float(OTBelectrodes_ied[matrix])
                return IED
        warnings.warn("OTB recording grid not found, IED could not be inferred")
        return np.nan

    def get_otb_rawsignal(self, df, extras_regex):
        """from openHDEMG to get otb raw signal
        Params (relevant to us): None
        Returns: Raw signal
        """
        base_pattern = (
            "Source for decomposition|Decomposition of|acquired data|performed path"
        )
        if extras_regex is None:
            pattern = base_pattern
        else:
            pattern = base_pattern + "|" + extras_regex

        emg_df = df[df.columns.drop(list(df.filter(regex=pattern)))]
        expectedchannels = np.nan
        OTBelectrodes_Nelectrodes = {
            "GR04MM1305": 64,
            "GR08MM1305": 64,
            "GR100ML1305": 64,
            "GR10MM0804": 32,
            "GR10MM0808": 64,
            "HD04MM1305": 64,
            "HD08MM1305": 64,
            "HD10MM0804": 32,
            "HD10MM0808": 64,
        }
        for matrix in OTBelectrodes_Nelectrodes.keys():
            if matrix in str(emg_df.columns):
                expectedchannels = int(OTBelectrodes_Nelectrodes[matrix])
                break
        if expectedchannels is np.nan:
            self.error = 0
            ErrorDialog("Matrix not recognised", "Error").exec_()
            raise ValueError("Matrix not recognised")
        if len(emg_df.columns) == expectedchannels:
            emg_df.columns = np.arange(len(emg_df.columns))
            RAW_SIGNAL = emg_df
            return RAW_SIGNAL
        else:
            self.error = 0
            ErrorDialog("Failure in searching the raw signal", "Error").exec_()
            raise ValueError(
                "\nFailure in searching the raw signal, please check that it is present in the .mat file and that only the accepted parameters have been included\n"
            )

    def get_otb_extras(self, df, extras):
        """from openHDEMG to get extra features in imported data
        Params (relevant to us): None
        Returns: Extra data
        """
        if extras is None:
            return pd.DataFrame(columns=[0])
        else:
            EXTRAS = df.filter(regex=extras)
            return EXTRAS

    def mupulses_from_binary(self, binarymusfiring):
        """from openHDEMG to get mu pulses
        Params (relevant to us): None
        Returns: Extra data
        """
        numberofMUs = len(binarymusfiring.columns)
        MUPULSES = [[] for _ in range(numberofMUs)]
        for mu in binarymusfiring:
            my_ndarray = []
            for idx, x in binarymusfiring[mu].items():
                if x > 0:
                    my_ndarray.append(idx)
            MUPULSES[mu] = np.array(my_ndarray)
        return MUPULSES

    def emg_from_otb(
        self,
        filepath,
        ext_factor=8,
        refsig=[True, "fullsampled"],
        version="1.5.9.3",
        extras=None,
        ignore_negative_ipts=False,
    ):
        """from openHDEMG but edited to sort and store file (this is for otb files) and error on bad mat files
        Params (relevant to us): filepath
        Returns: 1 on success
        """
        try:
            mat_file = loadmat(filepath, simplify_cells=True)
            valid_versions = [
                "1.5.3.0",
                "1.5.4.0",
                "1.5.5.0",
                "1.5.6.0",
                "1.5.7.2",
                "1.5.7.3",
                "1.5.8.0",
                "1.5.9.3",
            ]
            if version not in valid_versions:
                raise ValueError(
                    f"\nSpecified version is not valid. Use one of:\n{valid_versions}\n"
                )
            if version in [
                "1.5.3.0",
                "1.5.4.0",
                "1.5.5.0",
                "1.5.6.0",
                "1.5.7.2",
                "1.5.7.3",
                "1.5.8.0",
                "1.5.9.3",
            ]:
                df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])
                SOURCE = "OTB"
                FILENAME = os.path.basename(filepath)
                FSAMP = float(mat_file["SamplingFrequency"])
                IED = self.get_otb_ied(df=df)
                RAW_SIGNAL = self.get_otb_rawsignal(df=df, extras_regex=extras)
                IPTS, BINARY_MUS_FIRING = self.get_otb_decomposition(df=df)
                BINARY_MUS_FIRING = BINARY_MUS_FIRING.shift(-int(ext_factor))
                BINARY_MUS_FIRING.fillna(value=0, inplace=True)
                MUPULSES = self.mupulses_from_binary(binarymusfiring=BINARY_MUS_FIRING)
                EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape
                REF_SIGNAL = self.get_otb_refsignal(df=df, refsig=refsig)
                if NUMBER_OF_MUS > 0:
                    to_append = []
                    for mu in range(NUMBER_OF_MUS):
                        func = CommonOpenFunc()
                        sil = func.compute_sil(
                            ipts=IPTS[mu],
                            mupulses=MUPULSES[mu],
                            ignore_negative_ipts=ignore_negative_ipts,
                        )
                        to_append.append(sil)
                    ACCURACY = pd.DataFrame(to_append)
                else:
                    ACCURACY = pd.DataFrame(columns=[0])
                EXTRAS = self.get_otb_extras(df=df, extras=extras)
            emgfile = {
                "SOURCE": SOURCE,
                "FILENAME": FILENAME,
                "RAW_SIGNAL": RAW_SIGNAL,
                "REF_SIGNAL": REF_SIGNAL,
                "ACCURACY": ACCURACY,
                "IPTS": IPTS,
                "MUPULSES": MUPULSES,
                "FSAMP": FSAMP,
                "IED": IED,
                "EMG_LENGTH": EMG_LENGTH,
                "NUMBER_OF_MUS": NUMBER_OF_MUS,
                "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
                "EXTRAS": EXTRAS,
            }
            self.unsortedFile = emgfile
            FileUploadFunc.file = self.sort_MUs(
                emgfile
            )  # sort imported MUs by recruitment order by default
            return 1
        except:
            return None

    def plot_idr(
        self,
        emgfile,
        analysis_plot,
        munumber="all",
        addrefsig=True,
        timeinseconds=True,
        figsize=[20, 15],
        tight_layout=True,
        line2d_kwargs_ax1=None,
        line2d_kwargs_ax2=None,
        axes_kwargs=None,
        showimmediately=False,
    ):
        """from openHDEMG to plot idr on graph when first loaded
        Params (relevant to us): emgfile, analysis_plot(instance of centre plot)
        Returns: None
        """
        common = CommonOpenFunc()
        idr = common.compute_idr(emgfile=emgfile)
        if isinstance(munumber, str):
            if emgfile["NUMBER_OF_MUS"] == 1:
                munumber = 0
            else:
                munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]
        if isinstance(munumber, list) and len(munumber) == 1:
            munumber = munumber[0]
        figname = "aditi_unique_name"
        plt.close()  # This is to prevent plots from overlaying in centre on repeated uploads
        fig, ax1 = plt.subplots(
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=figname,
        )
        if isinstance(munumber, int):
            ax1.plot(
                idr[munumber]["timesec" if timeinseconds else "mupulses"],
                idr[munumber]["idr"],
                ".",
                markersize=12,
            )
            ax1.set_ylabel("MU {} (pps)".format(munumber))
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
        elif isinstance(munumber, list):
            idr_all = pd.DataFrame({key: df["idr"] for key, df in idr.items()})
            idr_all = idr_all[munumber]
            common = CommonOpenFunc()
            norm_idr_all = common.min_max_scaling(data=idr_all, col_by_col=False)
            for count, thisMU in enumerate(munumber):
                norm_idr = norm_idr_all[thisMU]
                if norm_idr.mean() <= 0.5:
                    norm_idr = norm_idr + (0.5 - norm_idr.mean()) + count
                else:
                    norm_idr = norm_idr - (norm_idr.mean() - 0.5) + count
                ax1.plot(
                    idr[thisMU]["timesec" if timeinseconds else "mupulses"][1:],
                    norm_idr.dropna(),
                    ".",
                    markersize=8,
                )
            ax1.set_yticks(np.arange(0.5, len(munumber) + 0.5, 1))
            ax1.set_yticklabels([str(mu) for mu in munumber])
            ax1.set_ylabel("Motor units")
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
        else:
            raise TypeError(
                "While calling the plot_idr function, you should pass an "
                + "integer, a list or 'all' to munumber"
            )
        if addrefsig:
            if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
                raise TypeError(
                    "REF_SIGNAL is probably absent or it is not contained in a "
                    + "dataframe"
                )
            x_axis = (
                emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
                if timeinseconds
                else emgfile["REF_SIGNAL"].index
            )
            ax2 = ax1.twinx()
            ax2.plot(x_axis, emgfile["REF_SIGNAL"][0], color='#555555')
            ax2.set_ylabel("MVC")
            ax2.set_zorder(0)
            ax1.set_zorder(1)
            ax1.patch.set_alpha(0)
        canvas = SaveablePlot(fig)  # plotting in centre with the data now handled
        analysis_plot.display_fig(canvas)

    def handle_reset_workflow(self, analysis_plot):
        """
        Handles the full workflow for resetting analysis data, including confirmation.
        """
        # Check if there's a file loaded to reset
        if self.original_file_path is None:
            print("No file loaded to reset.")
            return

        dialog = ConfirmationDialog(
            "This will reset the current analysis.", "Confirm Reset"
        )
        if dialog.exec_() == QDialog.Accepted:
            # User clicked 'Reset'
            self.reset_analysis_data(analysis_plot)

    def reset_analysis_data(self, analysis_plot):
        """
        Resets the analysis data by reloading the original file, clearing any transformations.
        """
        if self.original_file_path is None:
            print("No original file path stored. Cannot reset.")
            return

        print("--- DEBUG: Resetting analysis data by reloading original file ---")

        # Clear any transformation data (MVC value, etc.)
        self.mvc_value = None
        # Add any other transformation data clearing logic here

        # Reload the original file to reset any transformations
        if self.json:
            valid = self.emg_from_json(self.original_file_path)
        else:
            valid = self.emg_from_otb(self.original_file_path)
        if valid:
            # Re-import the data to refresh the display
            self.import_data(self.original_file_path, analysis_plot, valid)
            print("File successfully reloaded, transformations cleared.")
        else:
            print("Error reloading file during reset.")
            # If reload fails, show error but keep the original file path
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("Reset Error")
            error_dialog.setInformativeText("Failed to reload the original file")
            error_dialog.setWindowTitle("Error")
            error_dialog.exec_()

    def plot_refsig(
        self,
        emgfile,
        analysis_plot,
        timeinseconds=True,
        figsize=[20, 15],
        tight_layout=True,
        line2d_kwargs_ax1=None,
        axes_kwargs=None,
        showimmediately=False,
    ):
        """From OPENHDEMG. Plots the reference signal
        Params:
            - emgfile: the file
            - analysis_plot: instance used to plot fig in the centre
            - timeinseconds: boolean if you want the axis to be plotted in seconds
            - figsize: (legacy code) defines the size of the plot, but now it's
            plotted in the centre
            - tight_layout: specifies different UI for the plot
            - line2d_kwargs_ax1: keyword arguments for line2d objects
            - axes_kwargs: keyword arguments for axes styling
            - showimmediately: (legacy code) plots it immediately, but this function now defaults to plotting it immediately
        """
        if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            refsig = emgfile["REF_SIGNAL"]
        else:
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a "
                + "dataframe"
            )

        if timeinseconds:
            x_axis = refsig.index / emgfile["FSAMP"]
        else:
            x_axis = refsig.index

        figname = "Reference Signal Graph"
        plt.close()
        fig, ax1 = plt.subplots(
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=figname,
        )

        ax1.plot(x_axis, refsig[0], color='#555555')

        ax1.set_ylabel("MVC")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        # Plotting
        canvas = SaveablePlot(fig)
        analysis_plot.display_fig(canvas)

    def sort_MUs(self, emgfile):
        """
        Sort motor units (MUs) in an EMG file based on the timing of their
        first detected pulse.

        Parameters
        ----------
        emgfile : dict
            A dictionary containing EMG data fields, including MU pulse timings,
            accuracy metrics, binary firing patterns, and other related signals.

        Returns
        -------
        dict
            A new EMG file dictionary with all MU-related fields sorted according
            to the order of their first pulses.
        """
        
        if emgfile["NUMBER_OF_MUS"] <= 1:
            return emgfile

        # Create the object to store the sorted emgfile.
        # Create a deepcopy to avoid changing the original emgfile
        sorted_emgfile = copy.deepcopy(emgfile)
        """
        Need to be changed: ==>
        emgfile =   {
                    "SOURCE" : SOURCE,
                    "RAW_SIGNAL" : RAW_SIGNAL,
                    "REF_SIGNAL" : REF_SIGNAL,
                    ==> "ACCURACY": ACCURACY,
                    ==> "IPTS" : IPTS,
                    ==> "MUPULSES" : MUPULSES,
                    "FSAMP" : FSAMP,
                    "IED" : IED,
                    "EMG_LENGTH" : EMG_LENGTH,
                    "NUMBER_OF_MUS" : NUMBER_OF_MUS,
                    ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                    }
        """

        # Identify the sorting_order by the first MUpulse of every MUs
        df = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            if len(emgfile["MUPULSES"][mu]) > 0:
                df.append(emgfile["MUPULSES"][mu][0])
            else:
                df.append(np.inf)

        df = pd.DataFrame(df, columns=["firstpulses"])
        df.sort_values(by="firstpulses", inplace=True)
        sorting_order = list(df.index)

        # Sort ACCURACY (single column)
        for origpos, newpos in enumerate(sorting_order):
            sorted_emgfile["ACCURACY"].loc[origpos] = emgfile["ACCURACY"].loc[newpos]

        # Sort IPTS (multiple columns, sort by columns, then reset columns' name)
        sorted_emgfile["IPTS"] = sorted_emgfile["IPTS"].reindex(columns=sorting_order)
        sorted_emgfile["IPTS"].columns = np.arange(emgfile["NUMBER_OF_MUS"])

        # Sort BINARY_MUS_FIRING (multiple columns, sort by columns,
        # then reset columns' name)
        sorted_emgfile["BINARY_MUS_FIRING"] = sorted_emgfile[
            "BINARY_MUS_FIRING"
        ].reindex(columns=sorting_order)
        sorted_emgfile["BINARY_MUS_FIRING"].columns = np.arange(
            emgfile["NUMBER_OF_MUS"]
        )

        for origpos, newpos in enumerate(sorting_order):
            sorted_emgfile["MUPULSES"][origpos] = emgfile["MUPULSES"][newpos]

        return sorted_emgfile

    def updateEMGFile(self, emgfile):
        print(f"updating original file")
        FileUploadFunc.file = emgfile
