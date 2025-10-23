from PyQt5.QtCore import QThread, pyqtSignal, QObject
from core.utils.decomposition.remove_duplicates_between_arrays import remove_duplicates_between_arrays
import numpy as np
from core.logger import logger

class duplicates_between_grids_worker(QThread):
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

            # Count total MUs
            mu_count = 0
            for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
                mu_count += self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]
            
            # Create arrays for remduplicatesbgrids
            all_pulse_trains = np.zeros((mu_count, self.MUedition["edition"]["time"].shape[0]))
            all_discharge_times = []
            muscle = np.zeros(mu_count, dtype=int)

            # Collect all MUs
            mu_idx_global = 0
            for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
                for mu_idx in range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]):
                    all_pulse_trains[mu_idx_global] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx]

                    if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                        all_discharge_times.append(self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx])
                    else:
                        all_discharge_times.append(np.array([]))

                    muscle[mu_idx_global] = array_idx
                    mu_idx_global += 1

            self.progress_changed.emit(
                0,
                f"Canculating unique MUs...."
            )
            
            if self._cancelled:
                print("Batch processing interruption!")
                return
            # Remove duplicates between arrays
            unique_discharge_times, unique_pulse_train, unique_muscle = remove_duplicates_between_arrays(
                all_pulse_trains, all_discharge_times, muscle, round(fsamp / 40), 0.00025, 0.3, fsamp  # Duplicate threshold
            )
            if self._cancelled:
                print("Batch processing interruption!")
                return

            self.progress_changed.emit(
                50,
                f"Canculating unique MUs done"
            )

            # Recreate data structures
            new_pulsetrain = []
            new_dischargetimes = {}

            # Initialize arrays for each grid
            for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
                percent = int(array_idx / total_arrays * 50 + 50)
                self.progress_changed.emit(
                    percent,
                    f"Processing Array #{array_idx + 1}: Set new data and calculate SIL"
                )
                array_indices = np.where(unique_muscle == array_idx)[0]

                if len(array_indices) > 0:
                    # Get pulse trains for this array
                    array_pulse_train = unique_pulse_train[array_indices]
                    new_pulsetrain.append(array_pulse_train)

                    # Get discharge times for this array
                    for mu_idx, global_idx in enumerate(array_indices):
                        if global_idx < len(unique_discharge_times):
                            new_dischargetimes[array_idx, mu_idx] = unique_discharge_times[global_idx]

                        # Calculate SIL values
                        self.parent_instance.calculate_silval(array_idx, mu_idx)
                else:
                    # Add empty array
                    new_pulsetrain.append(
                        np.zeros(
                            (
                                0,
                                (
                                    unique_pulse_train.shape[1]
                                    if unique_pulse_train.shape[0] > 0
                                    else self.MUedition["edition"]["time"].shape[0]
                                ),
                            )
                        )
                    )
                if self._cancelled:
                    self.MUedition["edition"]["Pulsetrain"] = self.original_data[0]
                    self.MUedition["edition"]["Dischargetimes"] = self.original_data[1]
                    self.MUedition["edition"]["silval"] = self.original_data[2]
                    self.MUedition["edition"]["silvalcon"] = self.original_data[3]
                    print("Batch processing interruption!")
                    return

            # Update the data
            self.MUedition["edition"]["Pulsetrain"] = new_pulsetrain
            self.MUedition["edition"]["Dischargetimes"] = new_dischargetimes

            self.progress_changed.emit(100, "Done")
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
