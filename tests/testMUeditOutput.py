# 0. Copy input data (e.g. trial1_20MVC.otb+ into tests folder)
# 1. generate muedit output:
#   a) cd into tests folder
#   b) edit parameters in gen_muedit_output.m file to reflect what you want to test
#   c) run in terminal ==> "C:\...\matlab.exe" -nodisplay -nosplash -nodesktop -r "run('gen_muedit_output.m'); exit();"
# 2. generate pymuedit output (this software):
#   a) run src/main.py, change input parameters (e.g. iterations, ref signal, initialisation, filters, etc. to match muedit inputs)
#   b) save results in tests folder
# -- You should now have two .mat output files in tests folder; actual output (pymuedit) and expected output (muedit)

# 3. run testMUeditOutput.py to compare these two files

# Tests folder file structure should look like the following after (excluding other test files which are not used in this process):
# tests/
#   ActualFinalOutxyz.mat
#   ExpFinalOutxyz.mat
#   gen_muedit_output.m
#   testMUeditOutput.py
#   xyz.otb+

import numpy as np
from scipy.io import loadmat

# === File Paths (CHANGE AS NEEDED) ===
FILE_1 = 'ActualFinalOut20_10iters.mat' #pymuedit output
FILE_2 = 'ExpFinalOut20-10_iters.mat'   #muedit output

# === fields to compare inside the 'signal' struct (some i have left out as they are unlikely to change (i.e. fsamp, IED, etc))===
FIELDS_TO_COMPARE = [
    'data', 'auxiliary', 'path', 'target',
    'coordinates', 'EMGmask', 'Pulsetrain', 'Dischargetimes'
]

def load_mat_signal(file_path):
    """Load the 'signal' struct from a .mat file."""
    mat = loadmat(file_path, struct_as_record=False, squeeze_me=True)
    if 'signal' not in mat:
        raise ValueError(f"No 'signal' struct found in {file_path}")
    return mat['signal']

def is_cell_array(obj):
    """Check if the object is a MATLAB-style cell array."""
    return isinstance(obj, np.ndarray) and obj.dtype == object

def compare_arrays(arr1, arr2, field_path="", atol=1e-8, rtol=1e-5):
    """Compare arrays or nested cells recursively."""
    differences = []

    if is_cell_array(arr1) and is_cell_array(arr2):
        if arr1.shape != arr2.shape:
            differences.append(f"{field_path}: Cell shape mismatch {arr1.shape} vs {arr2.shape}")
            return differences
        for idx in np.ndindex(arr1.shape):
            a = arr1[idx]
            b = arr2[idx]
            subfield = f"{field_path}[{idx}]"
            differences.extend(compare_arrays(a, b, subfield, atol, rtol))

    elif isinstance(arr1, np.ndarray) and isinstance(arr2, np.ndarray):
        if arr1.shape != arr2.shape:
            differences.append(f"{field_path}: Array shape mismatch {arr1.shape} vs {arr2.shape}")
        elif not np.allclose(arr1, arr2, atol=atol, rtol=rtol, equal_nan=True):
            max_diff = np.max(np.abs(arr1 - arr2))
            mean_diff = np.mean(np.abs(arr1 - arr2))
            differences.append(
                f"{field_path}: Values differ (max diff = {max_diff:.3e}, mean diff = {mean_diff:.3e})"
            )

    else:
        # Convert both to arrays to allow broadcastable comparison
        a1 = np.atleast_1d(arr1)
        a2 = np.atleast_1d(arr2)

        if a1.shape != a2.shape:
            differences.append(f"{field_path}: Shape mismatch for scalar values {a1.shape} vs {a2.shape}")
        elif not np.allclose(a1, a2, atol=atol, rtol=rtol, equal_nan=True):
            max_diff = np.max(np.abs(a1 - a2))
            mean_diff = np.mean(np.abs(a1 - a2))
            differences.append(
                f"{field_path}: Scalar values differ (max diff = {max_diff:.3e}, mean diff = {mean_diff:.3e})"
            )

    return differences

def compare_signals(signal1, signal2):
    """Compare key fields in two signal structs."""
    all_differences = {}
    for field in FIELDS_TO_COMPARE:
        val1 = getattr(signal1, field, None)
        val2 = getattr(signal2, field, None)

        if val1 is None or val2 is None:
            all_differences[field] = [f"{field}: Missing in one of the signals."]
            continue

        diffs = compare_arrays(val1, val2, field_path=field)
        if diffs:
            all_differences[field] = diffs

    return all_differences

if __name__ == "__main__":
    print(f"Comparing '{FILE_1}' vs '{FILE_2}'...\n")
    try:
        signal1 = load_mat_signal(FILE_1)
        signal2 = load_mat_signal(FILE_2)
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        exit(1)

    differences = compare_signals(signal1, signal2)

    if not differences:
        print("✅ All selected fields are equal within tolerance.")
    else:
        print("❌ Differences found:\n")

        for field, diffs in differences.items():
            print(f"Field: {field} ({len(diffs)} difference{'s' if len(diffs) > 1 else ''})")
            for diff in diffs:
                print("  -", diff)
            print()

        passed_fields = [f for f in FIELDS_TO_COMPARE if f not in differences]
        if passed_fields:
            print("✅ Fields with no differences:", ", ".join(passed_fields))