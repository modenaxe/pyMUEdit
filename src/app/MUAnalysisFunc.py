import sys
from PyQt5.QtWidgets import (
    QFileDialog
)
from scipy.io import loadmat
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
# from openhdemg.library.electrodes import *
import warnings
import os
import copy
import itertools

class MUAnalysisFunc:
    def __init__(self):
        self.file = None

    def select_file_button_pushed(self):
        """Open file dialog to select file for editing and automatically import it."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(None, "Select file", "", "MAT Files (*.mat);;All Files (*.*)")

        if file_path:
            self.emg_from_otb(file_path)
            self.import_data(file_path)


    def import_data(self, filepath):
        # plot_idr(self.file)
        print(self.file)

    def compute_sil(self, ipts, mupulses, ignore_negative_ipts=False):
        # Manage exception of no firings
        if len(mupulses) == 0:
            return np.nan

        # Extract source and peaks and align source and peaks based on IPTS
        source = ipts.to_numpy()

        if ignore_negative_ipts:
            # Ignore negative values, this is particularly needed for negative
            # unbalanced sources.
            source = source * np.abs(source)

        peaks_idxs = mupulses - ipts.index[0]

        # Create clusters
        peak_cluster = source[peaks_idxs]
        noise_cluster = np.delete(source, peaks_idxs)

        # Create centroids for each cluster
        peak_centroid = np.mean(peak_cluster)
        noise_centroid = np.mean(noise_cluster)

        # Calculate within-cluster sums of point-to-centroid distances using the
        # squared Euclidean distance metric. It is defined as the sum of the
        # squares of the differences between the corresponding elements of the two
        # vectors.
        intra_sums = cdist(
            peak_cluster.reshape(-1, 1),
            peak_centroid.reshape(-1, 1),
            metric="sqeuclidean",
        ).sum()

        # Calculate between-cluster sums of point-to-centroid distances
        inter_sums = cdist(
            peak_cluster.reshape(-1, 1),
            noise_centroid.reshape(-1, 1),
            metric="sqeuclidean",
        ).sum()

        # Calculate silhouette coefficient
        sil = (inter_sums - intra_sums) / max(intra_sums, inter_sums)

        return sil

    def get_otb_refsignal(self, df, refsig):
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
                # Extract the performed path (subsampled data)
                REF_SIGNAL_SUBSAMPLED = df.filter(regex="performed path")
                # Check if the REF_SIGNAL is available
                if not REF_SIGNAL_SUBSAMPLED.empty:
                    REF_SIGNAL_SUBSAMPLED = REF_SIGNAL_SUBSAMPLED.rename(
                        columns={REF_SIGNAL_SUBSAMPLED.columns[0]: 0}
                    )
                    # Verify that there is no value above 100% since the
                    # REF_SIGNAL is expected to be expressed as % of the MVC
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
                # Extract the acquired path (raw data)
                REF_SIGNAL_FULLSAMPLED = df.filter(regex="acquired data")
                if not REF_SIGNAL_FULLSAMPLED.empty:
                    REF_SIGNAL_FULLSAMPLED = REF_SIGNAL_FULLSAMPLED.rename(
                        columns={REF_SIGNAL_FULLSAMPLED.columns[0]: 0}
                    )
                    # Verify that there is no value above 100% since the
                    # REF_SIGNAL is expected to be expressed as % of the MVC
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
            warnings.warn("\nNot searched for reference signal, it might be necessary for some analyses\n")

            return pd.DataFrame(columns=[0])


    def get_otb_decomposition(self, df):
        # Extract the IPTS and rename columns progressively
        IPTS = df.filter(regex="Source for decomposition")
        IPTS.columns = np.arange(len(IPTS.columns))
        # Verify to have the IPTS
        if IPTS.empty:
            raise ValueError(
                "\nSource for decomposition (IPTS) not found in the .mat file\n"
            )

        # Extract the BINARY_MUS_FIRING and rename columns progressively
        BINARY_MUS_FIRING = df.filter(regex="Decomposition of")
        BINARY_MUS_FIRING.columns = np.arange(len(BINARY_MUS_FIRING.columns))
        # Verify to have the BINARY_MUS_FIRING
        if BINARY_MUS_FIRING.empty:
            raise ValueError(
                "\nDecomposition of (BINARY_MUS_FIRING) not found in the .mat file\n"
            )

        return IPTS, BINARY_MUS_FIRING


    def get_otb_ied(self, df):
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
            # Check the matrix used in the columns name
            # (in the df obtained from OTBiolab+)
            if matrix in str(df.columns):
                IED = float(OTBelectrodes_ied[matrix])

                return IED

        # If no matrix is found and we exit the loop:
        warnings.warn(
            "OTB recording grid not found, IED could not be inferred"
        )
        return np.nan


    def get_otb_rawsignal(self, df, extras_regex):
        # Drop all the known columns different from the raw EMG signal.
        # This is a workaround since the OTBiolab+ software does not export a
        # unique name for the raw EMG signal.
        base_pattern = "Source for decomposition|Decomposition of|acquired data|performed path"
        if extras_regex is None:
            pattern = base_pattern
        else:
            pattern = base_pattern + "|" + extras_regex

        emg_df = df[df.columns.drop(list(df.filter(regex=pattern)))]

        # Check if the number of remaining columns matches the expected number of
        # matrix channels.
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
            # Check the matrix used in the columns name (in the emg_df) to know
            # the number of expected channels.
            if matrix in str(emg_df.columns):
                expectedchannels = int(OTBelectrodes_Nelectrodes[matrix])
                break
        if expectedchannels is np.nan:
            raise ValueError("Matrix not recognised")
        if len(emg_df.columns) == expectedchannels:
            emg_df.columns = np.arange(len(emg_df.columns))
            RAW_SIGNAL = emg_df
            return RAW_SIGNAL
        else:
            # This check here is usefull to control that only the appropriate
            # elements have been included in the .mat file exported from OTBiolab+.
            raise ValueError(
                "\nFailure in searching the raw signal, please check that it is present in the .mat file and that only the accepted parameters have been included\n"
            )


    def get_otb_extras(self, df, extras):
        if extras is None:
            return pd.DataFrame(columns=[0])
        else:
            EXTRAS = df.filter(regex=extras)
            return EXTRAS
    def mupulses_from_binary(self, binarymusfiring):
        # Create empty list of lists to fill with ndarrays containing the MUPULSES
        # (point of firing)
        numberofMUs = len(binarymusfiring.columns)
        MUPULSES = [[] for _ in range(numberofMUs)]

        for mu in binarymusfiring:  # Loop all the MUs
            my_ndarray = []
            for idx, x in binarymusfiring[mu].items():  # Loop the MU firing times
                if x > 0:
                    my_ndarray.append(idx)
                    # Take the firing time and add it to the ndarray

            MUPULSES[mu] = np.array(my_ndarray)

        return MUPULSES

    def emg_from_otb(self,
    filepath,
    ext_factor=8,
    refsig=[True, "fullsampled"],
    version="1.5.9.3",
    extras=None,
    ignore_negative_ipts=False,
    ):
        mat_file = loadmat(filepath, simplify_cells=True)
        # Check if a valid version has been specified
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
            # Simplify (rename) columns description and extract all the parameters
            # in a pd.DataFrame
            df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])

            # First, get the basic information and compulsory variables (i.e.,
            # RAW_SIGNAL, IPTS, MUPULSES, BINARY_MUS_FIRING) in a pd.DataFrame (df) or
            # list (for matlab cell arrays).

            # Use this to know the data source and name of the file
            SOURCE = "OTB"
            FILENAME = os.path.basename(filepath)
            FSAMP = float(mat_file["SamplingFrequency"])
            IED = self.get_otb_ied(df=df)

            # Get RAW_SIGNAL
            RAW_SIGNAL = self.get_otb_rawsignal(df=df, extras_regex=extras)

            # Get IPTS and BINARY_MUS_FIRING
            IPTS, BINARY_MUS_FIRING = self.get_otb_decomposition(df=df)
            # Align BINARY_MUS_FIRING to IPTS
            BINARY_MUS_FIRING = BINARY_MUS_FIRING.shift(- int(ext_factor))
            BINARY_MUS_FIRING.fillna(value=0, inplace=True)

            # Get MUPULSES
            MUPULSES = self.mupulses_from_binary(binarymusfiring=BINARY_MUS_FIRING)

            # Get EMG_LENGTH and NUMBER_OF_MUS
            EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape

            # Get REF_SIGNAL
            REF_SIGNAL = self.get_otb_refsignal(df=df, refsig=refsig)

            # Estimate ACCURACY (SIL)
            if NUMBER_OF_MUS > 0:
                to_append = []
                for mu in range(NUMBER_OF_MUS):
                    sil = self.compute_sil(
                        ipts=IPTS[mu],
                        mupulses=MUPULSES[mu],
                        ignore_negative_ipts=ignore_negative_ipts,
                    )
                    to_append.append(sil)
                ACCURACY = pd.DataFrame(to_append)

            else:
                ACCURACY = pd.DataFrame(columns=[0])

            # Get EXTRAS
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

        self.file = emgfile
