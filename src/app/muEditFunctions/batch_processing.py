from PyQt5.QtWidgets import (
    QProgressDialog,
    QApplication,
)
import numpy as np
import copy # moy
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt

from core.logger import logger
from core.utils.manual_editing.batch_filter_worker import batch_filter_worker
from core.utils.manual_editing.duplicates_between_grids_worker import duplicates_between_grids_worker
from core.utils.manual_editing.duplicates_within_grids_worker import duplicates_within_grids_worker
from ui.components import (
    WarningDialog,
)

from app.muEditFunctions.mu_selection import (
    mu_checkbox_state_changed,
    update_mu_checkboxes,
    calculate_silval
)
# Batch processing
def remove_all_outliers_button_pushed(self):
    """Remove outliers from all motor units."""
    if not self.MUedition:
        return
    removal_summary = {}
    # Create a progress dialog
 

    original_dischargetimes = copy.deepcopy(self.MUedition["edition"]["Dischargetimes"])
    original_silval = copy.deepcopy(self.MUedition["edition"]["silval"])
    original_silvalcon = copy.deepcopy(self.MUedition["edition"]["silvalcon"])
    logger.debug("deep copy complete!")

    progress = QProgressDialog("Removing outliers...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    # Count total MUs
    total_mus = 0
    for i in range(len(self.MUedition["edition"]["Pulsetrain"])):
        total_mus += self.MUedition["edition"]["Pulsetrain"][i].shape[0]

    # Process each MU
    processed_mus = 0
    for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
        num_mus = self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]

        for mu_idx in range(num_mus):
            progress.setValue(int(processed_mus / total_mus * 100))
            progress.setLabelText(f"Removing outliers for Array #{array_idx+1} MU #{mu_idx+1}")
            QApplication.processEvents()

            if progress.wasCanceled():
                self.MUedition["edition"]["Dischargetimes"] = original_dischargetimes
                self.MUedition["edition"]["silval"] = original_silval
                self.MUedition["edition"]["silvalcon"] = original_silvalcon
                progress.close()
                logger.debug("Batch processing interruption!")
                return

            # Create dummy arrays for remoutliers function
            pulse_trains = np.zeros((1, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[1]))
            pulse_trains[0, :] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]

            distime_list = [self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))]

            # Apply remoutliers if there are discharge times
            if len(distime_list[0]) > 1:
                mu_name = f"Array_{array_idx+1}_MU_{mu_idx+1}"
                filtered_distime, removal_dict = remove_outliers(
                    self,
                    pulse_trains,
                    distime_list,
                    self.MUedition["signal"]["fsamp"],
                    [mu_name]
                )

                # Update discharge times
                if filtered_distime and len(filtered_distime) > 0:
                    self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = filtered_distime[0]

                # Update SIL values
                calculate_silval(self, array_idx, mu_idx)

            processed_mus += 1

        if progress.wasCanceled():
            self.MUedition["edition"]["Dischargetimes"] = original_dischargetimes
            self.MUedition["edition"]["silval"] = original_silval
            self.MUedition["edition"]["silvalcon"] = original_silvalcon
            progress.close()
            logger.debug("Batch processing interruption!")
            return

    progress.setValue(100)
    # SuccessDialog(text="All motor unit outliers have been removed successfully.")
    self.show_tip("All motor unit outliers have been removed successfully.", duration_ms=4000)

    self.dirty_depth += 1
    self.update_save_button()
    # Update the current MU display
    mu_checkbox_state_changed(self)

