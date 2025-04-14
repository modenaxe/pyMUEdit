import numpy as np
from utils.decomposition.notchsignals import notchsignals


def formatsignalHDEMG(signal, gridname, fsamp, checkEMG=0):
    if signal.dtype == object and signal.shape == (1, 1):
        signal = signal[0, 0]

    # Initialize return variables
    coordinates = []
    IED = np.zeros(len(gridname))
    discardChannelsVec = []
    emgtype = np.zeros(len(gridname))

    # Process each grid
    ch = 0  # Channel counter
    for i in range(len(gridname)):
        # Get grid name as string
        grid_str = str(gridname[i].item() if isinstance(gridname[i], np.ndarray) else gridname[i])

        # Determine grid configuration based on grid name
        if "GR04MM1305" in grid_str or "HD04MM1305" in grid_str:
            ElChannelMap = np.array(
                [
                    [1, 25, 26, 51, 52],
                    [1, 24, 27, 50, 53],
                    [2, 23, 28, 49, 54],
                    [3, 22, 29, 48, 55],
                    [4, 21, 30, 47, 56],
                    [5, 20, 31, 46, 57],
                    [6, 19, 32, 45, 58],
                    [7, 18, 33, 44, 59],
                    [8, 17, 34, 43, 60],
                    [9, 16, 35, 42, 61],
                    [10, 15, 36, 41, 62],
                    [11, 14, 37, 40, 63],
                    [12, 13, 38, 39, 64],
                ]
            )
            if "HD" in grid_str:
                ElChannelMap = np.fliplr(ElChannelMap)
            nbelectrodes = 64
            IED[i] = 4
            emgtype[i] = 1

        elif "GR08MM1305" in grid_str or "HD08MM1305" in grid_str:
            ElChannelMap = np.array(
                [
                    [1, 25, 26, 51, 52],
                    [1, 24, 27, 50, 53],
                    [2, 23, 28, 49, 54],
                    [3, 22, 29, 48, 55],
                    [4, 21, 30, 47, 56],
                    [5, 20, 31, 46, 57],
                    [6, 19, 32, 45, 58],
                    [7, 18, 33, 44, 59],
                    [8, 17, 34, 43, 60],
                    [9, 16, 35, 42, 61],
                    [10, 15, 36, 41, 62],
                    [11, 14, 37, 40, 63],
                    [12, 13, 38, 39, 64],
                ]
            )
            if "HD" in grid_str:
                ElChannelMap = np.fliplr(ElChannelMap)
            nbelectrodes = 64
            IED[i] = 8
            emgtype[i] = 1

        elif "GR10MM0808" in grid_str or "HD10MM0808" in grid_str:
            ElChannelMap = np.array(
                [
                    [8, 16, 24, 32, 40, 48, 56, 64],
                    [7, 15, 23, 31, 39, 47, 55, 63],
                    [6, 14, 22, 30, 38, 46, 54, 62],
                    [5, 13, 21, 29, 37, 45, 53, 61],
                    [4, 12, 20, 28, 36, 44, 52, 60],
                    [3, 11, 19, 27, 35, 43, 51, 59],
                    [2, 10, 18, 26, 34, 42, 50, 58],
                    [1, 9, 17, 25, 33, 41, 49, 57],
                ]
            )
            if "HD" in grid_str:
                ElChannelMap = np.fliplr(ElChannelMap)
            nbelectrodes = 64
            IED[i] = 10
            emgtype[i] = 1

        elif "GR10MM0804" in grid_str or "HD10MM0804" in grid_str:
            ElChannelMap = np.array(
                [
                    [32, 24, 16, 8],
                    [31, 23, 15, 7],
                    [30, 22, 14, 6],
                    [29, 21, 13, 5],
                    [28, 20, 12, 4],
                    [27, 19, 11, 3],
                    [26, 18, 10, 2],
                    [25, 17, 9, 1],
                ]
            )
            if "HD" in grid_str:
                ElChannelMap = np.rot90(ElChannelMap, 2)
            nbelectrodes = 32
            IED[i] = 10
            emgtype[i] = 1

        elif "MYOMRF-4x8" in grid_str:
            ElChannelMap = np.array(
                [
                    [25, 1, 16, 24],
                    [26, 2, 15, 23],
                    [27, 3, 14, 22],
                    [28, 4, 13, 21],
                    [29, 5, 12, 20],
                    [30, 6, 11, 19],
                    [31, 7, 10, 18],
                    [32, 8, 9, 17],
                ]
            )
            nbelectrodes = 32
            IED[i] = 1
            emgtype[i] = 2

        elif "MYOMNP-1x32" in grid_str:
            ElChannelMap = np.array(
                [
                    [24, 25, 16, 1],
                    [23, 26, 15, 2],
                    [22, 27, 14, 3],
                    [21, 28, 13, 4],
                    [20, 29, 12, 5],
                    [19, 30, 11, 6],
                    [18, 31, 10, 7],
                    [17, 32, 9, 8],
                ]
            )
            nbelectrodes = 32
            IED[i] = 1
            emgtype[i] = 2

        else:
            # Default case for unknown grid types
            ElChannelMap = np.array([[1]])
            nbelectrodes = 1
            IED[i] = 1
            emgtype[i] = 1

        # Initialize channel discard vector
        discardChannelsVec.append(np.zeros(nbelectrodes))

        # Create coordinates for each electrode
        coordinates.append(np.zeros((np.max(ElChannelMap), 2)))
        for r in range(ElChannelMap.shape[0]):
            for c in range(ElChannelMap.shape[1]):
                if ElChannelMap[r, c] > 0:
                    coordinates[i][ElChannelMap[r, c] - 1, 0] = r + 1
                    coordinates[i][ElChannelMap[r, c] - 1, 1] = c + 1

        # Apply notch filter to the signal
        signal_filtered = notchsignals(signal, fsamp)

        # Visual checking of EMG
        if checkEMG == 1:
            try:
                import matplotlib.pyplot as plt

                ch1 = 0
                for c in range(ElChannelMap.shape[1]):
                    # Auto-detect bad channels
                    bad_channels = []
                    for r in range(ElChannelMap.shape[0]):
                        if ch < signal_filtered.shape[0] and ch1 < len(discardChannelsVec[i]):
                            # Check for obviously bad channels
                            if np.isnan(signal_filtered[ch]).any() or np.max(np.abs(signal_filtered[ch])) < 1e-6:
                                bad_channels.append(ch1)
                            ch += 1
                            ch1 += 1

                    # Mark detected bad channels
                    for bad_ch in bad_channels:
                        if bad_ch < len(discardChannelsVec[i]):
                            discardChannelsVec[i][bad_ch] = 1

            except ImportError:
                pass

        # Ensure length of discardChannelsVec is appropriate
        if len(discardChannelsVec[i]) > nbelectrodes:
            discardChannelsVec[i] = discardChannelsVec[i][:nbelectrodes]

    return coordinates, IED, discardChannelsVec, emgtype
