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

def load_from_h5(filepath):
    signal_dict = {}
    raw_filepath = None

    with h5py.File(filepath, 'r') as f:
        for key, item in f.items():
            if isinstance(item, h5py.Dataset):
                signal_dict[key] = np.array(item)

        for key, value in f.attrs.items():
            if key == "raw_filepath":
                raw_filepath = str(value)
            else:
                try:
                    val = int(value)
                except ValueError:
                    try:
                        val = float(value)
                    except ValueError:
                        val = str(value)
                signal_dict[key] = val

    return signal_dict, raw_filepath
