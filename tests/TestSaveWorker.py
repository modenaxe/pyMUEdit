'''
Test command:
python -m unittest TestSaveWorker.py -v
'''
# test saveworker
import unittest
import numpy as np
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.utils.manual_editing.save_worker import Save_worker
import tempfile
import scipy.io as sio
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop, QTimer

class TestSaveWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # QApplication must be initialized once globally
        cls.app = QApplication([])

    def test_save_success(self):
        fd, filepath = tempfile.mkstemp(suffix=".mat")
        os.close(fd)

        data = {"a": [1, 2, 3], "b": 42}
        finished_flag = []

        def on_finished():
            finished_flag.append(True)
            loop.quit()

        worker = Save_worker(filepath, data, on_finished=on_finished)

        # Start the thread and enter the event loop
        worker.start()
        loop = QEventLoop()
        QTimer.singleShot(3000, loop.quit)  # Timeout protection
        loop.exec_()

        # Verify that the finished signal is emitted
        self.assertTrue(finished_flag, "finished signal was not emitted")

        # Verify that the file was written successfully
        loaded = sio.loadmat(filepath)
        self.assertIn("a", loaded)
        self.assertIn("b", loaded)
        self.assertEqual(loaded["b"][0, 0], 42)

        os.remove(filepath)

    def test_save_failure(self):
        filepath = "/invalid/path/file.mat"
        data = {"x": [1, 2]}
        error_msgs = []

        def on_error(msg):
            error_msgs.append(msg)
            loop.quit()

        worker = Save_worker(filepath, data, on_error=on_error)

        # Start the thread and enter the event loop
        worker.start()
        loop = QEventLoop()
        QTimer.singleShot(3000, loop.quit)
        loop.exec_()

        # Verify that the error signal is emitted
        self.assertTrue(error_msgs, "error signal was not emitted")
        self.assertTrue("No such file" in error_msgs[0] or "Permission" in error_msgs[0])


if __name__ == "__main__":
    unittest.main()
