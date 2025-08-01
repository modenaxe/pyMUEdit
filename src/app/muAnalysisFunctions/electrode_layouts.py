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
GR08MM1305_180 = [
    [np.nan,  0,  1,  2,  3],
    [ 4,      5,  6,  7,  8],
    [ 9,     10, 11, 12, 13],
    [14,     15, 16, 17, 18],
    [19,     20, 21, 22, 23],
    [24,     25, 26, 27, 28],
    [29,     30, 31, 32, 33],
    [34,     35, 36, 37, 38],
    [39,     40, 41, 42, 43],
    [44,     45, 46, 47, 48],
    [49,     50, 51, 52, 53],
    [54,     55, 56, 57, 58],
    [59,     60, 61, 62, 63]
]

GR08MM1305_0 = [
    [63, 62, 61, 60, 59],
    [58, 57, 56, 55, 54],
    [53, 52, 51, 50, 49],
    [48, 47, 46, 45, 44],
    [43, 42, 41, 40, 39],
    [38, 37, 36, 35, 34],
    [33, 32, 31, 30, 29],
    [28, 27, 26, 25, 24],
    [23, 22, 21, 20, 19],
    [18, 17, 16, 15, 14],
    [13, 12, 11, 10,  9],
    [ 8,  7,  6,  5,  4],
    [ 3,  2,  1,  0, np.nan]
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
