import os
import shutil
import tarfile
import numpy as np
import xml.etree.ElementTree as ET
from lib.xml2struct import xml2struct
from lib.Quattrodlg import Quattrodlg
import scipy.io as sio


def openOTB4(path, file, dialog):
    # Make new folder
    if os.path.exists("tmpopen"):
        shutil.rmtree("tmpopen")
    os.makedirs("tmpopen")

    # Extract contents of tar file
    with tarfile.open(os.path.join(path, file), "r") as tar:
        tar.extractall("tmpopen")

    signals = [f for f in os.listdir("tmpopen") if f.endswith(".sig")]

    nChannel = [0]
    nCh = np.zeros(len(signals) - 1)
    Fs = np.zeros(len(signals) - 1)
    abstracts = "Tracks_000.xml"
    abs, _, _ = xml2struct(os.path.join(".", "tmpopen", abstracts))
    AUX_index = -1
    EMG_index = np.zeros(len(abs["ArrayOfTrackInfo"]["TrackInfo"]))
    EMG_nchannel = np.zeros(len(abs["ArrayOfTrackInfo"]["TrackInfo"]))
    counter = 1
    AUX_Subtitle = ""

    Gains = []
    nADBit = []
    PowerSupply = []
    Fsample = []
    Path = []
    startIndex = []
    Title = []

    for ntype in range(len(abs["ArrayOfTrackInfo"]["TrackInfo"])):
        device_text = abs["ArrayOfTrackInfo"]["TrackInfo"][0]["Device"]["Text"]
        device = device_text.split(";")[0]

        Gains.append(float(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["Gain"]["Text"]))
        nADBit.append(float(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["ADC_Nbits"]["Text"]))
        PowerSupply.append(float(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["ADC_Range"]["Text"]))
        Fsample.append(float(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["SamplingFrequency"]["Text"]))
        Path.append(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["SignalStreamPath"]["Text"])
        nChannel.append(int(float(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["NumberOfChannels"]["Text"])))
        startIndex.append(float(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["AcquisitionChannel"]["Text"]))
        Title.append(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["Title"]["Text"])

        channels = float(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["NumberOfChannels"]["Text"])

        if channels == 32 or channels == 64:
            for i in range(counter, counter + int(channels)):
                EMG_index[i - 1] = startIndex[-1]  # contains index of connector (adapter)
                EMG_nchannel[i - 1] = channels  # contains n° of channels in that adapter
            counter += int(channels)

        if Title[-1] == "Direct connection to Auxiliary Input":
            AUX_index = startIndex[-1]
            AUX_Subtitle = abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["SubTitle"]["Text"]

        if channels >= 32:
            if "signal" not in locals():
                signal = {"gridname": [], "data": np.array([])}
            signal["gridname"].append(abs["ArrayOfTrackInfo"]["TrackInfo"][0][ntype]["SubTitle"]["Text"])

    TotCh = int(sum(nChannel))

    if device == "Novecento+":
        for i in range(1, len(signals)):
            flag = False
            for j in range(len(Path)):
                if Path[j] == signals[i]:
                    nCh[i - 1] += nChannel[j + 1]
                    Fs[i - 1] = Fsample[j]
                    Psup = PowerSupply[j]
                    ADbit = nADBit[j]
                    Gain = Gains[j]
                    flag = True

            if flag:
                with open(os.path.join("tmpopen", signals[i]), "rb") as h:
                    data = np.fromfile(h, dtype=np.int32).reshape((int(nCh[i - 1]), -1))

                for Ch in range(int(nCh[i - 1])):
                    data[Ch, :] = data[Ch, :] * Psup / (2**ADbit) * 1000 / Gain
    else:
        with open(os.path.join("tmpopen", signals[0]), "rb") as h:
            data = np.fromfile(h, dtype=np.int16).reshape((TotCh, -1))

        sumidx = nChannel[0]
        idx = np.zeros(len(nChannel))
        idx[0] = sumidx
        for i in range(1, len(nChannel)):
            sumidx += nChannel[i]
            idx[i] = sumidx

        for ntype in range(1, len(abs["ArrayOfTrackInfo"]["TrackInfo"]) + 1):
            for nCh in range(int(idx[ntype - 1]) + 1, int(idx[ntype]) + 1):
                data[nCh - 1, :] = (
                    data[nCh - 1, :] * PowerSupply[ntype - 1] / (2 ** nADBit[ntype - 1]) * 1000 / Gains[ntype - 1]
                )

    Gains = np.zeros(TotCh)
    Adapter = np.zeros(TotCh)
    Posdev = np.zeros(TotCh)
    Grid = [""] * TotCh
    Muscle = [""] * TotCh

    # fill the adapter array similarly to the openOTB+ script
    Adapter = np.zeros(TotCh)
    for i in range(len(EMG_index)):
        value = 3  # 32 channels
        if EMG_nchannel[i] == 64:
            value = 4  # 64 channels
        Adapter[i] = value

    signal["data"] = data[(Adapter == 3) | (Adapter == 4), :]
    if AUX_index != -1:
        signal["auxiliary"] = data[int(AUX_index), :]

    if len(data[Adapter < 3, :]) > 0:
        signal["emgnotgrid"] = data[Adapter < 3, :]

    nch = 1
    nch2 = 1
    Grid2 = []
    Muscle2 = []

    for i in range(len(Grid)):
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

    signal["fsamp"] = Fsample[0]
    signal["nChan"] = TotCh
    Posdev = Posdev[(Adapter == 3) | (Adapter == 4)]

    idxa = np.unique(Posdev)
    signal["ngrid"] = len(signal["gridname"])
    signal["muscle"] = [""] * signal["ngrid"]  # Initialize muscle names

    if "QUATTROCENTO" not in device:
        idxa = np.arange(len(idxa)) + 3

    # Check for target files
    target_files = [f for f in os.listdir("tmpopen") if f.endswith(".sip")]

    if target_files:
        with open(os.path.join("tmpopen", target_files[1]), "rb") as h:
            data1 = np.fromfile(h, dtype=np.float64)[: data.shape[1]]
        signal["path"] = data1

        with open(os.path.join("tmpopen", target_files[2]), "rb") as h:
            data2 = np.fromfile(h, dtype=np.float64)[: data.shape[1]]
        signal["target"] = data2

        if "auxiliary" in signal:
            signal["auxiliary"] = np.vstack([signal["auxiliary"], signal["path"], signal["target"]])
            signal["auxiliaryname"] = AUX_Subtitle  # should be appended
        else:
            signal["auxiliary"] = np.vstack([signal["path"], signal["target"]])
            signal["auxiliaryname"] = ["Path", "Target"]

    shutil.rmtree("tmpopen")

    if dialog == 1:
        # Set the configuration
        dlgbox = Quattrodlg()
        dlgbox.edit_field_nchan.setValue(signal["data"].shape[0])

        if 1 in idxa:
            dlgbox.checkbox_S1.setChecked(True)
            dlgbox.checkbox_S1.setVisible(False)
            dlgbox.splitter1_panel.setEnabled(True)
            dlgbox.lamp_S1.set_color("green")
            dlgbox.dropdown_S1.setCurrentText(signal["gridname"][idxa == 1][0])
            dlgbox.edit_field_S1.setText(signal["muscle"][idxa == 1][0])

        if 2 in idxa:
            dlgbox.checkbox_S2.setChecked(True)
            dlgbox.checkbox_S2.setVisible(False)
            dlgbox.splitter2_panel.setEnabled(True)
            dlgbox.lamp_S2.set_color("green")
            dlgbox.dropdown_S2.setCurrentText(signal["gridname"][idxa == 2][0])
            dlgbox.edit_field_S2.setText(signal["muscle"][idxa == 2][0])

        if 3 in idxa:
            dlgbox.checkbox_M1.setChecked(True)
            dlgbox.checkbox_M1.setVisible(False)
            dlgbox.mi1_panel.setEnabled(True)
            dlgbox.lamp_M1.set_color("green")
            dlgbox.dropdown_M1.setCurrentText(signal["gridname"][idxa == 3][0])
            dlgbox.edit_field_M1.setText(signal["muscle"][idxa == 3][0])

        if 4 in idxa:
            dlgbox.checkbox_M2.setChecked(True)
            dlgbox.checkbox_M2.setVisible(False)
            dlgbox.mi2_panel.setEnabled(True)
            dlgbox.lamp_M2.set_color("green")
            dlgbox.dropdown_M2.setCurrentText(signal["gridname"][idxa == 4][0])
            dlgbox.edit_field_M2.setText(signal["muscle"][idxa == 4][0])

        if 5 in idxa:
            dlgbox.checkbox_M3.setChecked(True)
            dlgbox.checkbox_M3.setVisible(False)
            dlgbox.mi3_panel.setEnabled(True)
            dlgbox.lamp_M3.set_color("green")
            dlgbox.dropdown_M3.setCurrentText(signal["gridname"][idxa == 5][0])
            dlgbox.edit_field_M3.setText(signal["muscle"][idxa == 5][0])

        if 6 in idxa:
            dlgbox.checkbox_M4.setChecked(True)
            dlgbox.checkbox_M4.setVisible(False)
            dlgbox.mi4_panel.setEnabled(True)
            dlgbox.lamp_M4.set_color("green")
            dlgbox.dropdown_M4.setCurrentText(signal["gridname"][idxa == 6][0])
            dlgbox.edit_field_M4.setText(signal["muscle"][idxa == 6][0])

        # Create and save a temporary .mat file for the dialog
        savename = os.path.join(path, f"{file}_decomp.mat")
        dlgbox.pathname.setText(savename)
        sio.savemat(savename, {"signal": signal})

        return dlgbox, signal
    else:
        return None, signal
