import os
import shutil
import tarfile
import numpy as np
from utils.config_and_input.readXMLotb import readXMLotb
from utils.config_and_input.Quattrodlg import Quattrodlg


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

    # Parse channel information
    for nChild in range(len(abs["Device"]["Channels"]["Adapter"])):
        localGain = float(abs["Device"]["Channels"]["Adapter"][nChild]["Attributes"]["Gain"])
        startIndex = int(abs["Device"]["Channels"]["Adapter"][nChild]["Attributes"]["ChannelStartIndex"])

        Channel = abs["Device"]["Channels"]["Adapter"][nChild]["Channel"]

        for nChan in range(len(Channel) if isinstance(Channel, list) else 1):
            if isinstance(Channel, list):
                current_channel = Channel[nChan]
            else:
                current_channel = Channel

            ChannelAtt = current_channel["Attributes"]
            Description = ChannelAtt["Description"]
            idx = int(ChannelAtt["Index"])

            # Calculate position - adjust to match MATLAB indexing
            position = startIndex + idx + 1
            if position > nChannel:
                print(f"Warning: Index {position} out of bounds, skipping channel")
                continue

            # Determine adapter type based on description
            if "General" in Description or "iEMG" in Description:
                Adapter[position - 1] = 1
            elif "16" in Description:
                Adapter[position - 1] = 2
            elif "32" in Description:
                Adapter[position - 1] = 3
            elif "64" in Description:
                Adapter[position - 1] = 4
            elif "Splitter" in Description:
                Adapter[position - 1] = 4
            else:
                Adapter[position - 1] = 5

            # Determine device position
            if "QUATTROCENTO" in abs["Device"]["Attributes"]["Name"]:
                Adpatidx = ChannelAtt["Prefix"]
                if "MULTIPLE IN" in Adpatidx:
                    Posdev[position - 1] = int(Adpatidx[12]) + 2
                elif "IN" in Adpatidx:
                    Posdev[position - 1] = int(Adpatidx[3])
                    if Posdev[position - 1] < 5:
                        Posdev[position - 1] = 1
                    else:
                        Posdev[position - 1] = 2
            else:
                Posdev[position - 1] = int(abs["Device"]["Channels"]["Adapter"][nChild]["Attributes"]["AdapterIndex"])

            Gains[position - 1] = localGain
            Grid[position - 1] = ChannelAtt["ID"]
            Muscle[position - 1] = ChannelAtt["Muscle"]

            if not isinstance(Channel, list):
                break

    # Read the actual signal data
    try:
        with open(os.path.join("tmpopen", signals[0]), "rb") as h:
            raw_data = np.fromfile(h, dtype=np.int16)

            # Reshape using Fortran order to match MATLAB's fread(h,[nChannel Inf], 'short')
            data = raw_data.reshape((nChannel, -1), order="F")
    except Exception as e:
        print(f"Error reading signal file: {e}")
        data = np.zeros((nChannel, 1000))

    data_converted = np.zeros_like(data, dtype=np.float64)  # Use float64 to match MATLAB
    for nCh in range(nChannel):
        if Gains[nCh] > 0:  # Avoid division by zero
            data_converted[nCh, :] = data[nCh, :] * PowerSupply / (2**nADBit) * 1000 / Gains[nCh]

    signal = {}

    # Create mask for data selection
    mask_data = (Adapter == 3) | (Adapter == 4)
    signal["data"] = data_converted[mask_data, :]

    # Create mask for auxiliary data
    mask_aux = Adapter == 5
    if np.any(mask_aux):
        signal["auxiliary"] = data_converted[mask_aux, :]

    if np.any(Adapter < 3):
        signal["emgnotgrid"] = data_converted[Adapter < 3, :]

    # Process grid and muscle names
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

    # Store sampling rate and channel count
    signal["fsamp"] = Fsample
    signal["nChan"] = nChannel

    # Extract Posdev values for grid data using the same mask as data extraction
    grid_posdev = Posdev[mask_data]

    # Process grid information
    idxa = np.unique(grid_posdev[grid_posdev > 0])
    idxb = np.unique([m for m in Muscle if m])

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
                if len(data1) >= data_converted.shape[1]:
                    data1 = data1[: data_converted.shape[1]]
                else:
                    data1 = np.pad(data1, (0, data_converted.shape[1] - len(data1)))
                signal["path"] = data1

            with open(os.path.join("tmpopen", target_files[2]), "rb") as h:
                data2 = np.fromfile(h, dtype=np.float64)
                # Ensure data2 is the same length as the EMG data
                if len(data2) >= data_converted.shape[1]:
                    data2 = data2[: data_converted.shape[1]]
                else:
                    data2 = np.pad(data2, (0, data_converted.shape[1] - len(data2)))
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
        dlgbox = Quattrodlg()
        savename = os.path.join(path, f"{file}_decomp.mat")
        dlgbox.pathname.setText(savename)

        # Set channel count
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

                    # Find the correct index for this port
                    port_index = np.where(idxa == port_num)[0]
                    if len(port_index) > 0 and port_index[0] < len(signal["gridname"]):
                        idx = port_index[0]
                        dropdown.setCurrentText(signal["gridname"][idx])
                        edit_field.setText(signal["muscle"][idx])
            except Exception as e:
                print(f"Error setting up port {port_num}: {e}")

        return dlgbox, signal, savename
    else:
        return None, signal, None
