import numpy as np


def segmenttargets(target, nwindows, threshold):
    plateau = np.where(target >= np.max(target) * threshold)[0]
    sep = np.where(np.diff(plateau) > 1)[0]

    if nwindows > 1 and len(sep) > 0:
        coordinatestmp = np.zeros((len(sep) + 1, 2), dtype=int)
        coordinatestmp[0, :] = [plateau[0], plateau[sep[0]]]

        for i in range(len(sep)):
            if i < len(sep) - 1:
                coordinatestmp[i + 1, :] = [plateau[sep[i] + 1], plateau[sep[i + 1]]]
            else:
                coordinatestmp[i + 1, :] = [plateau[sep[i] + 1], plateau[-1]]

        lplat = coordinatestmp[:, 1] - coordinatestmp[:, 0]
        lwin = np.floor(lplat / nwindows).astype(int)

        coordinates = np.zeros((len(sep) + 1, nwindows * 2), dtype=int)
        for i in range(nwindows):
            coordinates[:, i * 2] = coordinatestmp[:, 0] + (i - 1) * lwin + 1
            coordinates[:, i * 2 + 1] = coordinatestmp[:, 0] + i * lwin

        coordinates = coordinates.flatten()

    elif nwindows > 1:
        coordinatestmp = np.array([[plateau[0], plateau[-1]]])
        lplat = coordinatestmp[:, 1] - coordinatestmp[:, 0]
        lwin = np.floor(lplat / nwindows).astype(int)

        coordinates = np.zeros((1, nwindows * 2), dtype=int)
        for i in range(nwindows):
            coordinates[:, i * 2] = coordinatestmp[:, 0] + (i - 1) * lwin + 1
            coordinates[:, i * 2 + 1] = coordinatestmp[:, 0] + i * lwin

        coordinates = coordinates.flatten()

    elif nwindows == 1 and len(sep) > 0:
        coordinatestmp = np.zeros((len(sep) + 1, 2), dtype=int)
        coordinatestmp[0, :] = [plateau[0], plateau[sep[0]]]

        for i in range(len(sep)):
            if i < len(sep) - 1:
                coordinatestmp[i + 1, :] = [plateau[sep[i] + 1], plateau[sep[i + 1]]]
            else:
                coordinatestmp[i + 1, :] = [plateau[sep[i] + 1], plateau[-1]]

        lplat = coordinatestmp[:, 1] - coordinatestmp[:, 0]
        lwin = np.floor(lplat / nwindows).astype(int)

        coordinates = np.zeros((len(sep) + 1, nwindows * 2), dtype=int)
        for i in range(nwindows):
            coordinates[:, i * 2] = coordinatestmp[:, 0] + (i - 1) * lwin + 1
            coordinates[:, i * 2 + 1] = coordinatestmp[:, 0] + i * lwin

        coordinates = coordinates.flatten()
    else:
        coordinates = np.array([plateau[0], plateau[-1]])

    return coordinates
