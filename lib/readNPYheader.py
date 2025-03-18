import numpy as np
import os
import struct


def readNPYheader(filename):
    dtypes_python = {
        "uint8": "u1",
        "uint16": "u2",
        "uint32": "u4",
        "uint64": "u8",
        "int8": "i1",
        "int16": "i2",
        "int32": "i4",
        "int64": "i8",
        "float32": "f4",
        "float64": "f8",
        "bool": "b1",
        "str": "S513",
    }

    dtypes_numpy = {v: k for k, v in dtypes_python.items()}

    if not os.path.exists(filename):
        if not os.access(os.path.dirname(filename), os.W_OK):
            raise PermissionError(f"Permission denied: {filename}")
        else:
            raise FileNotFoundError(f"File not found: {filename}")

    with open(filename, "rb") as fid:
        # Read magic string
        magic_string = np.fromfile(fid, dtype="uint8", count=6)

        if not np.array_equal(magic_string, np.array([147, 78, 85, 77, 80, 89], dtype="uint8")):
            raise ValueError("Error: This file does not appear to be NUMPY format based on the header.")

        # Read version
        major_version = np.fromfile(fid, dtype="uint8", count=1)[0]
        minor_version = np.fromfile(fid, dtype="uint8", count=1)[0]

        npy_version = np.array([major_version, minor_version])

        # Read header length
        header_length = np.fromfile(fid, dtype="uint16", count=1)[0]

        total_header_length = 10 + header_length

        # Read header content
        header_content = fid.read(header_length).decode("latin1")

        # Parse header content
        import re

        # Parse dtype
        r = re.search(r"'descr'\s*:\s*'(.*?)'", header_content)
        if r:
            dt_npy = r.group(1)
            little_endian = dt_npy[0] != ">"
            data_type = dtypes_numpy.get(dt_npy[1:], "float64")  # Default to float64 if not found
        else:
            raise ValueError("Cannot parse dtype information from header")

        # Parse fortran order
        r = re.search(r"'fortran_order'\s*:\s*(\w+)", header_content)
        if r:
            fortran_order = r.group(1) == "True"
        else:
            raise ValueError("Cannot parse fortran_order information from header")

        # Parse shape
        r = re.search(r"'shape'\s*:\s*\((.*?)\)", header_content)
        if r:
            shape_str = r.group(1)
            shape_str = shape_str.replace("L", "")  # Remove 'L' suffixes from integers
            array_shape = tuple(int(num) for num in shape_str.split(", ") if num)
        else:
            raise ValueError("Cannot parse shape information from header")

    return array_shape, data_type, fortran_order, little_endian, total_header_length, npy_version
