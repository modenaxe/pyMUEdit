import numpy as np
import matplotlib.pyplot as plt
from lib.notchsignals import notchsignals


def formatsignalHDEMG(signal, gridname, fsamp, checkEMG):
    coordinates = []
    IED = np.zeros(len(gridname))
    discardChannelsVec = []
    emgtype = np.zeros(len(gridname))

    ch = 0  # Python uses 0-based indexing
    for i in range(len(gridname)):
        # Handle gridname as scalar or array
        grid_str = gridname[i]
        if isinstance(grid_str, np.ndarray):
            grid_str = str(grid_str.item()) if grid_str.size == 1 else str(grid_str)
        elif not isinstance(grid_str, str):
            grid_str = str(grid_str)

        # Define the parameters depending on the name of the grid
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

            discardChannelsVec.append(np.zeros(64))
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

            discardChannelsVec.append(np.zeros(64))
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

            discardChannelsVec.append(np.zeros(64))
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

            discardChannelsVec.append(np.zeros(32))
            nbelectrodes = 32
            IED[i] = 10
            emgtype[i] = 1

        elif "protogrid_v1" in grid_str:
            ElChannelMap = np.array(
                [
                    [0, 55, 0, 43, 0, 15, 0, 14, 0, 0],
                    [0, 57, 53, 41, 25, 13, 24, 12, 4, 0],
                    [0, 0, 45, 39, 23, 11, 22, 10, 2, 9],
                    [0, 63, 47, 27, 21, 30, 20, 8, 5, 0],
                    [0, 61, 49, 29, 19, 28, 18, 6, 7, 0],
                    [0, 59, 51, 37, 17, 26, 16, 34, 1, 0],
                    [64, 60, 54, 50, 44, 40, 35, 32, 0, 0],
                    [0, 62, 56, 52, 46, 42, 36, 33, 31, 0],
                    [0, 0, 58, 0, 48, 0, 38, 0, 3, 0],
                ]
            )

            discardChannelsVec.append(np.zeros(64))
            nbelectrodes = 64
            IED[i] = 2
            emgtype[i] = 1

        elif "intan64" in grid_str:
            ElChannelMap = np.array(
                [
                    [37, 33, 34, 3, 1],
                    [37, 46, 35, 5, 7],
                    [39, 48, 36, 2, 9],
                    [41, 50, 38, 18, 11],
                    [43, 52, 40, 16, 13],
                    [45, 54, 42, 14, 29],
                    [47, 56, 44, 12, 27],
                    [49, 58, 32, 10, 25],
                    [51, 60, 31, 8, 23],
                    [62, 53, 30, 6, 21],
                    [64, 55, 28, 4, 19],
                    [59, 57, 26, 20, 17],
                    [61, 63, 24, 22, 15],
                ]
            )

            discardChannelsVec.append(np.zeros(64))
            nbelectrodes = 64
            IED[i] = 4
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

            discardChannelsVec.append(np.zeros(32))
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

            discardChannelsVec.append(np.zeros(32))
            nbelectrodes = 32
            IED[i] = 1
            emgtype[i] = 2
        else:
            # Default case for unknown grid types
            print(f"Warning: Unknown grid type '{grid_str}'. Using default values.")
            ElChannelMap = np.array([[1]])
            discardChannelsVec.append(np.zeros(1))
            nbelectrodes = 1
            IED[i] = 1
            emgtype[i] = 1

        # Create coordinates for each electrode
        coordinates.append(np.zeros((np.max(ElChannelMap), 2)))
        for r in range(ElChannelMap.shape[0]):
            for c in range(ElChannelMap.shape[1]):
                if ElChannelMap[r, c] > 0:
                    # Use 0-based indexing for Python
                    coordinates[i][ElChannelMap[r, c] - 1, 0] = r + 1
                    coordinates[i][ElChannelMap[r, c] - 1, 1] = c + 1

        # Apply notch filter before visualization
        signal_filtered = notchsignals(signal, fsamp)

        # Visual checking of EMG signals by column
        if checkEMG == 1:
            ch1 = 0
            for c in range(ElChannelMap.shape[1]):
                plt.figure(figsize=(12, 8))
                colors = plt.cm.viridis(np.linspace(0, 1, ElChannelMap.shape[0]))  # type: ignore

                for r in range(ElChannelMap.shape[0]):
                    if ch < signal_filtered.shape[0] and ch1 < len(discardChannelsVec[i]):
                        # Normalize the signal for visualization
                        max_val = np.max(np.abs(signal_filtered[ch]))
                        if max_val > 0:  # Prevent division by zero
                            signal_normalized = signal_filtered[ch] / max_val
                        else:
                            signal_normalized = signal_filtered[ch]

                        plt.plot(signal_normalized + r + 1, color=colors[r], linewidth=1)
                        plt.grid(True)
                        ch += 1
                        ch1 += 1

                plt.ylim([0, ElChannelMap.shape[0] + 1])
                plt.title(f"Column#{c+1}", color=(0.9412, 0.9412, 0.9412), fontsize=20)
                plt.xlabel("Time (s)", fontsize=20)
                plt.ylabel("Row #", fontsize=20)
                plt.gcf().set_facecolor((0.5, 0.5, 0.5))
                plt.gca().set_facecolor((0.5, 0.5, 0.5))
                plt.gca().xaxis.label.set_color((0.9412, 0.9412, 0.9412))
                plt.gca().yaxis.label.set_color((0.9412, 0.9412, 0.9412))
                plt.gca().tick_params(axis="x", colors=(0.9412, 0.9412, 0.9412))
                plt.gca().tick_params(axis="y", colors=(0.9412, 0.9412, 0.9412))

                discchan = input("Enter the number of discarded channels (Enter space-separated numbers): ")

                if discchan:
                    try:
                        discchan_nums = [int(num) for num in discchan.split()]
                        for num in discchan_nums:
                            if 0 <= num < len(discardChannelsVec[i]):
                                idx = num + (c - 1) * ElChannelMap.shape[0]
                                if 0 <= idx < len(discardChannelsVec[i]):
                                    discardChannelsVec[i][idx] = 1
                    except (ValueError, TypeError):
                        print("Invalid input format. No channels discarded.")

                plt.close()

            # Check length of discardChannelsVec
            if len(discardChannelsVec[i]) > nbelectrodes:
                discardChannelsVec[i] = discardChannelsVec[i][:nbelectrodes]
        else:
            discardChannelsVec[i] = np.zeros(nbelectrodes)

    return coordinates, IED, discardChannelsVec, emgtype
