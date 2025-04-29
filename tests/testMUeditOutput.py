import filecmp
from scipy.io import loadmat
import numpy as np
import os

def compare_mat_files(file1, file2):

    expected = loadmat(file1)
    output = loadmat(file2)

    # Remove MATLAB metadata entries
    for key in ['__header__', '__version__', '__globals__']:
        expected.pop(key, None)
        output.pop(key, None)

    if expected.keys() != output.keys():
        return False

    for key in expected:
        print(key, "|", expected[key])
        print('///////////////////')
        print(output[key])
        # if not np.array_equal(expected[key], output[key]):
        #    print(f"Difference found in variable: {key}")
        #    return False

    return True
#################
print("Current working directory:", os.getcwd())
data1 = os.path.join('data', 'io', 'input_decomposition', 'trial1_20MVC.otb+_decomp.mat')
data2 = os.path.join('data', 'io', 'input_decomposition', 'trial1_20MVC.otb+_decomp.mat')
if compare_mat_files(data1, data2):
    print("Files are the same ✅")
else:
    print("Files are different ❌")






# filecmp.cmp(expected, output, shallow=False)