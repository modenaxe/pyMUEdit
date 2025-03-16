import os
import shutil
import tarfile
import numpy as np
from lib.readXMLotb import readXMLotb
from lib.Quattrodlg import Quattrodlg
import scipy.io as sio


def openOTBplus(path, file, dialog):
    if os.path.exists("tmpopen"):
        shutil.rmtree("tmpopen")
    os.makedirs("tmpopen")

    with tarfile.open(os.path.join(path, file), "r") as tar:
        tar.extractall("tmpopen")

    signals = [f for f in os.listdir("tmpopen") if f.endswith(".sig")]

    PowerSupply = 3.3
    abs, _, _ = readXMLotb(os.path.join(".", "tmpopen", signals[0][:-4] + ".xml"))
    Fsample = float(abs["Device"]["Attributes"]["SampleFrequency"])
    nChannel = int(abs["Device"]["Attributes"]["DeviceTotalChannels"])
    nADBit = int(abs["Device"]["Attributes"]["ad_bits"])

    # Create arrays with exact size to avoid indexing issues
    Gains = np.zeros(nChannel)
    Adapter = np.zeros(nChannel)
    Posdev = np.zeros(nChannel)
    Grid = [""] * nChannel
    Muscle = [""] * nChannel

    for nChild in range(len(abs["Device"]["Channels"]["Adapter"])):
        localGain = float(abs["Device"]["Channels"]["Adapter"][nChild]["Attributes"]["Gain"])
        startIndex = int(abs["Device"]["Channels"]["Adapter"][nChild]["Attributes"]["ChannelStartIndex"])

        Channel = abs["Device"]["Channels"]["Adapter"][nChild]["Channel"]

        for nChan in range(len(Channel) if isinstance(Channel, list) else 1):
            # Check if Channel is a list or dictionary and handle accordingly
            if isinstance(Channel, list):
                current_channel = Channel[nChan]
            else:
                # If it's a single channel (dict), just use it directly
                current_channel = Channel

            ChannelAtt = current_channel["Attributes"]
            Description = ChannelAtt["Description"]
            idx = int(ChannelAtt["Index"])

            # Calculate position with bounds check
            position = startIndex + idx
            if position >= nChannel:
                print(f"Warning: Index {position} out of bounds, skipping channel")
                continue

            if "General" in Description or "iEMG" in Description:
                Adapter[position] = 1
            elif "16" in Description:
                Adapter[position] = 2
            elif "32" in Description:
                Adapter[position] = 3
            elif "64" in Description:
                Adapter[position] = 4
            elif "Splitter" in Description:
                Adapter[position] = 4
            else:
                Adapter[position] = 5

            if "QUATTROCENTO" in abs["Device"]["Attributes"]["Name"]:
                Adpatidx = ChannelAtt["Prefix"]
                if "MULTIPLE IN" in Adpatidx:
                    Posdev[position] = int(Adpatidx[12]) + 2
                elif "IN" in Adpatidx:
                    Posdev[position] = int(Adpatidx[3])
                    if Posdev[position] < 5:
                        Posdev[position] = 1
                    else:
                        Posdev[position] = 2
            else:
                Posdev[position] = int(abs["Device"]["Channels"]["Adapter"][nChild]["Attributes"]["AdapterIndex"])

            Gains[position] = localGain
            Grid[position] = ChannelAtt["ID"]
            Muscle[position] = ChannelAtt["Muscle"]

            # If it's not a list but a single channel, we processed it, so break the loop
            if not isinstance(Channel, list):
                break

    with open(os.path.join("tmpopen", signals[0]), "rb") as h:
        data = np.fromfile(h, dtype=np.int16).reshape((nChannel, -1))

    for nCh in range(nChannel):
        if Gains[nCh] > 0:  # Avoid division by zero
            data[nCh, :] = data[nCh, :] * PowerSupply / (2**nADBit) * 1000 / Gains[nCh]

    signal = {}
    # Create mask for data selection
    mask_data = (Adapter == 3) | (Adapter == 4)
    signal["data"] = data[mask_data, :]

    # Create mask for auxiliary data
    mask_aux = Adapter == 5
    if np.any(mask_aux):
        signal["auxiliary"] = data[mask_aux, :]

    if np.any(Adapter < 3):
        signal["emgnotgrid"] = data[Adapter < 3, :]

    nch = 1
    nch2 = 1
    Grid2 = []
    Muscle2 = []

    for i in range(nChannel):
        if Adapter[i] == 3 or Adapter[i] == 4:
            Grid2.append(Grid[i])
            Muscle2.append(Muscle[i])
            nch += 1
        elif Adapter[i] == 5:
            if "auxiliaryname" not in signal:
                signal["auxiliaryname"] = []
            signal["auxiliaryname"].append(Grid[i])
            nch2 += 1

    Grid = Grid2
    Muscle = Muscle2

    signal["fsamp"] = Fsample
    signal["nChan"] = nChannel

    # Extract Posdev values for grid data using the same mask as data extraction
    grid_posdev = Posdev[mask_data]

    idxa = np.unique(grid_posdev[grid_posdev > 0])  # Filter out zero values
    idxb = np.unique([m for m in Muscle if m])  # Filter out empty strings

    if len(idxa) >= len(idxb) and len(idxa) > 0:
        signal["ngrid"] = len(idxa)
        signal["gridname"] = [""] * signal["ngrid"]
        signal["muscle"] = [""] * signal["ngrid"]

        for i in range(signal["ngrid"]):
            idx_matches = np.where(grid_posdev == idxa[i])[0]
            if len(idx_matches) > 0:
                idx = idx_matches[0]
                if idx < len(Grid):
                    signal["gridname"][i] = Grid[idx]
                if idx < len(Muscle):
                    signal["muscle"][i] = Muscle[idx]

        if "QUATTROCENTO" not in abs["Device"]["Attributes"]["Name"]:
            idxa = np.arange(len(idxa)) + 3
    elif len(idxb) > 0:
        signal["ngrid"] = len(idxb)
        signal["gridname"] = [""] * signal["ngrid"]
        signal["muscle"] = [""] * signal["ngrid"]

        for i in range(signal["ngrid"]):
            idx = [j for j, m in enumerate(Muscle2) if m == idxb[i]]
            if idx:  # Make sure the list is not empty
                signal["gridname"][i] = Grid[idx[0]]
                signal["muscle"][i] = Muscle[idx[0]]
    else:
        # No valid grid or muscle names found
        signal["ngrid"] = 1
        signal["gridname"] = ["Unknown"]
        signal["muscle"] = ["Unknown"]

    # Check for target files
    target_files = [f for f in os.listdir("tmpopen") if f.endswith(".sip")]

    if target_files and len(target_files) >= 3:
        try:
            with open(os.path.join("tmpopen", target_files[1]), "rb") as h:
                data1 = np.fromfile(h, dtype=np.float64)
                # Ensure data1 is the same length as the EMG data
                if len(data1) >= data.shape[1]:
                    data1 = data1[: data.shape[1]]
                else:
                    # Pad with zeros if necessary
                    data1 = np.pad(data1, (0, data.shape[1] - len(data1)))
                signal["path"] = data1

            with open(os.path.join("tmpopen", target_files[2]), "rb") as h:
                data2 = np.fromfile(h, dtype=np.float64)
                # Ensure data2 is the same length as the EMG data
                if len(data2) >= data.shape[1]:
                    data2 = data2[: data.shape[1]]
                else:
                    # Pad with zeros if necessary
                    data2 = np.pad(data2, (0, data.shape[1] - len(data2)))
                signal["target"] = data2

            if "auxiliary" in signal and signal["auxiliary"].size > 0:
                # Ensure auxiliary data has at least one row
                if len(signal["auxiliary"].shape) == 1:
                    signal["auxiliary"] = signal["auxiliary"].reshape(1, -1)

                # Create stacked array
                signal["auxiliary"] = np.vstack([signal["auxiliary"], signal["path"], signal["target"]])

                # Add auxiliary names
                if isinstance(signal["auxiliaryname"], list):
                    signal["auxiliaryname"].extend(["Path", "Target"])
                else:
                    signal["auxiliaryname"] = ["Path", "Target"]
            else:
                signal["auxiliary"] = np.vstack([signal["path"].reshape(1, -1), signal["target"].reshape(1, -1)])
                signal["auxiliaryname"] = ["Path", "Target"]
        except Exception as e:
            print(f"Error processing target files: {e}")

    try:
        shutil.rmtree("tmpopen")
    except Exception as e:
        print(f"Error removing temporary directory: {e}")

    if dialog == 1:
        # Set the configuration
        dlgbox = Quattrodlg()
        if signal["data"].size > 0:
            dlgbox.edit_field_nchan.setValue(signal["data"].shape[0])

        # Handle the configuration UI safely
        for port_num, port_elements in [
            (1, (dlgbox.checkbox_S1, dlgbox.splitter1_panel, dlgbox.lamp_S1, dlgbox.dropdown_S1, dlgbox.edit_field_S1)),
            (2, (dlgbox.checkbox_S2, dlgbox.splitter2_panel, dlgbox.lamp_S2, dlgbox.dropdown_S2, dlgbox.edit_field_S2)),
            (3, (dlgbox.checkbox_M1, dlgbox.mi1_panel, dlgbox.lamp_M1, dlgbox.dropdown_M1, dlgbox.edit_field_M1)),
            (4, (dlgbox.checkbox_M2, dlgbox.mi2_panel, dlgbox.lamp_M2, dlgbox.dropdown_M2, dlgbox.edit_field_M2)),
            (5, (dlgbox.checkbox_M3, dlgbox.mi3_panel, dlgbox.lamp_M3, dlgbox.dropdown_M3, dlgbox.edit_field_M3)),
            (6, (dlgbox.checkbox_M4, dlgbox.mi4_panel, dlgbox.lamp_M4, dlgbox.dropdown_M4, dlgbox.edit_field_M4)),
        ]:
            try:
                if port_num in idxa:
                    checkbox, panel, lamp, dropdown, edit_field = port_elements
                    checkbox.setChecked(True)
                    checkbox.setVisible(False)
                    panel.setEnabled(True)
                    lamp.set_color("green")

                    # Find the index for this port in the signal arrays
                    port_index = np.where(idxa == port_num)[0]
                    if len(port_index) > 0 and port_index[0] < len(signal["gridname"]):
                        dropdown.setCurrentText(signal["gridname"][port_index[0]])
                        edit_field.setText(signal["muscle"][port_index[0]])
            except Exception as e:
                print(f"Error setting up port {port_num}: {e}")

        # Create and save a temporary .mat file for the dialog
        savename = os.path.join(path, f"{file}_decomp.mat")
        dlgbox.pathname.setText(savename)
        try:
            sio.savemat(savename, {"signal": signal})
        except Exception as e:
            print(f"Error saving .mat file: {e}")

        return dlgbox, signal
    else:
        return None, signal
