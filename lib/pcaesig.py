import numpy as np


def pcaesig(signal):
    covarianceMatrix = np.cov(signal.T, ddof=1)
    eigenvalues, E = np.linalg.eig(covarianceMatrix)

    # Sort the eigenvalues - descending
    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    E = E[:, idx]

    # Create diagonal matrix of eigenvalues
    D = np.diag(eigenvalues)

    # Calculate regularization tolerance
    rankTolerance = np.mean(eigenvalues[len(eigenvalues) // 2 :])
    if rankTolerance < 0:
        rankTolerance = 0

    maxLastEig = np.sum(np.diag(D) > rankTolerance)
    if maxLastEig < signal.shape[0]:
        lowerLimitValue = (eigenvalues[maxLastEig] + eigenvalues[maxLastEig + 1]) / 2
    else:
        lowerLimitValue = 0

    # Select the columns which correspond to the desired range of eigenvalues
    mask = np.diag(D) > lowerLimitValue
    E = E[:, mask]
    D = D[mask, :][:, mask]

    return E, D
