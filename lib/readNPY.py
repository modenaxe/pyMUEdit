import numpy as np
from lib.readNPYheader import readNPYheader


def readNPY(filename):
    shape, dataType, fortranOrder, littleEndian, totalHeaderLength, _ = readNPYheader(filename)

    if littleEndian:
        endian = "<"
    else:
        endian = ">"

    with open(filename, "rb") as fid:
        # Skip the header
        fid.seek(totalHeaderLength)

        # Read the data
        if dataType == "string":  # Assume 513 bytes
            stringLength = 513
            rawData = np.fromfile(fid, dtype=np.int8)
            data = np.empty(len(rawData) // stringLength, dtype=object)

            for n in range(len(data)):
                nonzero_vals = rawData[(n * stringLength) : (n + 1) * stringLength]
                nonzero_vals = nonzero_vals[nonzero_vals != 0]
                text = "".join([chr(val) for val in nonzero_vals])
                data[n] = text
        else:
            data = np.fromfile(fid, dtype=np.dtype(endian + dataType))

        if len(shape) > 1 and not fortranOrder:
            data = data.reshape(shape[::-1])
            data = data.transpose(range(len(shape) - 1, -1, -1))
        elif len(shape) > 1:
            data = data.reshape(shape)

    return data
