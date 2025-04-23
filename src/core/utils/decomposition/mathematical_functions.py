import numpy as np
import numba


@numba.njit
def square(x):
    """
    Computes the square of input values.
    Used as a contrast function in FastICA.
    """
    return np.square(x)


@numba.njit
def skew(x):
    """
    Computes the skewness-related function (x^3/3).
    Used as a contrast function in FastICA.
    """
    return x**3 / 3


@numba.njit
def exp(x):
    """
    Computes exponential function e^(-x^2/2).
    Used as a contrast function in FastICA.
    """
    return np.exp(-np.square(x) / 2)


@numba.njit
def logcosh(x):
    """
    Computes the hyperbolic tangent of the input.
    Used as a contrast function in FastICA.
    """
    return np.tanh(x)
    # return np.log(np.cosh(x))


@numba.njit
def dot_square(x):
    """
    Computes the derivative of the square function.
    Used in FastICA when the square contrast function is selected.
    """
    return 2 * x


@numba.njit
def dot_skew(x):
    """
    Computes the derivative of the skew function.
    Used in FastICA when the skew contrast function is selected.
    """
    return 2 * (np.square(x)) / 3


@numba.njit
def dot_exp(x):
    """
    Computes the derivative of the exp function.
    Used in FastICA when the exp contrast function is selected.
    """
    return -1 * (np.exp(-np.square(x) / 2)) + np.dot((np.square(x)), np.exp(-np.square(x) / 2))


@numba.njit
def dot_logcosh(x):
    """
    Computes the derivative of the logcosh function.
    Used in FastICA when the logcosh contrast function is selected.
    """
    return 1 - np.square(np.tanh(x))
    # return np.tanh(x)
