import numpy as np
from utils.decomposition.extend_emg import extend_emg


def get_mu_filters(data, rejected_channels, discharge_times, chans_per_electrode, g):
    """
    Recalculates motor unit filters using discharge times.

    Used in post-processing to refine motor unit templates.
    """

    data_slice = data[chans_per_electrode[g] * (g) : (g + 1) * chans_per_electrode[g], :]
    rejected_channels_slice = rejected_channels[g] == 1
    cleaned_data = np.delete(data_slice, rejected_channels_slice, 0)

    # get the first estimate of pulse trains using the previously derived mu filters, applied to the emg data
    ext_factor = int(np.round(1500 / np.shape(cleaned_data)[0]))
    extended_data = np.zeros([1, np.shape(cleaned_data)[0] * (ext_factor), np.shape(cleaned_data)[1] + ext_factor - 1])
    extended_data = extend_emg(extended_data, cleaned_data, ext_factor)

    # recalculate MU filters
    mu_filters = np.zeros(np.shape(extended_data)[0], np.shape(discharge_times)[1])  # type:ignore
    for mu in range(np.shape(discharge_times)[1]):
        mu_filters[:, mu] = np.sum(extended_data[:, discharge_times[:, mu]], axis=1)
