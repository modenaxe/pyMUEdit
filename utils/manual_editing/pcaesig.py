import numpy as np


def pcaesig(signal):
    """
    Performs Principal Component Analysis (PCA) on the signal.

    Args:
        signal: Input signal matrix

    Returns:
        E: Eigenvectors matrix
        D: Diagonal matrix of eigenvalues
    """
    # Calculate covariance matrix exactly as MATLAB does
    covarianceMatrix = np.cov(signal, rowvar=True, bias=True)

    # Perform eigendecomposition
    eigenvalues, E = np.linalg.eigh(covarianceMatrix)

    # Sort eigenvalues and eigenvectors (descending)
    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    E = E[:, idx]

    # Create diagonal matrix of eigenvalues
    D = np.diag(eigenvalues)

    # Determine rank tolerance exactly as MATLAB
    rankTolerance = np.mean(eigenvalues[len(eigenvalues) // 2 :])
    if rankTolerance < 0:
        rankTolerance = 0

    # Find threshold for eigenvalue selection
    maxLastEig = np.sum(np.diag(D) > rankTolerance)
    if maxLastEig < signal.shape[0]:
        lowerLimitValue = (eigenvalues[maxLastEig] + eigenvalues[maxLastEig + 1]) / 2
    else:
        lowerLimitValue = 0

    # Select eigenvectors based on eigenvalues
    mask = np.diag(D) > lowerLimitValue
    E = E[:, mask]
    D = D[mask, :][:, mask]

    return E, D