def remove_outliers(self, pulse_trains, discharge_times, fsamp, mu_names=None):
    """
    Remove outlier discharges: for each spike pair with high discharge rate,
    remove the spike with lower amplitude. Logic follows MATLAB implementation.
    Only a single pass is applied, no iteration.
    """
    removal_summary = {}
    for mu in range(len(discharge_times)):
        # Discharge rate between consecutive spikes
        drates = 1 / (np.diff(discharge_times[mu]) / fsamp)
        drates = np.array(drates).flatten()
        mean_dr = np.mean(drates)
        std_dr = np.std(drates, ddof=1)
        threshold = mean_dr + 3 * std_dr

        # Indices where DR exceeds threshold
        artifact_inds = np.where(drates > threshold)[0]

        del_indices = []

        for i in artifact_inds:
            t1 = discharge_times[mu][i]
            t2 = discharge_times[mu][i + 1]

            amp1 = pulse_trains[mu][t1]
            amp2 = pulse_trains[mu][t2]

            if amp1 < amp2:
                del_indices.append(i)
            else:
                del_indices.append(i + 1)

        # Remove duplicates & sort
        del_indices = sorted(set(del_indices))

        # Ensure not out of bounds
        del_indices = [idx for idx in del_indices if idx < len(discharge_times[mu])]

        # Perform deletion
        discharge_times[mu] = np.delete(discharge_times[mu], del_indices)
        # Identify MU name (fallback to MU_{index} if no name provided)
        mu_name = mu_names[mu] if mu_names and mu < len(mu_names) else f"MU_{mu}"
        removal_summary[mu_name] = len(del_indices)

    return discharge_times, removal_summary

def update_all_mu_filters_button_pushed(self):
    """Update filters for all motor units."""
    if not self.MUedition:
        return

    # Create a progress dialog

    progress = QProgressDialog("Updating MU filters...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    self._filterWorker = batch_filter_worker(
        self.MUedition,
        (
            copy.deepcopy(self.MUedition["edition"]["Pulsetrain"]),
            copy.deepcopy(self.MUedition["edition"]["Dischargetimes"]),
            copy.deepcopy(self.MUedition["edition"]["silval"]),
            copy.deepcopy(self.MUedition["edition"]["silvalcon"]),
        ),
        self
    )

    self._filterWorker.progress_changed.connect(lambda val, text: (
        progress.setValue(val), progress.setLabelText(text)
    ))
    # Update the current MU display
    self._filterWorker.finished.connect(lambda: (progress.close(), self.update_save_button(), mu_checkbox_state_changed(self)))
    self._filterWorker.error.connect(lambda msg: (progress.close(), logger.error(f"Error: {msg}")))

    progress.canceled.connect(self._filterWorker.cancel)
    self._filterWorker.start()

