from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QProgressDialog,
)

from core.database.database import insert_log, upsert_file_versions
from core.utils.session.convert_h5 import save_as_h5
from ui.components import (
    SuccessDialog,
    ErrorDialog,
)

from PyQt5.QtCore import Qt, pyqtSignal
import os
import numpy as np
import copy # moy
import json

from core.utils.manual_editing.save_worker import Save_worker


def saveas_button_pushed(self):
    """Save the edited motor units to a selected file."""
    """Open file dialog to select file for editing and automatically save it."""
    if not self.MUedition:
        return
    file_dialog = QFileDialog()
    file_path, _ = file_dialog.getSaveFileName(self, "Save as", "", "MAT Files (*.mat);;All Files (*.*)")

    if file_path:
        self.pathname = os.path.dirname(file_path) + "/"
        self.filename = os.path.basename(file_path)
        self.file_path_field.setText(self.filename)
        self.select_file_title_btn.setText(self.filename)
        save_file(self, file_path)
        SuccessDialog(title_label="Save Complete", text=f"Data saved to:\n{file_path}")

def save_button_pushed(self):
    """Save the edited motor units to a file."""
    # Determine the save filename
    if self.filename is None:
        return

    if os.path.splitext(self.filename)[0].endswith("_pyedited"):
        savename = os.path.join(self.pathname or "", self.filename)
    else:
        savename = os.path.join(self.pathname or "", os.path.splitext(self.filename)[0] + "_pyedited.mat")
        self.filename = os.path.splitext(self.filename)[0] + "_pyedited.mat"

    self.file_path_field.setText(self.filename)
    self.select_file_title_btn.setText(self.filename)

    save_file(self, savename)

