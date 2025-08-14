'''
Test command:
python -m unittest TestH5pyConvert.py -v
'''

import unittest
import numpy as np
import h5py
import tempfile
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.utils.manual_editing.h5_import import h5py_convert


class TestH5pyConvert(unittest.TestCase):

    def setUp(self):
        # Create a temporary HDF5 file
        self.tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".h5")
        with h5py.File(self.tmpfile.name, "w") as f:
            # Common datasets
            f.create_dataset("scalar", data=42)
            f.create_dataset("array", data=np.array([1, 2, 3]))

            # Nested group
            grp = f.create_group("group1")
            grp.create_dataset("subdata", data=np.array([[10], [20]]))  # 2D, shape(N,1)

            # Reference Dataset
            ref_dtype = h5py.ref_dtype
            dset_ref_target = f.create_dataset("ref_target", data=np.array([100, 200]))
            ref = dset_ref_target.ref  # 获取 reference
            f.create_dataset("ref_dataset", shape=(1,), dtype=ref_dtype)
            f["ref_dataset"][0] = ref

        self.converter = h5py_convert()

    def tearDown(self):
        self.tmpfile.close()  # Close the temporary file object first
        try:
            os.unlink(self.tmpfile.name)
        except PermissionError:
            import time
            time.sleep(0.1)
            os.unlink(self.tmpfile.name)

    def test_scalar_dataset(self):
        with h5py.File(self.tmpfile.name, "r") as f:
            result = self.converter.h5py_to_dict(f["scalar"])
            self.assertEqual(result, 42)

    def test_array_dataset(self):
        with h5py.File(self.tmpfile.name, "r") as f:
            result = self.converter.h5py_to_dict(f["array"])
            np.testing.assert_array_equal(result, np.array([1, 2, 3]))

    def test_group_conversion(self):
        with h5py.File(self.tmpfile.name, "r") as f:
            result = self.converter.h5py_to_dict(f["group1"])
            # subdata will be flattened into a one-dimensional list because shape(N,1) will remove the second dimension.
            self.assertEqual(result["subdata"].tolist(), [[10], [20]])

    def test_reference_dataset(self):
        with h5py.File(self.tmpfile.name, "r") as f:
            result = self.converter.h5py_to_dict(f["ref_dataset"])
            # After reference resolution, the data should be ref_target
            self.assertEqual(result, [[100, 200]])


if __name__ == '__main__':
    unittest.main()