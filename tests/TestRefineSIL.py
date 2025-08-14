'''
Test command:
python -m unittest TestRefineSIL.py -v
'''
# test refinesil
import unittest
import numpy as np
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.utils.manual_editing.refinesil import refinesil

class TestRefineSIL(unittest.TestCase):
    def setUp(self):
        self.fsamp = 1000
        duration = 3
        t = np.arange(0, duration, 1/self.fsamp)
        self.PulseT = 0.1 * np.random.randn(len(t))
        self.PulseT[::500] += 2
        self.distime = np.arange(0, len(t), 500)

    def test_output_shape(self):
        sil_vals = refinesil(self.PulseT, self.distime, self.fsamp)
        self.assertEqual(sil_vals.shape[1], 2)
        self.assertEqual(sil_vals.shape[0], 3)  # duration = 3s

    def test_values(self):
        sil_vals = refinesil(self.PulseT, self.distime, self.fsamp)
        self.assertTrue(np.all(np.isfinite(sil_vals[:,0])))
        self.assertTrue(np.any(~np.isnan(sil_vals[:,1])))

if __name__ == '__main__':
    unittest.main()
