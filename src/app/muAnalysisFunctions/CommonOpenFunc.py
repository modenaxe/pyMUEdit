import sys
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox
)
from scipy.io import loadmat
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
import warnings
import os
import copy
import itertools

# class to hold any open functions that are being repeated
class CommonOpenFunc():
    
    """Holds commonly used functions from openHDEMG"""

    def __init__(self):
        pass
    
    # OPENHDEMG
    def compute_idr(self, emgfile):
        # Compute the instantaneous discharge rate (IDR) from the MUPULSES
        if isinstance(emgfile["MUPULSES"], list):
            # Empty dict to fill with dataframes containing the MUPULSES
            # information
            idr = {x: np.nan**2 for x in range(emgfile["NUMBER_OF_MUS"])}
            for mu in range(emgfile["NUMBER_OF_MUS"]):
                # Manage the exception of a single MU and add MUPULSES in column 0
                df = pd.DataFrame(
                    emgfile["MUPULSES"][mu]
                    if emgfile["NUMBER_OF_MUS"] > 1
                    else np.transpose(np.array(emgfile["MUPULSES"]))
                )
                # Calculate difference in MUPULSES and add it in column 1
                df[1] = df[0].diff()
                # Calculate time in seconds and add it in column 2
                df[2] = df[0] / emgfile["FSAMP"]
                # Calculate the idr and add it in column 3
                df[3] = emgfile["FSAMP"] / df[1]
                df = df.rename(
                    columns={
                        0: "mupulses",
                        1: "diff_mupulses",
                        2: "timesec",
                        3: "idr",
                    },
                )
                # Add the idr to the idr dict
                idr[mu] = df
            return idr
        else:
            raise Exception(
                "MUPULSES is probably absent or it is not contained in a list"
            )

    #OPENHDEMG
    def min_max_scaling(self, data=None, series_or_df=None, col_by_col=False):
        # Create a deepcopy of the original data
        if data is not None:
            data = copy.deepcopy(data)

        elif series_or_df is not None:
            data = copy.deepcopy(series_or_df)

            # Warn for the use of deprecated parameters
            msg = (
                "The 'series_or_df' parameter is deprecated since v0.1.1 and " +
                "will be removed after v0.2.0. Please use 'data' instead."
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=2)

        # Automatically act depending on the data received
        if isinstance(data, pd.Series):
            data = (data - data.min()) / (data.max() - data.min())

            return data

        elif isinstance(data, pd.DataFrame):
            if col_by_col:
                for col in data.columns:
                    data[col] = (
                        (data[col] - data[col].min()) /
                        (data[col].max() - data[col].min())
                    )

                return data

            else:
                data = (
                    (data - data.min().min()) /
                    (data.max().max() - data.min().min())
                )

                return data

        elif isinstance(data, np.ndarray):
            if col_by_col:
                # Check if data is 1D 2D or nD and act accordingly
                if len(data.shape) == 1:
                    data = (data - data.min()) / (data.max() - data.min())

                    return data

                elif len(data.shape) == 2:
                    dims = any(d == 0 or d == 1 for d in data.shape)
                    if dims:  # Only 1 column
                        data = (data - data.min()) / (data.max() - data.min())
                    else:  # Multiple columns
                        for col in range(data.shape[1]):
                            data[:, col] = (
                                (data[:, col] - data[:, col].min()) /
                                (data[:, col].max() - data[:, col].min())
                            )

                    return data

                elif len(data.shape) > 2:
                    raise ValueError(
                        "col_by_col is supported only for 1 and 2D arrays. Set " +
                        "col_by_col=False to normalise the whole data instead."
                    )

            else:
                data = (data - data.min()) / (data.max() - data.min())

                return data

        else:
            raise TypeError(
                "data must be one of pd.series, pd.dataframe or np.ndarray. " +
                f"{type(data)} was passed instead."
            )
            
