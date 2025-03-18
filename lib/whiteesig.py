import numpy as np


def whiteesig(signal, E, D):
    # Calculate the whitening matrix
    D_inv_sqrt = np.linalg.inv(np.sqrt(D))
    whiteningMatrix = E @ D_inv_sqrt @ E.T

    # Calculate the dewhitening matrix
    D_sqrt = np.sqrt(D)
    dewhiteningMatrix = E @ D_sqrt @ E.T

    # Whiten the signal
    whitensignals = whiteningMatrix @ signal

    return whitensignals, whiteningMatrix, dewhiteningMatrix
