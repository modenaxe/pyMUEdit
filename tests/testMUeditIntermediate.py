# See README.md for usage instructions.

from glob import glob

import numpy as np
import numpy.testing as npt
from natsort import natsorted
from scipy.io import loadmat

if __name__ == "__main__":

    for filename in natsorted(set(glob("*.mat", root_dir="debug_outputs")) & set(glob("*.mat", root_dir="../src/data1/decomp_output/debug_outputs"))):
        print(filename)
        expected = loadmat(f"debug_outputs/{filename}", squeeze_me=True)
        actual = loadmat(f"../src/data1/decomp_output/debug_outputs/{filename}", squeeze_me=True)

        if "sub_iteration_2" in filename:
            npt.assert_array_equal(np.squeeze(actual["init_its_i"]), np.squeeze(expected["init_its_i"]) - 1)
            npt.assert_allclose(np.squeeze(actual["w_sep_vect_initial"]), np.squeeze(expected["w_sep_vect_initial"]))
        elif "sub_iteration_3" in filename:
            npt.assert_allclose(np.squeeze(actual["w_sep_vect_orthonormalized"]), np.squeeze(expected["w_sep_vect_orthonormalized"]), rtol=1e-6)
        elif "sub_iteration_4" in filename:
            npt.assert_allclose(np.squeeze(actual["w_sep_vect_after_fpa"]), np.squeeze(expected["w_sep_vect_after_fpa"]), rtol=1e-6)
        else:
            print("warning: ignored")
