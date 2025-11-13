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
import core.logger as logger

class CommonOpenFunc():
    
    """Holds commonly used functions from openHDEMG"""

    def __init__(self):
        pass
    
    def compute_idr(self, emgfile):
        """From openHDEMG computes IDR
        Params (relevant for us): file
        Returns: idr
        """
        try:
            if isinstance(emgfile["MUPULSES"], list):
                idr = {x: np.nan**2 for x in range(emgfile["NUMBER_OF_MUS"])}
                for mu in range(emgfile["NUMBER_OF_MUS"]):
                    df = pd.DataFrame(
                        emgfile["MUPULSES"][mu]
                        if emgfile["NUMBER_OF_MUS"] > 1
                        else np.transpose(np.array(emgfile["MUPULSES"]))
                    )
                    df[1] = df[0].diff()
                    df[2] = df[0] / emgfile["FSAMP"]
                    df[3] = emgfile["FSAMP"] / df[1]
                    df = df.rename(
                        columns={
                            0: "mupulses",
                            1: "diff_mupulses",
                            2: "timesec",
                            3: "idr",
                        },
                    )
                    idr[mu] = df
                return idr
            else:
                raise ValueError(
                    "MUPULSES is probably absent or it is not contained in a list"
                )
        except Exception as e:
            logger.exception("Failed to compute IDR for EMG file")
            raise

    def min_max_scaling(self, data=None, series_or_df=None, col_by_col=False):
        """From openHDEMG normalises given data
        Params (relevant for us): None
        Returns: idr
        """
        if data is not None:
            data = copy.deepcopy(data)
        elif series_or_df is not None:
            data = copy.deepcopy(series_or_df)
            msg = (
                "The 'series_or_df' parameter is deprecated since v0.1.1 and " +
                "will be removed after v0.2.0. Please use 'data' instead."
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
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
                if len(data.shape) == 1:
                    data = (data - data.min()) / (data.max() - data.min())
                    return data
                elif len(data.shape) == 2:
                    dims = any(d == 0 or d == 1 for d in data.shape)
                    if dims:
                        data = (data - data.min()) / (data.max() - data.min())
                    else:
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
            logger.error("data must be one of pd.series, pd.dataframe or np.ndarray. " +
                f"{type(data)} was passed instead.")
            
    def compute_sil(self, ipts, mupulses, ignore_negative_ipts=False):
        """From openHDEMG computes sil
        Params (relevant for us): None
        Returns: idr
        """
        if len(mupulses) == 0:
            return np.nan
        source = ipts.to_numpy()
        if ignore_negative_ipts:
            source = source * np.abs(source)
        peaks_idxs = mupulses - ipts.index[0]
        peak_cluster = source[peaks_idxs]
        noise_cluster = np.delete(source, peaks_idxs)
        peak_centroid = np.mean(peak_cluster)
        noise_centroid = np.mean(noise_cluster)
        intra_sums = cdist(
            peak_cluster.reshape(-1, 1),
            peak_centroid.reshape(-1, 1),
            metric="sqeuclidean",
        ).sum()
        inter_sums = cdist(
            peak_cluster.reshape(-1, 1),
            noise_centroid.reshape(-1, 1),
            metric="sqeuclidean",
        ).sum()
        sil = (inter_sums - intra_sums) / max(intra_sums, inter_sums)
        return sil
