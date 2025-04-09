import numpy as np
from scipy import linalg


def whiteesig(signal):
    """
    Whitening function for the EMG signal.

    Args:
        signal: Input EMG signal array

    Returns:
        whitened_emg: Whitened signal
        whitening_mat: Whitening matrix
        dewhitening_mat: Dewhitening matrix
    """
    if not signal.flags.c_contiguous:
        signal = np.ascontiguousarray(signal)

    # Get covariance matrix
    n_features = signal.shape[0]
    cov_mat = np.empty((n_features, n_features), dtype=signal.dtype)

    # covariance calculation
    scale = 1.0 / signal.shape[1]
    np.dot(signal, signal.T, out=cov_mat)
    cov_mat *= scale

    try:
        U, s, _ = linalg.svd(cov_mat, full_matrices=False, lapack_driver="gesvd")
    except:
        U, s, _ = np.linalg.svd(cov_mat, full_matrices=False)

    # Find regularization factor
    half_point = len(s) // 2
    penalty = np.mean(s[half_point:])
    penalty = max(0, penalty)  # type:ignore

    # Find rank limit
    rank_limit = np.sum(s > penalty)

    # Select only relevant eigenvectors/values
    U_filtered = U[:, :rank_limit]
    s_filtered = s[:rank_limit]

    # Pre-compute diagonals
    diag_sqrt_inv = np.diag(1.0 / np.sqrt(s_filtered))
    diag_sqrt = np.diag(np.sqrt(s_filtered))

    # Calculate matrices
    whitening_mat = U_filtered @ diag_sqrt_inv @ U_filtered.T
    dewhitening_mat = U_filtered @ diag_sqrt @ U_filtered.T

    # Compute whitened signal
    whitened_emg = whitening_mat @ signal

    return whitened_emg, whitening_mat, dewhitening_mat
