import os
import numpy as np
import scipy.io as sio
from lib.read_Intan_RHD_MUedit import read_Intan_RHD_MUedit


def openIntan(path, file, dialog):
    # Step 1: Get the configuration of the Intan board
    amplifier_channels, board_adc_channels, board_dig_in_channels, frequency_parameters = read_Intan_RHD_MUedit(
        path, file
    )

    # Step 2: Timestamp
    filetime = os.stat(os.path.join(path, "time.dat"))
    num_samples = filetime.st_size // 4  # int32 = 4 bytes
    with open(os.path.join(path, "time.dat"), "rb") as fid:
        time = np.fromfile(fid, dtype=np.int32, count=num_samples)

    time = time / frequency_parameters["amplifier_sample_rate"]  # sample rate from header file

    # Step 3: Import the data
    # amplifier channels
    signal = {}
    signal["data"] = np.zeros((len(amplifier_channels), num_samples))

    for i in range(len(amplifier_channels)):
        filename = None
        for file in os.listdir(path):
            if amplifier_channels[i]["native_channel_name"] in file:
                filename = file
                break

        if filename:
            file_stats = os.stat(os.path.join(path, filename))
            num_samples_file = file_stats.st_size // 2  # int16 = 2 bytes
            with open(os.path.join(path, filename), "rb") as fid:
                v = np.fromfile(fid, dtype=np.int16, count=num_samples_file)

            signal["data"][i, :] = v * 0.195  # convert to microvolts

    # analog inputs
    ch = 0
    signal["auxiliary"] = np.zeros((len(board_adc_channels) + len(board_dig_in_channels), num_samples))
    signal["auxiliaryname"] = [""] * (len(board_adc_channels) + len(board_dig_in_channels))

    for i in range(len(board_adc_channels)):
        filename = None
        for file in os.listdir(path):
            if board_adc_channels[i]["native_channel_name"] in file:
                filename = file
                break

        if filename:
            file_stats = os.stat(os.path.join(path, filename))
            num_samples_file = file_stats.st_size // 2  # int16 = 2 bytes
            with open(os.path.join(path, filename), "rb") as fid:
                v = np.fromfile(fid, dtype=np.uint16, count=num_samples_file)

            signal["auxiliary"][ch, :] = v
            signal["auxiliaryname"][ch] = board_adc_channels[i]["custom_channel_name"]
            ch += 1

    # digital inputs
    for i in range(len(board_dig_in_channels)):
        filename = None
        for file in os.listdir(path):
            if board_dig_in_channels[i]["native_channel_name"] in file:
                filename = file
                break

        if filename:
            file_stats = os.stat(os.path.join(path, filename))
            num_samples_file = file_stats.st_size // 2  # int16 = 2 bytes
            with open(os.path.join(path, filename), "rb") as fid:
                v = np.fromfile(fid, dtype=np.uint16, count=num_samples_file)

            signal["auxiliary"][ch, :] = v
            signal["auxiliaryname"][ch] = board_dig_in_channels[i]["custom_channel_name"]
            ch += 1

    # Step 4 Reorganize the structure for MUedit
    signal["fsamp"] = frequency_parameters["amplifier_sample_rate"]

    port_prefixes = [channel["port_prefix"] for channel in amplifier_channels]
    unique_ports = list(set(port_prefixes))
    signal["ngrid"] = len(unique_ports)

    posgrid = np.zeros(len(amplifier_channels))
    for i, port in enumerate(unique_ports):
        idxchan = [j for j, prefix in enumerate(port_prefixes) if prefix == port]
        if len(idxchan) < 16:
            posgrid[idxchan] = 0
            unique_ports[i] = ""
        else:
            posgrid[idxchan] = 1

    signal["emgnotgrid"] = signal["data"][posgrid == 0, :]
    signal["data"] = signal["data"][posgrid == 1, :]
    signal["nChan"] = signal["data"].shape[0]

    # Filter out empty ports
    ports = [port for port in unique_ports if port]

    if dialog == 1:
        from Intandlg import Intandlg

        dlgbox = Intandlg()
        dlgbox.edit_field_nchan.setValue(signal["nChan"])
        dlgbox.edit_field_Ain.setValue(len(board_adc_channels))
        dlgbox.edit_field_Din.setValue(len(board_dig_in_channels))

        if "A" in ports:
            dlgbox.lamp_A1.set_color("green")
            dlgbox.port_A1_panel.setEnabled(True)
            dlgbox.checkbox_A1.setChecked(True)
            dlgbox.checkbox_A1.setVisible(False)

        if "B" in ports:
            dlgbox.lamp_B1.set_color("green")
            dlgbox.port_B1_panel.setEnabled(True)
            dlgbox.checkbox_B1.setChecked(True)
            dlgbox.checkbox_B1.setVisible(False)

        if "C" in ports:
            dlgbox.lamp_C1.set_color("green")
            dlgbox.port_C1_panel.setEnabled(True)
            dlgbox.checkbox_C1.setChecked(True)
            dlgbox.checkbox_C1.setVisible(False)

        if "D" in ports:
            dlgbox.lamp_D1.set_color("green")
            dlgbox.port_D1_panel.setEnabled(True)
            dlgbox.checkbox_D1.setChecked(True)
            dlgbox.checkbox_D1.setVisible(False)

        # Create and save a temporary .mat file for the dialog
        savename = os.path.join(path, f"{file}_decomp.mat")
        dlgbox.pathname.setText(savename)
        sio.savemat(savename, {"signal": signal})

        return dlgbox, signal
    else:
        return None, signal
