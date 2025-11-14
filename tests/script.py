import re
import numpy as np
import scipy.io as sio
from pathlib import Path
from pandas import pd

# the file path assumes in the test folder
# also, matlab and python debug outputs have already
# been produced. see readme under testing to learn more
matlab_dir = Path("matlab_output/debug_outputs")
python_dir = Path("python_output/debug_outputs")
output_csv = Path("fastICA_comparison_summary2.csv")

# this is the pattern is for fast ICA algorithm
fast_ICA_pattern = re.compile(
    r"fast_ICA_and_CKC_electrode_(\d+)_interval_(\d+)_iteration_(\d+)_sub_iteration_(\d+)\.mat"
)

results = []

def extract_numeric_array(x):
    return np.ravel(x).astype(float)

# def extract_numeric_array(x):
#     if isinstance(x, np.ndarray):
#         if x.dtype == object:
#             inner = [extract_numeric_array(xx) for xx in x.flat if xx is not None]
#             return np.concatenate(inner).ravel() if inner else np.array([])
#         return np.ravel(x).astype(float)
#     return np.atleast_1d(np.array(x, dtype=float))


for mat_file in sorted(matlab_dir.glob("fast_ICA_and_CKC_electrode_*_interval_*_iteration_*_sub_iteration_*.mat")):
    
    m = fast_ICA_pattern.search(mat_file.name)
    if not m:
        continue
    electrode, interval, iteration, sub_it = map(int, m.groups())
    base_key = f"electrode_{electrode}_interval_{interval}_iteration_{iteration}_sub_iteration_{sub_it}"
    py_candidates = list(python_dir.glob(f"*{base_key}*.mat"))
    if not py_candidates:
        print(f"⚠️ No Python file found for {mat_file.name}")
        continue


    py_file = py_candidates[0]
    print(f"Matched {mat_file.name}")

    try:
        mat = sio.loadmat(mat_file)
        py = sio.loadmat(py_file)
    except Exception as e:
        print(f"Error loading {mat_file.name}: {e}")
        continue

    # --- Compare only overlapping variable names ---
    common_vars = [
        v for v in mat.keys()
        if v in py.keys() and not v.startswith("__")
    ]
    if not common_vars:
        print(f"No shared variable names for {mat_file.name}")
        continue

    for var in common_vars:
        w_mat = extract_numeric_array(mat[var])
        w_py = extract_numeric_array(py[var])

        if w_mat.size == 0 or w_py.size == 0:
            continue

        n = min(w_mat.size, w_py.size)
        w_mat, w_py = w_mat[:n], w_py[:n]
        corr = np.corrcoef(w_mat, w_py)[0, 1]
        dot = float(np.dot(w_mat, w_py))
        norm_ratio = float(np.linalg.norm(w_py) / np.linalg.norm(w_mat))
        angle_deg = float(np.degrees(np.arccos(
            np.clip(dot / (np.linalg.norm(w_mat) * np.linalg.norm(w_py)), -1, 1)
        )))

        results.append({
            "electrode": electrode,
            "iteration": iteration,
            "sub_iteration": sub_it,
            "variable": var,
            "correlation": corr,
            "angle_deg": angle_deg,
            "norm_ratio": norm_ratio,
        })

# # === EXPORT RESULTS ===
# if results:
#     df = pd.DataFrame(results)
#     df.sort_values(["electrode", "iteration", "sub_iteration", "variable"], inplace=True)
#     df.to_csv(output_csv, index=False)
#     print(f"\n✅ Comparison summary saved to {output_csv}")
#     print(df.head(15))
# else:
#     print("No matching files or results found.")
