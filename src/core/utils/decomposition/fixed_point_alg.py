import numpy as np
from numba import jit


# Pre-compile the math functions to avoid JIT compilation overhead during execution
@jit(nopython=True, cache=True)
def square(x):
    return x * x


@jit(nopython=True, cache=True)
def skew(x):
    return x**3 / 3


@jit(nopython=True, cache=True)
def logcosh(x):
    return np.tanh(x)


@jit(nopython=True, cache=True)
def dot_square(x):
    return 2 * x


@jit(nopython=True, cache=True)
def dot_skew(x):
    return 2 * x**2 / 3


@jit(nopython=True, cache=True)
def dot_logcosh(x):
    return 1 - np.tanh(x) ** 2


# Highly optimized fixed point algorithm
@jit(nopython=True, fastmath=True, cache=True, parallel=False)
def _fixed_point_core(w, X, B, cf_func_id, maxiter=500):
    """
    Efficient implementation of fixed point algorithm.

    Args:
        w: Initial separation vector (flattened)
        X: Whitened signal matrix
        B: Basis matrix
        cf_func_id: 0=skew, 1=kurtosis, 2=logcosh
        maxiter: Maximum iterations

    Returns:
        w: Updated separation vector
    """
    n_features, n_samples = X.shape
    tolerance = 1e-4

    # Pre-compute B*B^T once outside the loop
    BBT = B @ B.T

    # Pre-allocate arrays for intermediate values
    w_old = np.zeros(w.shape[0], dtype=w.dtype)
    w_new = np.zeros(w.shape[0], dtype=w.dtype)

    # Pre-compute buffer for X @ g_wx calculations
    buffer = np.zeros(n_features)
    counter = 1

    # Main iteration loop
    while counter < maxiter:
        # Store previous w
        for i in range(w.shape[0]):
            w_old[i] = w[i]

        # Calculate w^T * X
        wTX = w.T @ X

        # Apply contrast function based on ID
        if cf_func_id == 0:  # skew
            g_wx = wTX**2
            mean_gp = np.mean(2 * wTX)
        elif cf_func_id == 1:  # kurtosis
            g_wx = wTX**3
            mean_gp = np.mean(3 * wTX**2)
        else:  # logcosh
            g_wx = np.log(np.cosh(wTX))
            mean_gp = np.mean(np.tanh(wTX))

        # Calculate X @ g_wx for the new w (faster than naive matrix multiplication)
        buffer.fill(0)
        for i in range(n_samples):
            for j in range(n_features):
                buffer[j] += X[j, i] * g_wx[i]

        # Normalize by sample count
        buffer /= n_samples

        # Subtract A*w_old
        for j in range(n_features):
            w_new[j] = buffer[j] - mean_gp * w_old[j]

        # Orthogonalize against existing sources
        w_new = w_new - BBT @ w_new

        # Normalize
        norm = np.sqrt(np.sum(w_new**2))
        if norm > 1e-10:  # Avoid division by near-zero
            w_new = w_new / norm

        # Check for convergence
        angle = np.abs(np.dot(w_new, w_old))
        if np.abs(angle - 1.0) <= tolerance:
            break

        # Update w for next iteration
        for j in range(n_features):
            w[j] = w_new[j]
        counter += 1

    return w_new


def fixed_point_alg(w, B, X, cf_type, its=500):
    """
    Drop-in replacement for the original fixed_point_alg function with optimized implementation.

    Args:
        w: Initial separation vector
        B: Basis matrix of previously found separation vectors
        X: Whitened signal matrix
        cf_type: Contrast function
        its: Maximum iterations

    Returns:
        w: Updated separation vector
    """
    # Ensure inputs are properly formatted
    w_flat = w.ravel()

    # Ensure arrays are in C-contiguous format for Numba
    if not X.flags.c_contiguous:
        X = np.ascontiguousarray(X)
    if not B.flags.c_contiguous:
        B = np.ascontiguousarray(B)

    # Map contrast function based on the input function objects
    # This checks identity of function objects to determine which one was passed
    if cf_type == "skew":
        cf_id = 0
    elif cf_type == "kurtosis":
        cf_id = 1
    elif cf_type == "logcosh":
        cf_id = 2
    else:
        raise ValueError(f"Unknown contrast function '{cf_type}'")

    # Run optimized core algorithm
    result = _fixed_point_core(w_flat.copy(), X, B, cf_id, its)
    # Return in the original format expected by the caller
    return result
