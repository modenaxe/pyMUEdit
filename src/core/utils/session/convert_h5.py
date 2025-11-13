import json
import h5py
import numpy as np
import os

def save_as_h5(signal_dict, output_path, raw_filepath=None, config=None):
    with h5py.File(output_path, 'w') as f:
        for key, value in signal_dict.items():
            if isinstance(value, np.ndarray):
                if value.dtype.kind == 'U':
                    value_bytes = value.astype('S')
                    f.create_dataset(key, data=value_bytes)
                elif value.dtype.kind in ('S', 'O'):
                    f.create_dataset(key, data=value)
                else:
                    f.create_dataset(key, data=value)
            else:
                if isinstance(value, str):
                    f.create_dataset(key, data=np.string_(value))
                else:
                    f.attrs[key] = str(value)
        if raw_filepath:
            f.attrs['raw_filepath'] = os.path.abspath(raw_filepath)
        if config:
            f.attrs['config'] = json.dumps(config)

def load_from_h5(filepath):
    signal_dict = {}
    raw_filepath = None
    config_str = None

    with h5py.File(filepath, 'r') as f:
        for key, item in f.items():
            if isinstance(item, h5py.Dataset):
                signal_dict[key] = np.array(item)
        for key, value in f.attrs.items():
            if key == "raw_filepath":
                raw_filepath = str(value)
            elif key == "config":
                config_str = str(value)
            else:
                try:
                    val = int(value)
                except ValueError:
                    try:
                        val = float(value)
                    except ValueError:
                        val = str(value)
                signal_dict[key] = val
    config_dict = None
    if config_str:
        import json
        config_dict = json.loads(config_str)
    return signal_dict, raw_filepath, config_dict
