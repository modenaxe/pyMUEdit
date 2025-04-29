import filecmp
from scipy.io import loadmat
import numpy as np
import os
import h5py

def load_mat_v73(filename):
    data = {}
    with h5py.File(filename, 'r') as f:
        for key in f.keys():
            if isinstance(f[key], h5py.Group):
                data[key] = {k: np.array(f[key][k]) for k in f[key].keys() if isinstance(f[key][k], h5py.Dataset)}
            elif isinstance(f[key], h5py.Dataset):
                data[key] = np.array(f[key])
    return data




def compare_mat_files(file1, file2):

    expected = load_mat_v73(file1)
    output = loadmat(file2)
    #debug
    #print(expected)
    print('///////////////////')
    #print(output[key])

    # Remove MATLAB metadata entries
    for key in ['__header__', '__version__', '__globals__', '#refs#']:
        expected.pop(key, None)
        output.pop(key, None)

    if expected.keys() != output.keys():
        print(expected.keys())
        print("//////////////////////////////")
        print(output.keys())
        return False

    for key in expected:
        print(key, "|", expected[key])
        print('///////////////////')
        print(output[key])
        if not np.array_equal(expected[key], output[key]):
            print(f"Difference found in variable: {key}")
            return False

    return True
#################
print("Current working directory:", os.getcwd())
data1 = os.path.join('data', 'io', 'input_decomposition', 'expectedoutput_trial1_20MVC.otb+_decomp.mat')
data2 = os.path.join('data', 'io', 'input_decomposition', 'trial1_20MVC.otb+_output_decomp.mat')
if compare_mat_files(data1, data2):
    print("Files are the same ✅")
else:
    print("Files are different ❌")






# filecmp.cmp(expected, output, shallow=False)