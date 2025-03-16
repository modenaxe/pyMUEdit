import numpy as np


def extend(eY, exfactor):
    rows_eY, cols_eY = eY.shape
    esample = np.zeros((rows_eY * exfactor, cols_eY + exfactor - 1))

    for m in range(1, exfactor + 1):
        start_row = (m - 1) * rows_eY
        end_row = m * rows_eY
        start_col = m - 1
        end_col = cols_eY + m - 1
        esample[start_row:end_row, start_col:end_col] = eY

    return esample
