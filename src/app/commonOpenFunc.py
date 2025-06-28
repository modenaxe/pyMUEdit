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

class OpenFunct():
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