from PyQt5.QtCore import QThread, pyqtSignal
import scipy.io as sio
from core.logger import logger

class SaveMatWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, filename, data, compression=True):
        super().__init__()
        self.filename = filename
        self.data = data
        self.compression = compression

    def run(self):
        try:
            sio.savemat(self.filename, self.data, do_compression=self.compression)
            self.finished.emit()
        except Exception as e:
            logger.exception(f"failed to save file {self.filename}")
            self.error.emit(str(e))
