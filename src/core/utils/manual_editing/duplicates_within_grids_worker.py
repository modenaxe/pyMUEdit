from PyQt5.QtCore import QThread, pyqtSignal, QObject
from core.utils.decomposition.remove_duplicates import remove_duplicates
from core.logger import logger
import numpy as np

class duplicates_within_grids_worker(QThread):
    progress_changed = pyqtSignal(int, str) 
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, muedition, original_data, parent_instance):
        super().__init__()
        self.MUedition = muedition
        self.original_data = original_data
        self.parent_instance = parent_instance
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        print("Click cancel")

    def run(self):
        try:
            # Extract the sampling frequency as a scalar
            if self.MUedition["signal"]["fsamp"].ndim > 1:
                fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])
            else:
                fsamp = float(self.MUedition["signal"]["fsamp"][0])

            # Count total arrays
            total_arrays = len(self.MUedition["edition"]["Pulsetrain"])

            # Process each array
            for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):                
                if self._cancelled:
                    self.MUedition["edition"]["Pulsetrain"] = self.original_data[0]
                    self.MUedition["edition"]["Dischargetimes"] = self.original_data[1]
                    self.MUedition["edition"]["silval"] = self.original_data[2]
                    self.MUedition["edition"]["silvalcon"] = self.original_data[3]
                    print("Batch processing interruption!")
                    return
                percent = int(array_idx / total_arrays * 100)
                self.progress_changed.emit(
                    percent,
                    f"Processing Array #{array_idx + 1}"
                )
                self.progress_changed.emit(
                    percent,
                    f"Processing Array #{array_idx + 1}: preparing"
                )
                # Skip if there are no MUs
                if self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0] == 0:
                    continue

                # Create arrays for remduplicates
                pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]
                
                discharge_times = []
                for mu_idx in range(pulse_train.shape[0]):
                    if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                        discharge_times.append(self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx])
                    else:
                        discharge_times.append(np.array([]))

                self.progress_changed.emit(
                    percent,
                    f"Processing Array #{array_idx + 1}: calculate unique MUs"
                )
                # Remove duplicates
                unique_discharge_times, unique_pulse_train, _ = remove_duplicates(
                    pulse_train,
                    discharge_times,
                    discharge_times,
                    np.zeros([np.shape(pulse_train)[0], np.shape(pulse_train)[1]]),  # Placeholder for mu_filters (not used)
                    round(fsamp / 40),
                    0.00025,
                    0.3,  # Duplicate threshold
                    fsamp,
                )

                self.progress_changed.emit(
                    percent,
                    f"Processing Array #{array_idx + 1}: replace with unique MUs"
                )
                # Replace with unique MUs
                if isinstance(unique_pulse_train, list):
                    if len(unique_pulse_train) == 0:
                        unique_pulse_train = unique_pulse_train
                    else:
                        unique_pulse_train = np.stack(unique_pulse_train)
                self.MUedition["edition"]["Pulsetrain"][array_idx] = unique_pulse_train

                self.progress_changed.emit(
                    percent,
                    f"Processing Array #{array_idx + 1}: calculate new SIL"
                )
                # Update discharge times and SIL values
                for mu_idx in range(unique_pulse_train.shape[0]):  # type:ignore
                    self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = unique_discharge_times[mu_idx]
                    self.parent_instance.calculate_silval(array_idx, mu_idx)

            self.progress_changed.emit(100, "Done")
            self.finished.emit()

        except Exception as e:
            logger.exception("Error while removing duplicates within arrays")
            self.error.emit(str(e))
