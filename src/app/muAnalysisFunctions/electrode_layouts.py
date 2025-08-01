"""
Electrode matrix sorting utilities for HD-EMG plotting
(copied and adapted from OpenHD-EMG style definitions)
"""

import numpy as np
import copy
import itertools

OTBelectrodes_tuple = (
    "GR04MM1305",
    "GR08MM1305",
    "GR100ML1305",
    "GR10MM0804",
    "GR10MM0808",
    "HD04MM1305",
    "HD08MM1305",
    "HD10MM0804",
    "HD10MM0808",
)

OTBelectrodes_ied = {
    "GR04MM1305": 4,
    "GR08MM1305": 8,
    "GR100ML1305": 2.5,
    "GR10MM0804": 10,
    "GR10MM0808": 10,
    "HD04MM1305": 4,
    "HD08MM1305": 8,
    "HD10MM0804": 10,
    "HD10MM0808": 10,
}

OTBelectrodes_Nelectrodes = {
    "GR04MM1305": 64,
    "GR08MM1305": 64,
    "GR100ML1305": 64,
    "GR10MM0804": 32,
    "GR10MM0808": 64,
    "HD04MM1305": 64,
    "HD08MM1305": 64,
    "HD10MM0804": 32,
    "HD10MM0808": 64,
}

# --- Mappings (0 and 180 degree) for the most common grids ---
GR08MM1305_0 = [
    [63, 38, 37, 12, 11],
    [62, 39, 36, 13, 10],
    [61, 40, 35, 14,  9],
    [60, 41, 34, 15,  8],
    [59, 42, 33, 16,  7],
    [58, 43, 32, 17,  6],
    [57, 44, 31, 18,  5],
    [56, 45, 30, 19,  4],
    [55, 46, 29, 20,  3],
    [54, 47, 28, 21,  2],
    [53, 48, 27, 22,  1],
    [52, 49, 26, 23,  0],
    [51, 50, 25, 24, np.nan],
]
GR08MM1305_180 = [
    [np.nan, 24, 25, 50, 51],
    [0,      23, 26, 49, 52],
    [1,      22, 27, 48, 53],
    [2,      21, 28, 47, 54],
    [3,      20, 29, 46, 55],
    [4,      19, 30, 45, 56],
    [5,      18, 31, 44, 57],
    [6,      17, 32, 43, 58],
    [7,      16, 33, 42, 59],
    [8,      15, 34, 41, 60],
    [9,      14, 35, 40, 61],
    [10,     13, 36, 39, 62],
    [11,     12, 37, 38, 63],
]


# You can add other grid layouts here as needed...

def get_electrode_grid(code="GR08MM1305", orientation=180):
    """
    Returns the mapping grid for a given code and orientation.
    Only GR08MM1305 (0 or 180) is supported for now.
    """
    if code == "GR08MM1305":
        if orientation == 180:
            return GR08MM1305_180
        elif orientation == 0:
            return GR08MM1305_0
        else:
            raise ValueError("Unknown orientation for GR08MM1305")
    else:
        raise NotImplementedError("Grid code not implemented: %s" % code)
