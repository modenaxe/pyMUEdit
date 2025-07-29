import numpy as np
import scipy.io
import h5py
import os

# === Hardcoded file paths ===
FILE_1 = 'ActualFinalOut20_10iters.mat'  # v7 file
FILE_2 = 'ExpFinalOut20-10_iters.mat'                 # v7.3 file (HDF5)

FIELDS_TO_COMPARE = [
    'data', 'auxiliary', 'path', 'target',
    'coordinates', 'EMGmask', 'Pulsetrain', 'Dischargetimes'
]

def load_mat_signal_v7(file_path):
    """Load signal struct from a v7 MATLAB file using scipy."""
    mat = scipy.io.loadmat(file_path, struct_as_record=False, squeeze_me=True)
    if 'signal' not in mat:
        raise ValueError(f"No 'signal' found in {file_path}")
    return mat['signal']

def load_mat_signal_v73(file_path):
    """Load signal group from a v7.3 MATLAB file using h5py."""
    with h5py.File(file_path, 'r') as f:
        if 'signal' not in f:
            raise ValueError(f"'signal' group not found in {file_path}")
        signal_group = f['signal']
        signal_data = {}

        for key in FIELDS_TO_COMPARE:
            if key in signal_group:
                data = signal_group[key]
                signal_data[key] = read_h5_dataset(data)
            else:
                signal_data[key] = None

        return signal_data

def read_h5_dataset(dataset):
    """Read HDF5 dataset and auto-transpose to match MATLAB v7 orientation."""
    if isinstance(dataset, h5py.Dataset):
        data = dataset[()]
        if isinstance(data, np.ndarray) and data.ndim >= 2:
            return data.T  # transpose to match MATLAB format
        return data
    elif isinstance(dataset, h5py.Group):
        return {k: read_h5_dataset(dataset[k]) for k in dataset.keys()}
    else:
        return dataset

def extract_field(signal_obj, field):
    """Extract field from scipy struct or dictionary."""
    if isinstance(signal_obj, dict):
        return signal_obj.get(field, None)
    else:
        return getattr(signal_obj, field, None)

def is_cell_array(obj):
    return isinstance(obj, np.ndarray) and obj.dtype == object

def flatten_if_1d_or_column(arr):
    if isinstance(arr, np.ndarray):
        if arr.ndim == 2 and 1 in arr.shape:
            return arr.flatten()
    return arr

def compare_arrays(arr1, arr2, field_path="", atol=1e-8, rtol=1e-5):
    differences = []

    arr1 = flatten_if_1d_or_column(arr1)
    arr2 = flatten_if_1d_or_column(arr2)

    if is_cell_array(arr1) and is_cell_array(arr2):
        if arr1.shape != arr2.shape:
            differences.append(f"{field_path}: Cell shape mismatch {arr1.shape} vs {arr2.shape}")
            return differences
        for idx, (a, b) in np.ndenumerate(zip(arr1.flat, arr2.flat)):
            subfield = f"{field_path}[{idx}]"
            differences.extend(compare_arrays(a, b, subfield, atol, rtol))
    elif isinstance(arr1, np.ndarray) and isinstance(arr2, np.ndarray):
        if arr1.shape != arr2.shape:
            differences.append(f"{field_path}: Shape mismatch {arr1.shape} vs {arr2.shape}")
        elif not np.allclose(arr1, arr2, atol=atol, rtol=rtol, equal_nan=True):
            max_diff = np.max(np.abs(arr1 - arr2))
            mean_diff = np.mean(np.abs(arr1 - arr2))
            differences.append(f"{field_path}: Value mismatch (max diff = {max_diff:.3e}, mean diff = {mean_diff:.3e})")
    else:
        if not np.allclose(np.atleast_1d(arr1), np.atleast_1d(arr2), atol=atol, rtol=rtol, equal_nan=True):
            differences.append(f"{field_path}: Scalar mismatch: {arr1} vs {arr2}")
    return differences

def compare_signals(signal1, signal2):
    differences = []
    for field in FIELDS_TO_COMPARE:
        val1 = extract_field(signal1, field)
        val2 = extract_field(signal2, field)

        if val1 is None or val2 is None:
            differences.append(f"{field}: Missing in one of the signals.")
            continue

        diffs = compare_arrays(val1, val2, field_path=field)
        differences.extend(diffs)

    return differences

if __name__ == "__main__":
    print(f"Comparing:\n  FILE_1: {FILE_1} (v7)\n  FILE_2: {FILE_2} (v7.3 HDF5)\n")

    try:
        signal1 = load_mat_signal_v7(FILE_1)
        signal2 = load_mat_signal_v73(FILE_2)
    except Exception as e:
        print(f"❌ Error loading signals: {e}")
        exit(1)

    differences = compare_signals(signal1, signal2)

    if not differences:
        print("✅ All selected fields are equal within tolerance.")
    else:
        print("❌ Differences found:")
        for diff in differences:
            print(" -", diff)