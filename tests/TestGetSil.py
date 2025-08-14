'''
Test command:
python -m unittest TestH5pyConvert.py -v
'''
# test getsil
import unittest
import numpy as np
import sys, os

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.utils.manual_editing.getsil import getsil


class TestGetSil(unittest.TestCase):
    def test_getsil_no_peaks(self):
        # All 0 data → no peak
        PulseT = np.zeros(1000)
        fsamp = 1000
        self.assertEqual(getsil(PulseT, fsamp), 0)

    def test_getsil_two_clusters(self):
        fsamp = 1000
        PulseT = np.zeros(2000)

        # Type 1 peak: high amplitude
        high_peaks = [100, 300, 500]
        for p in high_peaks:
            PulseT[p] = 10

        # Type 2 peak: low amplitude
        low_peaks = [700, 900, 1100]
        for p in low_peaks:
            PulseT[p] = 2

        sil = getsil(PulseT, fsamp)
        self.assertGreaterEqual(sil, -1)
        self.assertLessEqual(sil, 1)
        self.assertGreater(sil, 0)  # The two categories are clearly different and should have positive silhouette-like values.

    def test_getsil_random_noise(self):
        np.random.seed(42)
        PulseT = np.random.rand(2000)
        fsamp = 1000
        sil = getsil(PulseT, fsamp)
        self.assertGreaterEqual(sil, -1)
        self.assertLessEqual(sil, 1)


if __name__ == "__main__":
    unittest.main()
