import h5py
import numpy as np
import os

def save_as_h5(signal_dict, output_path, raw_filepath=None):
    with h5py.File(output_path, 'w') as f:
        for key, value in signal_dict.items():
            if isinstance(value, np.ndarray):
                f.create_dataset(key, data=value)
            else:
                f.attrs[key] = str(value)

        if raw_filepath:
            f.attrs['raw_filepath'] = os.path.abspath(raw_filepath)