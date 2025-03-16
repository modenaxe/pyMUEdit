import numpy as np
import struct
import os
import math


def read_Intan_RHD_MUedit(path, file):
    filename = os.path.join(path, file)
    fid = open(filename, "rb")

    filesize = os.path.getsize(filename)

    # Check 'magic number' at beginning of file to make sure this is an Intan Technologies RHD2000 data file
    magic_number = struct.unpack("<I", fid.read(4))[0]
    if magic_number != 0xC6912702:
        raise ValueError("Unrecognized file type.")

    # Read version number
    data_file_main_version_number = struct.unpack("<h", fid.read(2))[0]
    data_file_secondary_version_number = struct.unpack("<h", fid.read(2))[0]

    print(
        f"\nReading Intan Technologies RHD2000 Data File, Version {data_file_main_version_number}.{data_file_secondary_version_number}\n"
    )

    if data_file_main_version_number == 1:
        num_samples_per_data_block = 60
    else:
        num_samples_per_data_block = 128

    # Read information of sampling rate and amplifier frequency settings
    sample_rate = struct.unpack("<f", fid.read(4))[0]
    dsp_enabled = struct.unpack("<h", fid.read(2))[0]
    actual_dsp_cutoff_frequency = struct.unpack("<f", fid.read(4))[0]
    actual_lower_bandwidth = struct.unpack("<f", fid.read(4))[0]
    actual_upper_bandwidth = struct.unpack("<f", fid.read(4))[0]

    desired_dsp_cutoff_frequency = struct.unpack("<f", fid.read(4))[0]
    desired_lower_bandwidth = struct.unpack("<f", fid.read(4))[0]
    desired_upper_bandwidth = struct.unpack("<f", fid.read(4))[0]

    # This tells us if a software 50/60 Hz notch filter was enabled during the data acquisition
    notch_filter_mode = struct.unpack("<h", fid.read(2))[0]
    notch_filter_frequency = 0
    if notch_filter_mode == 1:
        notch_filter_frequency = 50
    elif notch_filter_mode == 2:
        notch_filter_frequency = 60

    desired_impedance_test_frequency = struct.unpack("<f", fid.read(4))[0]
    actual_impedance_test_frequency = struct.unpack("<f", fid.read(4))[0]

    # Place notes in data structure
    notes = {}
    notes["note1"] = read_QString(fid)
    notes["note2"] = read_QString(fid)
    notes["note3"] = read_QString(fid)

    # If data file is from GUI v1.1 or later, see if temperature sensor data was saved
    num_temp_sensor_channels = 0
    if (data_file_main_version_number == 1 and data_file_secondary_version_number >= 1) or (
        data_file_main_version_number > 1
    ):
        num_temp_sensor_channels = struct.unpack("<h", fid.read(2))[0]

    # If data file is from GUI v1.3 or later, load board mode
    board_mode = 0
    if (data_file_main_version_number == 1 and data_file_secondary_version_number >= 3) or (
        data_file_main_version_number > 1
    ):
        board_mode = struct.unpack("<h", fid.read(2))[0]

    # If data file is from v2.0 or later (Intan Recording Controller), load name of digital reference channel
    reference_channel = ""
    if data_file_main_version_number > 1:
        reference_channel = read_QString(fid)

    # Place frequency-related information in data structure
    frequency_parameters = {
        "amplifier_sample_rate": sample_rate,
        "aux_input_sample_rate": sample_rate / 4,
        "supply_voltage_sample_rate": sample_rate / num_samples_per_data_block,
        "board_adc_sample_rate": sample_rate,
        "board_dig_in_sample_rate": sample_rate,
        "desired_dsp_cutoff_frequency": desired_dsp_cutoff_frequency,
        "actual_dsp_cutoff_frequency": actual_dsp_cutoff_frequency,
        "dsp_enabled": dsp_enabled,
        "desired_lower_bandwidth": desired_lower_bandwidth,
        "actual_lower_bandwidth": actual_lower_bandwidth,
        "desired_upper_bandwidth": desired_upper_bandwidth,
        "actual_upper_bandwidth": actual_upper_bandwidth,
        "notch_filter_frequency": notch_filter_frequency,
        "desired_impedance_test_frequency": desired_impedance_test_frequency,
        "actual_impedance_test_frequency": actual_impedance_test_frequency,
    }

    # Define data structure for data channels
    def create_channel_struct():
        return {
            "native_channel_name": "",
            "custom_channel_name": "",
            "native_order": 0,
            "custom_order": 0,
            "board_stream": 0,
            "chip_channel": 0,
            "port_name": "",
            "port_prefix": "",
            "port_number": 0,
            "electrode_impedance_magnitude": 0.0,
            "electrode_impedance_phase": 0.0,
        }

    # Define data structure for spike trigger settings
    def create_trigger_struct():
        return {
            "voltage_trigger_mode": 0,
            "voltage_threshold": 0,
            "digital_trigger_channel": 0,
            "digital_edge_polarity": 0,
        }

    amplifier_channels = []
    aux_input_channels = []
    supply_voltage_channels = []
    board_adc_channels = []
    board_dig_in_channels = []
    board_dig_out_channels = []

    amplifier_index = 0
    aux_input_index = 0
    supply_voltage_index = 0
    board_adc_index = 0
    board_dig_in_index = 0
    board_dig_out_index = 0

    # Read signal summary from data file header
    number_of_signal_groups = struct.unpack("<h", fid.read(2))[0]

    for signal_group in range(number_of_signal_groups):
        signal_group_name = read_QString(fid)
        signal_group_prefix = read_QString(fid)
        signal_group_enabled = struct.unpack("<h", fid.read(2))[0]
        signal_group_num_channels = struct.unpack("<h", fid.read(2))[0]
        signal_group_num_amp_channels = struct.unpack("<h", fid.read(2))[0]

        if signal_group_num_channels > 0 and signal_group_enabled > 0:
            new_channel = create_channel_struct()
            new_channel["port_name"] = signal_group_name
            new_channel["port_prefix"] = signal_group_prefix
            new_channel["port_number"] = signal_group

            for signal_channel in range(signal_group_num_channels):
                new_channel = create_channel_struct()
                new_channel["port_name"] = signal_group_name
                new_channel["port_prefix"] = signal_group_prefix
                new_channel["port_number"] = signal_group

                new_channel["native_channel_name"] = read_QString(fid)
                new_channel["custom_channel_name"] = read_QString(fid)
                new_channel["native_order"] = struct.unpack("<h", fid.read(2))[0]
                new_channel["custom_order"] = struct.unpack("<h", fid.read(2))[0]
                signal_type = struct.unpack("<h", fid.read(2))[0]
                channel_enabled = struct.unpack("<h", fid.read(2))[0]
                new_channel["chip_channel"] = struct.unpack("<h", fid.read(2))[0]
                new_channel["board_stream"] = struct.unpack("<h", fid.read(2))[0]

                new_trigger_channel = create_trigger_struct()
                new_trigger_channel["voltage_trigger_mode"] = struct.unpack("<h", fid.read(2))[0]
                new_trigger_channel["voltage_threshold"] = struct.unpack("<h", fid.read(2))[0]
                new_trigger_channel["digital_trigger_channel"] = struct.unpack("<h", fid.read(2))[0]
                new_trigger_channel["digital_edge_polarity"] = struct.unpack("<h", fid.read(2))[0]

                new_channel["electrode_impedance_magnitude"] = struct.unpack("<f", fid.read(4))[0]
                new_channel["electrode_impedance_phase"] = struct.unpack("<f", fid.read(4))[0]

                if channel_enabled:
                    if signal_type == 0:
                        amplifier_channels.append(new_channel)
                        amplifier_index += 1
                    elif signal_type == 1:
                        aux_input_channels.append(new_channel)
                        aux_input_index += 1
                    elif signal_type == 2:
                        supply_voltage_channels.append(new_channel)
                        supply_voltage_index += 1
                    elif signal_type == 3:
                        board_adc_channels.append(new_channel)
                        board_adc_index += 1
                    elif signal_type == 4:
                        board_dig_in_channels.append(new_channel)
                        board_dig_in_index += 1
                    elif signal_type == 5:
                        board_dig_out_channels.append(new_channel)
                        board_dig_out_index += 1
                    else:
                        raise ValueError("Unknown channel type")

    # Close data file
    fid.close()

    return amplifier_channels, board_adc_channels, board_dig_in_channels, frequency_parameters


def read_QString(fid):
    """
    Read Qt style QString from file.
    The first 32-bit unsigned number indicates the length of the string (in bytes).
    If this number equals 0xFFFFFFFF, the string is null.
    """
    length = struct.unpack("<I", fid.read(4))[0]
    if length == 0xFFFFFFFF:
        return ""

    # Convert length from bytes to 16-bit Unicode words
    length = length // 2

    # Read string data
    data = []
    for i in range(length):
        data.append(struct.unpack("<H", fid.read(2))[0])

    return "".join(chr(c) for c in data)
