import os
import json
import numpy as np
import scipy.io as sio
from lib.readNPY import readNPY


def openOEphys(path, file, dialog):
    """Load EMG signals recorded with the Open Ephys GUI"""

    # Create a session (loads all data from the most recent recording)
    with open(os.path.join(path, file), "r") as f:
        info = json.load(f)

    # Get the path with the data
    directory = os.path.join(path, "continuous", info["continuous"]["folder_name"])

    signal = {}
    signal["fsamp"] = info["continuous"]["sample_rate"]
    signal["nChan"] = info["continuous"]["num_channels"]

    name = []
    sigtype = np.zeros(signal["nChan"])

    for i in range(signal["nChan"]):
        name.append(info["continuous"]["channels"][i]["channel_name"])
        if "CH" in name[i]:
            sigtype[i] = 1
        elif "ADC" in name[i]:
            sigtype[i] = 2

    time = readNPY(os.path.join(directory, "timestamps.npy"))
    num_samples = readNPY(os.path.join(directory, "sample_numbers.npy"))

    # Memory map the continuous data file
    data_file = os.path.join(directory, "continuous.dat")
    file_size = os.path.getsize(data_file)
    num_data_points = file_size // 2  # int16 = 2 bytes

    with open(data_file, "rb") as f:
        raw_data = np.fromfile(f, dtype=np.int16)

    samples = raw_data.reshape((signal["nChan"], -1))

    # Apply bit_volts conversion
    for i in range(signal["nChan"]):
        samples[i, :] = samples[i, :] * info["continuous"]["channels"][i]["bit_volts"]

    signal["data"] = samples[sigtype == 1, :]
    signal["auxiliary"] = samples[sigtype == 2, :]

    idx = np.where(sigtype == 2)[0]
    signal["auxiliaryname"] = []

    for i in range(len(idx)):
        signal["auxiliaryname"].append(name[idx[i]])

    if dialog == 1:
        from OEphysdlg import OEphysdlg

        dlgbox = OEphysdlg()
        dlgbox.edit_field_nchan.setValue(signal["data"].shape[0])
        dlgbox.edit_field_Ain.setValue(signal["auxiliary"].shape[0])
        dlgbox.edit_field_Din.setValue(0)

        # Create and save a temporary .mat file for the dialog
        savename = os.path.join(path, f"{file}_decomp.mat")
        dlgbox.pathname.setText(savename)
        sio.savemat(savename, {"signal": signal})

        return dlgbox, signal
    else:
        return None, signal
