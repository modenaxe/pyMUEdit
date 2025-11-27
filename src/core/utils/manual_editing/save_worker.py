from PyQt5.QtCore import QThread, pyqtSignal
import scipy.io as sio
from core.logger import logger

class Save_worker(QThread):
    """
    A thread for saving HDF5/Mat files that can be started directly.

    Parameters:
      filepath     The path where the file will be saved.
      data         dict, the data to write into the .mat file.
      on_finished  Callback function invoked upon successful save (optional).
      on_error     Callback function invoked upon save failure (optional), receives a string errmsg.
    """
    # Define signals
    finished = pyqtSignal()
    error    = pyqtSignal(str)

    def __init__(self, filepath, data,
                 on_finished=None,
                 on_error=None,
                 parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.data     = data

        # If callback functions are provided, connect them automatically
        if on_finished:
            self.finished.connect(on_finished)
        if on_error:
            self.error.connect(on_error)

    def run(self):
        try:
            # do_compression=True enables compression
            sio.savemat(self.filepath, self.data, do_compression=True)
        except Exception as e:
            logger.exception("save worker failed")
            self.error.emit(str(e))
        else:
            self.finished.emit()
