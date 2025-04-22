import numpy as np
import scipy


def whiten_emg(signal):
    """
    Whitens the EMG signal for decorrelation.

    Imposes a signal covariance matrix equal to the identity matrix at time lag zero.
    This shrinks large directions of variance and expands small directions of variance,
    effectively decorrelating the data.
    """

    cov_mat = np.cov(np.squeeze(signal), bias=True)
    # get the eigenvalues and eigenvectors of the covariance matrix
    evalues, evectors = scipy.linalg.eigh(cov_mat)
    # in MATLAB: eig(A) returns diagonal matrix D of eigenvalues and matrix V whose columns are the corresponding right eigenvectors, so that A*V = V*D

    sorted_evalues = np.sort(evalues)[::-1]
    penalty = np.mean(sorted_evalues[len(sorted_evalues) // 2 :])  # int won't wokr for odd numbers
    penalty = max(0, penalty)

    rank_limit = np.sum(evalues > penalty) - 1
    if rank_limit < np.shape(signal)[0]:
        hard_limit = (np.real(sorted_evalues[rank_limit]) + np.real(sorted_evalues[rank_limit + 1])) / 2

    # use the rank limit to segment the eigenvalues and the eigenvectors
    evectors = evectors[:, evalues > hard_limit]
    evalues = evalues[evalues > hard_limit]
    diag_mat = np.diag(evalues)
    whitening_mat = evectors @ np.linalg.inv(np.sqrt(diag_mat)) @ np.transpose(evectors)
    dewhitening_mat = evectors @ np.sqrt(diag_mat) @ np.transpose(evectors)
    whitened_emg = np.matmul(whitening_mat, signal).real

    return whitened_emg, whitening_mat, dewhitening_mat