def save_file(self, filepath):
    print(filepath)
    if not self.MUedition:
        return

    # Remove flagged MUs before saving

    progress = QProgressDialog("Checking flagged units...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    # Count total arrays
    total_arrays = len(self.MUedition["edition"]["Pulsetrain"])

    # Clean the data structures
    for array_idx in range(total_arrays):
        progress.setValue(int(array_idx / total_arrays * 100))
        progress.setLabelText(f"Checking flagged units for Array #{array_idx+1}")
        QApplication.processEvents()

        if progress.wasCanceled():
            break

        # Get the pulse trains for this array
        array_pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

        # Check each MU from the end to avoid indexing issues when removing
        for mu_idx in range(array_pulse_train.shape[0] - 1, -1, -1):
            # Get discharge times
            discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

            # Check if it's flagged for deletion (0 pulse train and minimal discharge times)
            if (
                np.all(array_pulse_train[mu_idx, :] == 0)
                and len(discharge_times) == 2
                and discharge_times[0] == 1
                and discharge_times[1] == self.MUedition["signal"]["fsamp"]
            ):

                # Remove this MU
                self.MUedition["edition"]["Pulsetrain"][array_idx] = np.delete(
                    self.MUedition["edition"]["Pulsetrain"][array_idx], mu_idx, axis=0
                )

                # Remove from discharge times and SIL values
                if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                    del self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]

                if (array_idx, mu_idx) in self.MUedition["edition"]["silval"]:
                    del self.MUedition["edition"]["silval"][array_idx, mu_idx]

                if (array_idx, mu_idx) in self.MUedition["edition"]["silvalcon"]:
                    del self.MUedition["edition"]["silvalcon"][array_idx, mu_idx]

                # Shift higher motor units down
                for shift_mu in range(mu_idx + 1, array_pulse_train.shape[0]):
                    if (array_idx, shift_mu) in self.MUedition["edition"]["Dischargetimes"]:
                        self.MUedition["edition"]["Dischargetimes"][array_idx, shift_mu - 1] = self.MUedition[
                            "edition"
                        ]["Dischargetimes"][array_idx, shift_mu]
                        del self.MUedition["edition"]["Dischargetimes"][array_idx, shift_mu]

                    if (array_idx, shift_mu) in self.MUedition["edition"]["silval"]:
                        self.MUedition["edition"]["silval"][array_idx, shift_mu - 1] = self.MUedition["edition"][
                            "silval"
                        ][array_idx, shift_mu]
                        del self.MUedition["edition"]["silval"][array_idx, shift_mu]

                    if (array_idx, shift_mu) in self.MUedition["edition"]["silvalcon"]:
                        self.MUedition["edition"]["silvalcon"][array_idx, shift_mu - 1] = self.MUedition["edition"][
                            "silvalcon"
                        ][array_idx, shift_mu]
                        del self.MUedition["edition"]["silvalcon"][array_idx, shift_mu]
    progress.setValue(50)
    import time

    # Prepare data for saving
    signal = self.MUedition["signal"]
    parameters = copy.deepcopy(self.MUedition.get("parameters", {}))
    edition = copy.deepcopy(self.MUedition["edition"])


    for array_idx, pt in enumerate(edition["Pulsetrain"]):
        n_mu = pt.shape[0]
        flag_arr = edition["Flag"][array_idx]
        for i in range(n_mu):
            flag_arr[i] = 0


    # Convert Pulsetrain to MATLAB-compatible 1xN cell array
    pulsetrain_list = self.MUedition["edition"]["Pulsetrain"]
    pulsetrain_matlab_cell = np.empty((1, len(pulsetrain_list)), dtype=object)
    for i, pt in enumerate(pulsetrain_list):
        pulsetrain_matlab_cell[0, i] = pt
    edition["Pulsetrain"] = pulsetrain_matlab_cell  # overwrite with proper format

    # flag_list = self.MUedition["edition"]["Flag"]
    # flag_matlab_cell = np.empty((1, len(flag_list)), dtype=object)
    # for i, pt in enumerate(flag_list):
    #     flag_matlab_cell[0, i] = pt
    # edition["Flag"] = flag_matlab_cell  # overwrite with proper format

    # Store as string，Fix .mat can not store dict
    for field in ("Dischargetimes", "silval", "silvalcon"):
        if field in edition and isinstance(edition[field], dict):
            # tuple key to str
            safe_dict = {}
            for k, v in edition[field].items():
                # key: (i,j) -> "[i,j]"
                k_str = str(list(k))
                # value: ndarray/list/float
                if isinstance(v, np.ndarray):
                    v_ = v.tolist()
                else:
                    v_ = v
                safe_dict[k_str] = v_
            edition[field] = json.dumps(safe_dict)

    signal["Pulsetrain"] = edition["Pulsetrain"]
    del edition["Pulsetrain"]

    progress.setValue(100)
    # Save the data

    data = {
        "signal":     signal,
        "parameters": parameters,
        "edition":    edition
    }
    self.update_save_button(on_save=1)
    self.select_file_title_btn.setEnabled(False)
    self._save_thread = Save_worker(
        filepath, data,
        on_finished=lambda: (
            self.update_save_button(on_save=2),
            self.show_tip(f"Save Complete! Data saved to: {filepath}", duration_ms=8000),
            self.select_file_title_btn.setEnabled(True)
        ),
        on_error=lambda errmsg: ErrorDialog(
            title_label="Save File Error",
            text=errmsg
        )
    )

    signal_dict = {
        "signal": signal,
        "parameters": parameters,
        "edition": edition
    }

    log = self.get_action_logs()
    print(log)
    # h5_readin_savename = os.path.join(path, f"{base_name}_readin.h5")
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    h5_save_filename = os.path.join(self.pathname, f"{base_name}_edited.h5")
    save_as_h5(signal_dict, h5_save_filename, raw_filepath=filepath, config=log)

    versionid = upsert_file_versions(h5_save_filename, self.raw_fileid, "decomposed")

    insert_log(versionid, log, None)

    self._save_thread.start()

    self.dirty_depth = 0 #shr

    # Set current data as clear data
    self.initial_data = copy.deepcopy(self.MUedition["edition"])

    # Show a confirmation message
    #QMessageBox.information(self, "Save Complete", f"Data saved to {savename}", QMessageBox.Ok)
