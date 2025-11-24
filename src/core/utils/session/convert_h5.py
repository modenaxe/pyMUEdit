import json
import h5py
import numpy as np
import traceback
import os
import ast
from core.logger import logger

def save_as_h5(signal_dict, output_path, raw_filepath=None, config=None):
    """
    Save nested dictionary structure to HDF5 file
    """
    try:
        with h5py.File(output_path, 'w') as f:
            # Recursively save the dictionary
            _save_dict_to_h5(f, signal_dict)

            # Save metadata as attributes
            if raw_filepath:
                f.attrs['raw_filepath'] = os.path.abspath(raw_filepath)
            if config:
                try:
                    f.attrs['config'] = json.dumps(config)
                except Exception as e:
                    logger.warning(f"Error saving 'config' attribute: {e}")
                    traceback.print_exc()

        logger.debug(f"Successfully saved HDF5 file at {output_path}")
    except Exception as e:
        logger.warning(f"Error during saving HDF5 file at {output_path}:")
        traceback.print_exc()


def _save_dict_to_h5(h5_group, data_dict):
    """
    Recursively save dictionary to HDF5 group
    """
    for key, value in data_dict.items():
        try:
            if value is None:
                h5_group.attrs[f"{key}_is_none"] = True

            elif isinstance(value, dict):
                subgroup = h5_group.create_group(key)
                _save_dict_to_h5(subgroup, value)

            elif isinstance(value, np.ndarray):
                # Handle different numpy array types
                if value.dtype.kind == 'U':  # Unicode string
                    value_bytes = value.astype('S')
                    h5_group.create_dataset(key, data=value_bytes)
                elif value.dtype.kind == 'O':  # Object arrays (mixed types)
                    try:
                        str_array = np.array([str(item) for item in value.flat]).reshape(value.shape)
                        h5_group.create_dataset(key, data=str_array.astype('S'))
                    except:
                        # Save as JSON if conversion fails
                        h5_group.attrs[key] = json.dumps(value.tolist())
                else:
                    h5_group.create_dataset(key, data=value)

            elif isinstance(value, (list, tuple)):
                # Try to convert to numpy array
                try:
                    arr = np.array(value)
                    # Check if it's a string array
                    if arr.dtype.kind == 'U':
                        arr = arr.astype('S')
                    h5_group.create_dataset(key, data=arr)
                except (ValueError, TypeError):
                    h5_group.attrs[key] = json.dumps(value)

            elif isinstance(value, (int, float, bool, np.integer, np.floating)):
                h5_group.attrs[key] = value

            elif isinstance(value, str):
                if len(value) < 64000:  # HDF5 attribute size limit
                    h5_group.attrs[key] = value
                else:
                    h5_group.create_dataset(key, data=np.string_(value))
            else:
                try:
                    h5_group.attrs[key] = json.dumps(value)
                except (TypeError, ValueError):
                    h5_group.attrs[key] = str(value)

        except Exception as e:
            logger.warning(f"Error saving key '{key}': {e}")
            traceback.print_exc()


def load_from_h5(filepath):
    """
    Load HDF5 file back to nested dictionary structure
    """
    signal_dict = {}
    raw_filepath = None
    config_dict = None

    try:
        with h5py.File(filepath, 'r') as f:
            # Recursively load the structure
            signal_dict = _load_h5_to_dict(f)

            # Load metadata attributes
            if 'raw_filepath' in f.attrs:
                raw_filepath = str(f.attrs['raw_filepath'])

            if 'config' in f.attrs:
                config_str = str(f.attrs['config'])
                try:
                    config_dict = json.loads(config_str)
                except json.JSONDecodeError:
                    logger.warning("Warning: Could not parse config JSON")
                    config_dict = None

    except Exception as e:
        logger.warning(f"Error loading HDF5 file: {e}")
        traceback.print_exc()

    return signal_dict, raw_filepath, config_dict


def _load_h5_to_dict(h5_group):
    """
    Recursively load HDF5 group to dictionary
    """
    result = {}

    # Load datasets and subgroups
    for key in h5_group.keys():
        item = h5_group[key]

        if isinstance(item, h5py.Group):
            result[key] = _load_h5_to_dict(item)

        elif isinstance(item, h5py.Dataset):
            data = item[()]

            # Convert bytes back to strings if needed
            if isinstance(data, bytes):
                result[key] = data.decode('utf-8')
            elif isinstance(data, np.ndarray) and data.dtype.kind == 'S':
                # Byte string array
                try:
                    result[key] = np.char.decode(data, 'utf-8')
                except:
                    result[key] = data
            else:
                result[key] = data

    # Load attributes
    for key, value in h5_group.attrs.items():
        # Skip special metadata keys at root level only
        if key in ('raw_filepath', 'config') and h5_group.file == h5_group:
            continue

        # Handle None values
        if key.endswith('_is_none'):
            original_key = key[:-8]
            result[original_key] = None
            continue

        if isinstance(value, str):
            parsed_value = _parse_string_value(value)
            if parsed_value is not value:
                result[key] = parsed_value
                continue

        # Try to convert to numeric types
        if isinstance(value, str):
            try:
                result[key] = int(value)
                continue
            except (ValueError, TypeError):
                try:
                    result[key] = float(value)
                    continue
                except (ValueError, TypeError):
                    pass

        result[key] = value

    return result


def _parse_string_value(value):
    """
    Try to parse a string value as JSON or Python literal
    Returns the parsed value, or the original value if parsing fails
    """
    if not isinstance(value, str):
        return value

    if value.startswith(('[', '{')):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass

    if value.startswith('('):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass

    return value