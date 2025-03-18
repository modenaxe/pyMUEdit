import numpy as np


def fixedpointalg(w, X, B, maxiter, contrastfunc):
    k = 1
    delta = np.ones(maxiter)
    TOL = 0.0001
    BBT = np.dot(B, B.T)

    # Define the contrast function and its derivative
    if contrastfunc == "skew":
        gp = lambda x: 2 * x
        g = lambda x: x**2
    elif contrastfunc == "kurtosis":
        gp = lambda x: 3 * x**2
        g = lambda x: x**3
    elif contrastfunc == "logcosh":
        gp = lambda x: np.tanh(x)
        g = lambda x: np.log(np.cosh(x))

    while delta[k - 1] > TOL and k < maxiter:
        # Save last weights
        wlast = w.copy()

        # Contrast function
        wTX = np.dot(w.T, X)
        A = np.mean(gp(wTX))

        # Update weights
        w = np.mean(X * g(wTX), axis=1, keepdims=True) - A * w

        # Orthogonalization
        w = w - np.dot(BBT, w)

        # Normalization
        w = w / np.linalg.norm(w)

        # Update convergence criteria
        k += 1
        delta[k - 1] = abs(np.dot(w.T, wlast) - 1)[0, 0]

    return w
