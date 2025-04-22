import numpy as np
from core.utils.decomposition.notch_filter import notch_filter
from core.utils.decomposition.bandpass_filter import bandpass_filter
from typing import TYPE_CHECKING, Any, Dict, List, Union, Tuple

if TYPE_CHECKING:
    from EmgDecomposition import offline_EMG


def electrode_formatter(emg_obj: "offline_EMG") -> None:
    """
    Match up the signals with the electrode shape and numbering.
    Moved from offline_EMG class to a standalone function.

    Args:
        emg_obj: Instance of offline_EMG class
    """
    electrode_names = emg_obj.signal_dict["electrodes"]
    print(f"Electrode names: {electrode_names}")
    ElChannelMap = []
    coordinates = []
    emg_obj.emgopt = []
    IED = []
    c_map = []
    r_map = []
    rejected_channels = []
    chans_per_electrode = []
    emg_obj.signal_dict["filtered_data"] = np.zeros(
        [np.shape(emg_obj.signal_dict["data"])[0], np.shape(emg_obj.signal_dict["data"])[1]]
    )
    print(f"Initialized filtered_data with shape {emg_obj.signal_dict['filtered_data'].shape}")

    for i in range(emg_obj.signal_dict["nelectrodes"]):
        print(f"\nProcessing electrode {i+1}/{emg_obj.signal_dict['nelectrodes']}: {electrode_names[i]}")

        if electrode_names[i] == "GR04MM1305":
            print(f"Configuring {electrode_names[i]} (4mm grid)")
            ElChannelMap.append(
                [
                    [0, 24, 25, 50, 51],
                    [0, 23, 26, 49, 52],
                    [1, 22, 27, 48, 53],
                    [2, 21, 28, 47, 54],
                    [3, 20, 29, 46, 55],
                    [4, 19, 30, 45, 56],
                    [5, 18, 31, 44, 57],
                    [6, 17, 32, 43, 58],
                    [7, 16, 33, 42, 59],
                    [8, 15, 34, 41, 60],
                    [9, 14, 35, 40, 61],
                    [10, 13, 36, 39, 62],
                    [11, 12, 37, 38, 63],
                ]
            )

            rejected_channels.append(np.zeros([65]))
            IED.append(4)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]) - 1)
            emg_obj.emgopt.append("surface")

        elif electrode_names[i] == "ELSCH064NM2":
            print(f"Configuring {electrode_names[i]} (non-mapped EMG)")
            ElChannelMap.append(
                [
                    [0, 0, 1, 2, 3],
                    [15, 7, 6, 5, 4],
                    [14, 13, 12, 11, 10],
                    [18, 17, 16, 8, 9],
                    [19, 20, 21, 22, 23],
                    [27, 28, 29, 30, 31],
                    [24, 25, 26, 32, 33],
                    [34, 35, 36, 37, 38],
                    [44, 45, 46, 47, 39],
                    [43, 42, 41, 40, 38],
                    [53, 52, 51, 50, 49],
                    [54, 55, 63, 62, 61],
                    [56, 57, 58, 59, 60],
                ]
            )

            rejected_channels.append(np.zeros([65]))
            IED.append(8)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]) - 1)
            emg_obj.emgopt.append("surface")

        elif electrode_names[i] == "GR08MM1305":
            print(f"Configuring {electrode_names[i]} (8mm grid)")
            ElChannelMap.append(
                [
                    [0, 24, 25, 50, 51],
                    [0, 23, 26, 49, 52],
                    [1, 22, 27, 48, 53],
                    [2, 21, 28, 47, 54],
                    [3, 20, 29, 46, 55],
                    [4, 19, 30, 45, 56],
                    [5, 18, 31, 44, 57],
                    [6, 17, 32, 43, 58],
                    [7, 16, 33, 42, 59],
                    [8, 15, 34, 41, 60],
                    [9, 14, 35, 40, 61],
                    [10, 13, 36, 39, 62],
                    [11, 12, 37, 38, 63],
                ]
            )

            rejected_channels.append(np.zeros([65]))
            IED.append(8)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]) - 1)
            emg_obj.emgopt.append("surface")

        elif electrode_names[i] == "GR10MM0808":
            print(f"Configuring {electrode_names[i]} (10mm grid)")
            ElChannelMap.append(
                [
                    [7, 15, 23, 31, 39, 47, 55, 63],
                    [6, 14, 22, 30, 38, 46, 54, 62],
                    [5, 13, 21, 29, 37, 45, 53, 61],
                    [4, 12, 20, 28, 36, 44, 52, 60],
                    [3, 11, 19, 27, 35, 43, 51, 59],
                    [2, 10, 18, 26, 34, 42, 50, 58],
                    [1, 9, 17, 25, 33, 41, 49, 57],
                    [0, 8, 16, 24, 32, 40, 48, 56],
                ]
            )

            rejected_channels.append(np.zeros([65]))
            IED.append(10)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]) - 1)
            emg_obj.emgopt.append("surface")

        elif electrode_names[i] == "other":
            print(f"Configuring {electrode_names[i]} (other type - assuming thin-film)")
            # TO DO: match up to the relevant configuration for a thin-film
            ElChannelMap.append(
                [
                    [0, 24, 25, 50, 51],
                    [0, 23, 26, 49, 52],
                    [1, 22, 27, 48, 53],
                    [2, 21, 28, 47, 54],
                    [3, 20, 29, 46, 55],
                    [4, 19, 30, 45, 56],
                    [5, 18, 31, 44, 57],
                    [6, 17, 32, 43, 58],
                    [7, 16, 33, 42, 59],
                    [8, 15, 34, 41, 60],
                    [9, 14, 35, 40, 61],
                    [10, 13, 36, 39, 62],
                    [11, 12, 37, 38, 63],
                ]
            )

            rejected_channels.append(np.zeros([65]))
            IED.append(1)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]) - 1)
            emg_obj.emgopt.append("intra")

        elif electrode_names[i] == "Thin film":
            print(f"Configuring {electrode_names[i]} (thin film)")
            ElChannelMap.append(
                [
                    [0, 10, 20, 30],
                    [1, 11, 21, 31],
                    [2, 12, 22, 32],
                    [3, 13, 23, 33],
                    [4, 14, 24, 34],
                    [5, 15, 25, 35],
                    [6, 16, 26, 36],
                    [7, 17, 27, 37],
                    [8, 18, 28, 38],
                    [9, 19, 29, 39],
                ]
            )

            rejected_channels.append(np.zeros([40]))
            IED.append(1)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]))
            emg_obj.emgopt.append("intra")

        elif electrode_names[i] == "4-wire needle":
            print(f"Configuring {electrode_names[i]} (4-wire needle)")
            ElChannelMap.append([[0, 8], [1, 9], [2, 10], [3, 11], [4, 12], [5, 13], [6, 14], [7, 15]])

            rejected_channels.append(np.zeros([16]))
            IED.append(4)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]))
            emg_obj.emgopt.append("intra")

        elif electrode_names[i] == "Myomatrix Monopolar":
            print(f"Configuring {electrode_names[i]} (Myomatrix Monopolar)")
            ElChannelMap.append(
                [
                    [0, 8, 16, 24],
                    [1, 9, 17, 25],
                    [2, 10, 18, 26],
                    [3, 11, 19, 27],
                    [4, 12, 20, 28],
                    [5, 13, 21, 29],
                    [6, 14, 22, 30],
                    [7, 15, 23, 31],
                ]
            )

            rejected_channels.append(np.zeros([16]))
            IED.append(4)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]))
            emg_obj.emgopt.append("intra")

        else:
            print(f"Unknown electrode type {electrode_names[i]} - assuming intramuscular array")
            # assume that it is some variation of an intramusuclar array
            ElChannelMap.append([[0, 8], [1, 9], [2, 10], [3, 11], [4, 12], [5, 13], [6, 14], [7, 15]])

            rejected_channels.append(np.zeros([16]))
            IED.append(4)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]))
            emg_obj.emgopt.append("intra")

        coordinates.append(np.zeros([chans_per_electrode[i], 2]))
        rows, cols = ElChannelMap[i].shape
        row_indices, col_indices = np.unravel_index(np.arange(ElChannelMap[i].size), (rows, cols))
        coordinates[i][:, 0] = row_indices[1:]
        coordinates[i][:, 1] = col_indices[1:]
        print(f"Set coordinates for electrode {i}, shape: {coordinates[i].shape}")

        c_map.append(np.shape(ElChannelMap[i])[1])
        r_map.append(np.shape(ElChannelMap[i])[0])
        print(f"Electrode {i} dimensions: rows={r_map[i]}, columns={c_map[i]}")

        electrode = i + 1
        print(f"Filtering data for electrode {electrode}...")

        # notch filtering
        print(f"Applying notch filter to electrode {electrode}...")
        emg_obj.signal_dict["filtered_data"][
            chans_per_electrode[i] * (electrode - 1) : electrode * chans_per_electrode[i], :
        ] = notch_filter(
            emg_obj.signal_dict["data"][
                chans_per_electrode[i] * (electrode - 1) : electrode * chans_per_electrode[i], :
            ],
            emg_obj.signal_dict["fsamp"],
        )

        # bandpass filtering
        print(f"Applying bandpass filter to electrode {electrode} with type {emg_obj.emgopt[i]}...")
        emg_obj.signal_dict["filtered_data"][
            chans_per_electrode[i] * (electrode - 1) : electrode * chans_per_electrode[i], :
        ] = bandpass_filter(
            emg_obj.signal_dict["filtered_data"][
                chans_per_electrode[i] * (electrode - 1) : electrode * chans_per_electrode[i], :
            ],
            emg_obj.signal_dict["fsamp"],
            emg_type=emg_obj.emgopt[i],
        )

    emg_obj.c_maps = c_map
    emg_obj.r_maps = r_map
    emg_obj.rejected_channels = rejected_channels
    emg_obj.ied = IED
    emg_obj.chans_per_electrode = chans_per_electrode
    emg_obj.coordinates = coordinates
    print(f"Electrode formatting results:")
    print(f"  - c_maps: {emg_obj.c_maps}")
    print(f"  - r_maps: {emg_obj.r_maps}")
    print(f"  - IEDs: {emg_obj.ied}")
    print(f"  - Channels per electrode: {emg_obj.chans_per_electrode}")
    print(f"  - EMG types: {emg_obj.emgopt}")