def remove_flagged_mu_button_pushed(self):
    """Remove motor units that have been flagged for deletion."""
    if not self.MUedition:
        return

    # Create a progress dialog

    progress = QProgressDialog("Removing flagged MUs...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    # Count total arrays
    total_arrays = len(self.MUedition["edition"]["Pulsetrain"])

    # Create clean versions of Pulsetrain and Dischargetimes
    clean_pulsetrain = []
    clean_dischargetimes = {}
    clean_silval = {}
    clean_silvalcon = {}

    # Process each array
    for array_idx in range(total_arrays):
        progress.setValue(int(array_idx / total_arrays * 100))
        progress.setLabelText(f"Processing Array #{array_idx + 1}")
        QApplication.processEvents()

        if progress.wasCanceled():
            progress.close()
            logger.debug("Batch processing interruption!")
            return

        # Get the pulse trains for this array
        array_pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

        # Get the Flag tag array for this array
        array_flag = self.MUedition["edition"]["Flag"][array_idx]

        # Create a mask for non-flagged MUs
        keep_mask = np.ones(array_pulse_train.shape[0], dtype=bool)

        # Create a flag for checking if remaining MU is empty
        array_empty_flag = True

        # Check each MU
        for mu_idx in range(array_pulse_train.shape[0]):
            # Get discharge times
            discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

            # Check if it's flagged for deletion (0 pulse train and minimal discharge times)
            if (
                    # np.all(array_pulse_train[mu_idx, :] == 0)
                    # and len(discharge_times) == 2
                    # and discharge_times[0] == 1
                    # and discharge_times[1] == self.MUedition["signal"]["fsamp"]
                    array_flag[mu_idx] == 1
            ):
                keep_mask[mu_idx] = False
            array_flag[mu_idx] = 0

        # Keep only non-flagged MUs
        if np.any(keep_mask):
            array_empty_flag = False
            clean_pulsetrain.append(array_pulse_train[keep_mask])

            # Keep corresponding discharge times and SIL values
            for mu_idx, new_idx in enumerate(np.where(keep_mask)[0]):
                if (array_idx, new_idx) in self.MUedition["edition"]["Dischargetimes"]:
                    clean_dischargetimes[array_idx, mu_idx] = self.MUedition["edition"]["Dischargetimes"][
                        array_idx, new_idx
                    ]

                if (array_idx, new_idx) in self.MUedition["edition"]["silval"]:
                    clean_silval[array_idx, mu_idx] = self.MUedition["edition"]["silval"][array_idx, new_idx]

                if (array_idx, new_idx) in self.MUedition["edition"]["silvalcon"]:
                    clean_silvalcon[array_idx, mu_idx] = self.MUedition["edition"]["silvalcon"][array_idx, new_idx]
        else:
            # Add empty array if all MUs are flagged
            clean_pulsetrain.append(np.zeros((0, array_pulse_train.shape[1])))

    progress.setValue(100)

    if array_empty_flag:
        WarningDialog(text="You Are Trying to Remove All MUs!\nPlease Check Your Flagged MU.")
        return

    # Update the data
    self.MUedition["edition"]["Pulsetrain"] = clean_pulsetrain
    self.MUedition["edition"]["Dischargetimes"] = clean_dischargetimes
    self.MUedition["edition"]["silval"] = clean_silval
    self.MUedition["edition"]["silvalcon"] = clean_silvalcon

    self.update_save_button()
    # Update the MU checkboxes
    update_mu_checkboxes(self)

def remove_duplicates_within_grids_button_pushed(self):
    """Remove duplicate motor units within each grid."""
    # import time # debug if this button real work moy
    # t0 = time.time()
    # print("[DEBUG] Start: remove_duplicates_within_grids")
    if not self.MUedition:
        return

    progress = QProgressDialog("Removing duplicates within grids...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    self._duplicatesInGridsWorker = duplicates_within_grids_worker(
        self.MUedition,
        (
            copy.deepcopy(self.MUedition["edition"]["Pulsetrain"]),
            copy.deepcopy(self.MUedition["edition"]["Dischargetimes"]),
            copy.deepcopy(self.MUedition["edition"]["silval"]),
            copy.deepcopy(self.MUedition["edition"]["silvalcon"]),
        ),
        self
    )

    self._duplicatesInGridsWorker.progress_changed.connect(lambda val, text: (
        progress.setValue(val), progress.setLabelText(text)
    ))
    # Update the current MU display
    self._duplicatesInGridsWorker.finished.connect(lambda: (progress.close(), self.update_save_button(), mu_checkbox_state_changed(self)))
    self._duplicatesInGridsWorker.error.connect(lambda msg: (progress.close(), logger.error(f"Duplicate detection worker error: {msg}")))

    progress.canceled.connect(self._duplicatesInGridsWorker.cancel)
    self._duplicatesInGridsWorker.start()

    # print(f"[DEBUG] Done: remove_duplicates_within_grids  (t={time.time()-t0:.2f}s)") # debug if this button real work moy

def remove_duplicates_between_grids_button_pushed(self):
    """Remove duplicate motor units between grids."""

    # import time # debug if this button real work moy
    # t0 = time.time()
    # print("[DEBUG] Start: remove_duplicates_within_grids")

    if not self.MUedition:
        return


    progress = QProgressDialog("Removing duplicates_between_grids...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    self._duplicatesWithGridsWorker = duplicates_between_grids_worker(
        self.MUedition,
        (
            copy.deepcopy(self.MUedition["edition"]["Pulsetrain"]),
            copy.deepcopy(self.MUedition["edition"]["Dischargetimes"]),
            copy.deepcopy(self.MUedition["edition"]["silval"]),
            copy.deepcopy(self.MUedition["edition"]["silvalcon"]),
        ),
        self
    )

    self._duplicatesWithGridsWorker.progress_changed.connect(lambda val, text: (
        progress.setValue(val), progress.setLabelText(text)
    ))

    # Update the current MU display
    self._duplicatesWithGridsWorker.finished.connect(lambda: (progress.close(), self.update_save_button(), mu_checkbox_state_changed(self)))
    self._duplicatesWithGridsWorker.error.connect(lambda msg: (progress.close(), logger.error(f"Duplicate-between-grids worker error: {msg}")))

    progress.canceled.connect(self._duplicatesWithGridsWorker.cancel)
    self._duplicatesWithGridsWorker.start()
    # print(f"[DEBUG] Done: remove_duplicates_within_grids  (t={time.time()-t0:.2f}s)") # debug if this button real work moy
