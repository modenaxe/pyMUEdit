import glob
import os
import tarfile as tf
import xml.etree.ElementTree as ET
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

import numpy as np

from ui.components.ConfigurationPanel import ConfigurationPanel

if TYPE_CHECKING:
    from app.ImportDataWindow import ImportDataWindow

POWER_SUPPLY = 3.3  # volts, I assume?

# The kinds of channels MUedit distinguishes between.

# EMG data which is not part of a grid (or which is part of a grid that's too
# small - grids with 16 channels get lumped in here too).
NON_GRID_CHANNEL = 1
# EMG data which is part of a grid.
GRID_CHANNEL_16 = 2
GRID_CHANNEL_32 = 3
GRID_CHANNEL_64 = 4
# Auxiliary data, e.g. force exerted by muscles.
AUXILIARY_CHANNEL = 5


def open_otb_plus(inputfile: str, import_window: "ImportDataWindow | None" = None) -> dict[str, Any]:
    """
    Opens OTB file and extracts data.
    Moved from offline_EMG class to a standalone function.

    Args:
        inputfile: Path to the input OTB file
    """
    print(inputfile)
    with TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")

        # Open the .tar file and extract all data
        print("Extracting OTB archive...")
        with tf.open(inputfile, "r") as emg_tar:
            emg_tar.extractall(temp_dir)
        print("Extraction complete")

        sig_files = [f for f in os.listdir(temp_dir) if f.endswith(".sig")]
        print(f"Found {len(sig_files)} signal files: {sig_files}")
        # only one .sig so can be used to get the trial name (0 index list->string)
        trial_label_sig = sig_files[0]
        trial_label_xml = trial_label_sig.rsplit(".", maxsplit=1)[0] + ".xml"
        trial_label_sig = os.path.join(temp_dir, trial_label_sig)
        trial_label_xml = os.path.join(temp_dir, trial_label_xml)
        print(f"Using signal file: {trial_label_sig}")
        print(f"Using XML file: {trial_label_xml}")

        # read the contents of the trial xml file
        print("Parsing XML configuration...")
        with open(trial_label_xml, encoding="utf-8") as file:
            xml = ET.fromstring(file.read())

        # get sampling frequency, no. bits of AD converter, no. channels, electrode names and muscle names
        fsamp = int(xml.attrib["SampleFrequency"])
        nADbit = int(xml.attrib["ad_bits"])
        nchans = int(xml.attrib["DeviceTotalChannels"])

        # The gain of each channel's adapter.
        chan_gains = np.zeros(nchans)
        # What kind of channel each channel is.
        chan_kinds = np.zeros(nchans, dtype=np.uint8)
        # The index of the adapter each channel is connected via.
        chan_adapters = np.zeros(nchans, dtype=np.uint64)
        # Which grid each channel is a part of.
        chan_names: list[str | None] = [None] * nchans
        # Which muscle each channel is measuring.
        chan_muscles: list[str | None] = [None] * nchans

        channels_element = xml.find("./Channels")
        if channels_element is None:
            raise ValueError("Could not find Channels element in XML file")

        for adapter in channels_element:
            adapter_gain = float(adapter.attrib["Gain"])
            start_index = int(adapter.attrib["ChannelStartIndex"])

            # Logic taken from MUedit
            for channel in adapter:
                index = start_index + int(channel.attrib["Index"])
                description = channel.attrib["Description"]
                if "General" in description or "iEMG" in description:
                    chan_kinds[index] = NON_GRID_CHANNEL
                elif "16" in description:
                    chan_kinds[index] = GRID_CHANNEL_16
                elif "32" in description:
                    chan_kinds[index] = GRID_CHANNEL_32
                elif "64" in description or "Splitter" in description:
                    chan_kinds[index] = GRID_CHANNEL_64
                else:
                    chan_kinds[index] = AUXILIARY_CHANNEL

                if "QUATTROCENTO" in xml.attrib["Name"]:
                    prefix = channel.attrib["Prefix"]
                    if "MULTIPLE IN" in prefix:
                        # ew...
                        chan_adapters[index] = int(prefix[12:13]) + 2
                    elif "IN" in prefix:
                        raw_index = int(prefix[3:4])
                        # This will assign the same index to multiple adapters with our data...
                        if raw_index < 5:
                            chan_adapters[index] = 1
                        else:
                            chan_adapters[index] = 2
                else:
                    chan_adapters[index] = int(adapter.attrib["AdapterIndex"])

                # TODO: should we be taking `channel.attrib["Gain"]` into account here? MUedit
                # doesn't.
                chan_gains[index] = adapter_gain
                chan_names[index] = channel.attrib["ID"]
                chan_muscles[index] = channel.attrib["Muscle"]

        print(f"Parsed XML: fsamp={fsamp}Hz, nADbit={nADbit}, nchans={nchans}")

        # read in the EMG trial data
        print("Reading EMG data...")
        with open(trial_label_sig) as f:
            emg_data = np.fromfile(f, dtype="int" + str(nADbit))

        # need to reshape because it is read as a stream
        emg_data = np.transpose(emg_data.reshape(len(emg_data) // nchans, nchans))
        # needed otherwise you just get an integer from the bits to microvolt division
        emg_data = emg_data.astype(float)
        print(f"EMG data shape: {emg_data.shape}")

        # convert the data from bits to microvolts
        print("Converting data from bits to microvolts...")
        for i in range(nchans):
            # Doing it this way instead of combining the two divisions into one is a bit
            # silly, but means we can get our results to match MUedit's _exactly_.
            emg_data[i] = (
                emg_data[i] * POWER_SUPPLY / (2 ** float(nADbit)) * 1000 / chan_gains[i]
            )
        print("Conversion complete")

        # get signal data components
        grid_data = emg_data[(chan_kinds == GRID_CHANNEL_32) | (chan_kinds == GRID_CHANNEL_64)]
        non_grid_data = emg_data[chan_kinds < GRID_CHANNEL_32]
        auxiliary_data = emg_data[chan_kinds == AUXILIARY_CHANNEL]

        chan_names_2 = []
        chan_muscles_2 = []
        auxiliary_names = []
        # grid and muscle labelling
        for i, grid in enumerate(chan_names):
            if chan_kinds[i] == GRID_CHANNEL_32 or chan_kinds[i] == GRID_CHANNEL_64:
                chan_names_2.append(grid)
                chan_muscles_2.append(chan_muscles[i])
            elif chan_kinds[i] == AUXILIARY_CHANNEL:
                auxiliary_names.append(grid)

        chan_names = chan_names_2
        chan_muscles = chan_muscles_2
        chan_adapters = chan_adapters[(chan_kinds == GRID_CHANNEL_32) | (chan_kinds == GRID_CHANNEL_64)]

        # The sets of adapters and muscles which are connected to / measured by grids.
        grid_adapter_set = sorted(set(chan_adapters))
        grid_muscle_set = sorted(set(chan_muscles))

        # The name of each grid.
        grid_names = []
        # The muscle measured by each grid.
        grid_muscles = []
        if len(grid_adapter_set) >= len(grid_muscle_set):
            ngrids = len(grid_adapter_set)
            for i, adapter in enumerate(grid_adapter_set):
                chan_index = next(
                    i
                    for i, other_adapter in enumerate(chan_adapters)
                    if other_adapter == adapter
                )
                grid_names.append(chan_names[chan_index])
                grid_muscles.append(chan_muscles[chan_index])
        else:
            ngrids = len(grid_muscle_set)
            for muscle in grid_muscle_set:
                chan_index = next(
                    i
                    for i, other_muscle in enumerate(chan_muscles)
                    if other_muscle == muscle
                )
                grid_names.append(chan_names[chan_index])
                grid_muscles.append(chan_muscles[chan_index])

        # if the signals were recorded with a feedback generated by OTBiolab+, get the
        # target and the path performed by the participant
        sip_files = glob.glob(f"{temp_dir}/*.sip")
        print(f"Found {len(sip_files)} SIP files: {sip_files}")
        if len(sip_files) != 0:
            print("Reference signals exist, loading target and path data...")
            # only opening the last two .sip files because the first is not needed for analysis
            # would only need MSE between the participant path (file 2) and the target path (file 3)
            _, path_label, target_label = sorted(sip_files)

            ######## path #########
            with open(path_label) as file:
                path = np.fromfile(file, dtype="float64")
                path = path[: np.shape(emg_data)[1]]
            print(f"Path data loaded, shape: {path.shape}")

            ######## target ########
            with open(target_label) as file:
                target = np.fromfile(file, dtype="float64")
                target = target[: np.shape(emg_data)[1]]
            print(f"Target data loaded, shape: {target.shape}")

            auxiliary_data = np.vstack((auxiliary_data, path, target))
            auxiliary_names.extend(("Path", "Target"))
        else:
            path = None
            target = None

    # create a dictionary containing all relevant signal parameters and data
    emg_obj = {
        "data": grid_data,
        "auxiliary": auxiliary_data,
        "emgnotgrid": non_grid_data,
        "auxiliaryname": auxiliary_names,
        "fsamp": fsamp,
        "nChan": nchans,
        "ngrid": ngrids,
        "gridname": grid_names,
        "muscle": grid_muscles,
        "path": path,
        "target": target,
    }  # discard the other muscle and grid entries, not relevant

    if import_window:
        # set the configuration (in the configuration panel)
        import_window.config_panel = set_configuration(emg_obj, grid_adapter_set, grid_names, grid_muscles)

    return emg_obj

def set_configuration(emg_obj, grid_adapter_set, gridname, muscle):
    config_panel = ConfigurationPanel(emg_obj)

    # enable splitter 1 (and fill in data)
    if 1 in grid_adapter_set:
        i = grid_adapter_set.index(1)
        config_panel.splitter1.checkbox.setChecked(True)
        config_panel.splitter1.checkbox.setVisible(False)
        config_panel.splitter1.enable_panel()
        config_panel.splitter1.gridname_dropdown.dropdown.setCurrentText(gridname[i])
        config_panel.splitter1.muscle_input.input.setText(muscle[i])

    # enable splitter 2 (and fill in data)
    if 2 in grid_adapter_set:
        i = grid_adapter_set.index(2)
        config_panel.splitter2.checkbox.setChecked(True)
        config_panel.splitter2.checkbox.setVisible(False)
        config_panel.splitter2.enable_panel()
        config_panel.splitter2.gridname_dropdown.dropdown.setCurrentText(gridname[i])
        config_panel.splitter2.muscle_input.input.setText(muscle[i])

    # enable multiple input 1 (and fill in data)
    if 3 in grid_adapter_set:
        i = grid_adapter_set.index(3)
        config_panel.mul_input_1.checkbox.setChecked(True)
        config_panel.mul_input_1.checkbox.setVisible(False)
        config_panel.mul_input_1.enable_panel()
        config_panel.mul_input_1.gridname_dropdown.dropdown.setCurrentText(gridname[i])
        config_panel.mul_input_1.muscle_input.input.setText(muscle[i])

    # enable multiple input 2 (and fill in data)
    if 4 in grid_adapter_set:
        i = grid_adapter_set.index(4)
        config_panel.mul_input_2.checkbox.setChecked(True)
        config_panel.mul_input_2.checkbox.setVisible(False)
        config_panel.mul_input_2.enable_panel()
        config_panel.mul_input_2.gridname_dropdown.dropdown.setCurrentText(gridname[i])
        config_panel.mul_input_2.muscle_input.input.setText(muscle[i])

    # enable multiple input 3 (and fill in data)
    if 5 in grid_adapter_set:
        i = grid_adapter_set.index(5)
        config_panel.mul_input_3.checkbox.setChecked(True)
        config_panel.mul_input_3.checkbox.setVisible(False)
        config_panel.mul_input_3.enable_panel()
        config_panel.mul_input_3.gridname_dropdown.dropdown.setCurrentText(gridname[i])
        config_panel.mul_input_3.muscle_input.input.setText(muscle[i])

    # enable multiple input 4 (and fill in data)
    if 6 in grid_adapter_set:
        i = grid_adapter_set.index(6)
        config_panel.mul_input_4.checkbox.setChecked(True)
        config_panel.mul_input_4.checkbox.setVisible(False)
        config_panel.mul_input_4.enable_panel()
        config_panel.mul_input_4.gridname_dropdown.dropdown.setCurrentText(gridname[i])
        config_panel.mul_input_4.muscle_input.input.setText(muscle[i])

    return config_panel
