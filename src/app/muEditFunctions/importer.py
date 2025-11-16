
import os
import scipy.io as sio
import h5py
import numpy as np
import copy # moy
import json

from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QProgressDialog
)
from PyQt5.QtCore import Qt

from core.utils.manual_editing.h5_import import h5py_convert

# Import custom components
from core.utils.session.convert_h5 import load_from_h5
from ui.components import (
    WarningDialog,
    ErrorDialog,
)

from app.muEditFunctions.mu_selection import (
    calculate_silval,
    update_mu_checkboxes
)

def import_data(self):
    """Import data from selected file (.mat or .h5)."""
    if not self.filename or not self.pathname:
        return

    self.ish5 = False
    filepath = os.path.join(self.pathname, self.filename)
    ext = self.filename.lower().split('.')[-1]

    # Show wait cursor
    QApplication.setOverrideCursor(Qt.WaitCursor)

    try:
        # Load file based on extension
        if ext == 'mat':
            try:
                files = sio.loadmat(filepath)
            except NotImplementedError:
                from core.utils.manual_editing.h5_import import h5py_convert
                try:
                    with h5py.File(filepath, "r") as f:
                        print("h5py File load success")
                        self.ish5 = True
                        files = h5py_convert().h5py_to_dict(f)
                        print("h5py File convert complete")
                except Exception:
                    import traceback
                    traceback.print_exc()
                    return
            # Check and process files
            if not self.ish5:
                # Verify fields present
                if "signal" not in files:
                    raise KeyError("Missing 'signal' in .mat file")
                if "Pulsetrain" not in files["signal"].dtype.names:
                    raise KeyError("Missing 'Pulsetrain' in signal")
                # Keep data for processing
                import_edited_file(self, files)
            else:
                # loaded via h5py_convert
                if "signal" not in files:
                    raise KeyError("Missing 'signal' in converted .mat")
                # Decode 'signal' JSON string if needed
                if isinstance(files["signal"], str):
                    try:
                        files["signal"] = json.loads(files["signal"])
                    except:
                        print("Failed to decode 'signal' JSON string.")
                        return
                if "Pulsetrain" not in files["signal"]:
                    raise KeyError("Missing 'Pulsetrain' in signal")
                import_h5py_edited_file(self, files)
        elif ext == 'h5':
            files, raw_filepath, config = load_from_h5(filepath)
            self.ish5 = True
            # Decode 'signal' if it's a string
            if "signal" in files and isinstance(files["signal"], str):
                try:
                    files["signal"] = json.loads(files["signal"])
                except:
                    print("Failed to decode 'signal' JSON string.")
                    return
            # Decode 'edition' if exists and is string
            if "edition" in files and isinstance(files["edition"], str):
                try:
                    files["edition"] = json.loads(files["edition"])
                except:
                    print("Failed to decode 'edition' JSON string.")
                    return
            # Check presence
            if not isinstance(files["signal"], dict):
                raise ValueError("'signal' is not a dict after decoding")
            if "Pulsetrain" not in files["signal"]:
                raise KeyError("Missing 'Pulsetrain' in signal")
            # Load data
            if "edition" in files:
                # load from edited
                import_h5py_edited_file(self, files)
            else:
                # load from decomposed
                import_h5py_decomposed_file(self, files)
        else:
            raise ValueError("Unsupported file extension. Use .mat or .h5.")

        # Post-processing
        print("File import complete")
        if getattr(self, "is_overlay", False):
            QApplication.restoreOverrideCursor()
            return self.MUedition

        # Calculate array number for each channel
        self.MUedition["edition"]["arraynb"] = np.zeros(self.MUedition["signal"]["data"].shape[0], dtype=int)
        ch1 = 0
        ngrid = int(self.MUedition["signal"]["ngrid"][0, 0])
        for i in range(ngrid):
            mask = self.MUedition["signal"]["EMGmask"][0, i]
            mask_length = len(mask)
            self.MUedition["edition"]["arraynb"][ch1: ch1 + mask_length] = i
            ch1 += mask_length

        # Update reference dropdown
        self.reference_dropdown.clear()
        if "auxiliary" in self.MUedition["signal"] and self.MUedition["signal"]["auxiliary"].size > 0:
            if "auxiliaryname" in self.MUedition["signal"]:
                aux_names = self.MUedition["signal"]["auxiliaryname"][0]
                aux_accel_count = 0
                for i in range(aux_names.shape[0]):
                    raw = aux_names[i]
                    base = str(raw[0]) if isinstance(raw, np.ndarray) and raw.size else str(raw)
                    if base.strip() == "AUX  Acceleration":
                        aux_accel_count += 1
                        label = f"{base} {aux_accel_count}"
                    else:
                        label = base
                    self.reference_dropdown.addItem(label)

        # Update MU checkboxes
        self.resetPlot = True
        update_mu_checkboxes(self)
        # Set initial view
        self.graphstart = self.MUedition["edition"]["time"][0]
        if hasattr(self, "pan_slider"):
            self.center_pan_slider()
        self.graphend = self.MUedition["edition"]["time"][-1]
        self.update_plot_limits()
        self._sync_pan_slider()

        # Save current data for reset
        self.initial_data = copy.deepcopy(self.MUedition["edition"])

    except KeyError as ke:
        QApplication.restoreOverrideCursor()
        ErrorDialog(title_label="Missing Field", text=f"The file is missing required fields:\n{ke}")
        import traceback; traceback.print_exc()
    except Exception as e:
        import traceback; traceback.print_exc()
        QApplication.restoreOverrideCursor()
        ErrorDialog(title_label="Import Error", text=f"Failed to load the file:\n{str(e)}")

def import_edited_file(self, files):
    """Import data from a previously edited file."""
    if not self.MUedition:
        return

    signal_data = files["signal"][0, 0]
    for field in signal_data.dtype.names:
        self.MUedition["signal"][field] = signal_data[field]

    self.MUedition["edition"]["Pulsetrain"] = []
    # Copy Pulsetrain data
    pulsetrain_data = self.MUedition["signal"]["Pulsetrain"][0]
    # Handle as a 1D array
    for i in range(len(pulsetrain_data)):
        self.MUedition["edition"]["Pulsetrain"].append(pulsetrain_data[i])


    # Copy structured data from MATLAB file
    edition_data = files["edition"][0, 0]

    # Restore the three dictionaries: "Dischargetimes", "silval", "silvalcon"
    for field in edition_data.dtype.names:
        val = edition_data[field]

        # Check if it is a JSON string
        if field in ("Dischargetimes", "silval", "silvalcon") and isinstance(val, np.ndarray) and val.dtype.kind in {'U', 'S', 'O'}:
            # Here `val` is an array of length 1, containing a string
            str_val = str(val.item())
            try:
                raw_dict = json.loads(str_val)
                # Restore keys from "[i,j]" string format to tuple
                new_dict = {}
                for k, v in raw_dict.items():
                    idx = tuple(json.loads(k.replace("'", '"')))  # Convert "[i, j]" -> (i, j)
                    # If value is a list, convert back to np.array; if float/int, use directly
                    if isinstance(v, list):
                        new_dict[idx] = np.array(v)
                    else:
                        new_dict[idx] = v
                self.MUedition["edition"][field] = new_dict
            except Exception as e:
                print(f"Error loading field {field}: {e}")
                self.MUedition["edition"][field] = {}

        # Process pulsetrain
        elif field == "Pulsetrain" and isinstance(val, np.ndarray):
            self.MUedition["edition"][field] = [x for x in val.flatten()]

        # Process flag
        elif field == "Flag" and isinstance(val, np.ndarray):
            self.MUedition["edition"][field] = [
                [0] * arr.shape[0]
                for arr in self.MUedition["edition"]["Pulsetrain"]
            ]

        # Process time
        elif field == "time" and isinstance(val, np.ndarray):
            self.MUedition["edition"][field] = val.flatten()

        # Process arraynb
        elif field == "arraynb" and isinstance(val, np.ndarray):
            self.MUedition["edition"][field] = val.flatten()

        else:
            self.MUedition["edition"][field] = val


    signal_data = files["signal"][0, 0]
    for field in signal_data.dtype.names:
        self.MUedition["signal"][field] = signal_data[field]

    if "parameters" in files:
        parameters_data = files["parameters"][0, 0]
        for field in parameters_data.dtype.names:
            self.MUedition["parameters"][field] = parameters_data[field]

def import_decomposed_file(self, files):
    """Import data from a new decomposition file that hasn't been edited yet."""
    if not self.MUedition:
        return

    signal_data = files["signal"][0, 0]

    # Copy signal fields
    for field in signal_data.dtype.names:
        self.MUedition["signal"][field] = signal_data[field]

    # Copy parameters if available
    if "parameters" in files:
        parameters_data = files["parameters"][0, 0]
        for field in parameters_data.dtype.names:
            self.MUedition["parameters"][field] = parameters_data[field]

    # Initialize edition data structures
    self.MUedition["edition"]["Pulsetrain"] = []
    self.MUedition["edition"]["Dischargetimes"] = {}
    self.MUedition["edition"]["silval"] = {}
    self.MUedition["edition"]["silvalcon"] = {}
    self.MUedition["edition"]["Flag"] = []


    # Extract scalar values
    ngrid = int(self.MUedition["signal"]["ngrid"][0, 0])
    fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])

    # Calculate time vector
    signal_length = self.MUedition["signal"]["data"].shape[1]
    self.MUedition["edition"]["time"] = np.linspace(0, signal_length / fsamp, signal_length)

    # Copy Pulsetrain data
    pulsetrain_data = self.MUedition["signal"]["Pulsetrain"][0]

    # Handle as a 1D array
    for i in range(len(pulsetrain_data)):
        self.MUedition["edition"]["Pulsetrain"].append(pulsetrain_data[i])

    # Copy Dischargetimes
    dischargetimes_data = self.MUedition["signal"]["Dischargetimes"]
    for i in range(dischargetimes_data.shape[0]):
        for j in range(dischargetimes_data.shape[1]):
            # Get the discharge times array and check if it's not empty
            dt = dischargetimes_data[i, j]
            if dt.size > 0:
                # Flatten and store as tuple key (array_idx, mu_idx)
                self.MUedition["edition"]["Dischargetimes"][(i, j)] = dt.flatten()

    # Calculate SIL values for each motor unit
    for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
        pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

        # Give every MU array a Flag array
        self.MUedition["edition"]["Flag"].append([])

        for mu_idx in range(pulse_train.shape[0]):
            if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                if not getattr(self, "is_overlay", False):
                    calculate_silval(self, array_idx, mu_idx)

            # Give every MU a Flag tag
            self.MUedition["edition"]["Flag"][array_idx].append(0)

def import_h5py_edited_file(self, files):
    """Import data from a new decomposition file that hasn't been edited yet."""
    self.MUedition = {"edition": {}, "signal": {}, "parameters": {}}

    signal_data = files["signal"]

    # Copy signal fields
    for field in signal_data:
        self.MUedition["signal"][field] = signal_data[field]

    # Copy parameters if available
    if "parameters" in files:
        parameters_data = files["parameters"]
        for field in parameters_data:
            self.MUedition["parameters"][field] = parameters_data[field]

    # Initialize edition data structures
    self.MUedition["edition"]["Pulsetrain"] = []
    self.MUedition["edition"]["Dischargetimes"] = {}
    self.MUedition["edition"]["silval"] = {}
    self.MUedition["edition"]["silvalcon"] = {}
    self.MUedition["edition"]["Flag"] = []

    # Calculate time vector
    self.MUedition["signal"]["data"] = self.MUedition["signal"]["data"].T
    self.MUedition["edition"]["time"] = files["edition"]["time"].squeeze()

    # Copy Pulsetrain data
    pulsetrain_data = files["edition"]["Pulsetrain"]

    # Handle as a 1D array
    for i in range(len(pulsetrain_data)):
        if isinstance(pulsetrain_data[i][0][0], float):
            self.MUedition["edition"]["Pulsetrain"].append(np.array(pulsetrain_data[i]))
        else:
            self.MUedition["edition"]["Pulsetrain"].append(np.array(pulsetrain_data[i][0]).T)

    self.MUedition["signal"]["Pulsetrain"] = self.MUedition["edition"]["Pulsetrain"]

    # Copy Dischargetimes
    dischargetimes_data = files["edition"]["Dischargetimes"]
    for i in range(len(dischargetimes_data)):
        for j in range(len(dischargetimes_data[0])):
            # Get the discharge times array and check if it's not empty
            dt = dischargetimes_data[i][j]
            if len(dt) > 0:
                # Flatten and store as tuple key (array_idx, mu_idx)
                self.MUedition["edition"]["Dischargetimes"][(j, i)] = np.array(dt, dtype=int)

    # Load SIL values for each motor unit
    for array_idx in range(len(files["edition"]["silval"][0])):
        # Give every MU array a Flag array
        self.MUedition["edition"]["Flag"].append([])

        for mu_idx in range(len(files["edition"]["silval"])):
            if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:

                self.MUedition["edition"]["silval"][(array_idx, mu_idx)] = files["edition"]["silval"][mu_idx][array_idx][0]
                self.MUedition["edition"]["silvalcon"][(array_idx, mu_idx)] = np.array(files["edition"]["silvalcon"][mu_idx][array_idx]).T
            self.MUedition["edition"]["Flag"][array_idx].append(0)

    # Refactored data structures to align with downstream processing requirements.
    EMGmask_list = []
    for array_idx in range(len(self.MUedition["signal"]["EMGmask"])):
        EMGmask = self.MUedition["signal"]["EMGmask"][array_idx][0][0]
        EMGmask_list.append(EMGmask)

    self.MUedition["signal"]["EMGmask"] = np.array([EMGmask_list])

    # Refactored data structures to align with downstream processing requirements.
    auxname_list = []
    for name_list in self.MUedition["signal"]["auxiliaryname"]:
        name_str = bytes(name_list[0]).decode('ascii')
        auxname_list.append(name_str)

    self.MUedition["signal"]["auxiliaryname"] = np.array([auxname_list])
    self.MUedition["signal"]["auxiliary"] = self.MUedition["signal"]["auxiliary"].T

def import_h5py_decomposed_file(self, files):
    """Import data from a new decomposition file that hasn't been edited yet."""

    signal_data = files["signal"]

    # Copy signal fields
    for field in signal_data:
        self.MUedition["signal"][field] = signal_data[field]

    # Copy parameters if available
    if "parameters" in files:
        parameters_data = files["parameters"]
        for field in parameters_data:
            self.MUedition["parameters"][field] = parameters_data[field]

    # Initialize edition data structures
    self.MUedition["edition"]["Pulsetrain"] = []
    self.MUedition["edition"]["Dischargetimes"] = {}
    self.MUedition["edition"]["silval"] = {}
    self.MUedition["edition"]["silvalcon"] = {}
    self.MUedition["edition"]["Flag"] = []

    # Extract scalar values
    ngrid = int(self.MUedition["signal"]["ngrid"][0, 0])
    fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])

    # Calculate time vector
    self.MUedition["signal"]["data"] = self.MUedition["signal"]["data"].T
    signal_length = self.MUedition["signal"]["data"].shape[1]
    self.MUedition["edition"]["time"] = np.linspace(0, signal_length / fsamp, signal_length)

    # Copy Pulsetrain data
    pulsetrain_data = self.MUedition["signal"]["Pulsetrain"]

    # Handle as a 1D array
    for i in range(len(pulsetrain_data)):
        self.MUedition["edition"]["Pulsetrain"].append(np.array(pulsetrain_data[i][0]).T)

    # Copy Dischargetimes
    dischargetimes_data = self.MUedition["signal"]["Dischargetimes"]
    for i in range(len(dischargetimes_data)):
        for j in range(len(dischargetimes_data[0])):
            # Get the discharge times array and check if it's not empty
            dt = dischargetimes_data[i][j]
            if len(dt) > 0:
                # Flatten and store as tuple key (array_idx, mu_idx)
                self.MUedition["edition"]["Dischargetimes"][(j, i)] = np.array(dt, dtype=int)

    max_progress = sum(pt.shape[0] for pt in self.MUedition["edition"]["Pulsetrain"])
    progress = QProgressDialog("Caculating SIL values for each motor unit...", "Cancle", 0, max_progress, self)
    cancel_btn = progress.findChild(QPushButton)
    if cancel_btn:
        cancel_btn.hide()
    cur_progress = 0
    # Calculate SIL values for each motor unit
    for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
        pulse_train = self.MUedition["edition"]["Pulsetrain"][array_idx]

        # Give every MU array a Flag array
        self.MUedition["edition"]["Flag"].append([])

        for mu_idx in range(pulse_train.shape[0]):
            if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                if not getattr(self, "is_overlay", False):
                    cur_progress += 1
                    calculate_silval(self, array_idx, mu_idx)
                    progress.setValue(cur_progress)
                    progress.setLabelText(f"Calculating for Array {array_idx}: MU {mu_idx}")
                    QApplication.processEvents()

            # Give every MU a Flag tag
            self.MUedition["edition"]["Flag"][array_idx].append(0)

    # Refactored data structures to align with downstream processing requirements.
    EMGmask_list = []
    for array_idx in range(len(self.MUedition["signal"]["EMGmask"])):
        EMGmask = self.MUedition["signal"]["EMGmask"][array_idx][0][0]
        EMGmask_list.append(EMGmask)

    self.MUedition["signal"]["EMGmask"] = np.array([EMGmask_list])

    # Refactored data structures to align with downstream processing requirements.
    auxname_list = []
    for name_list in self.MUedition["signal"]["auxiliaryname"]:
        name_str = bytes(name_list[0]).decode('ascii')
        auxname_list.append(name_str)

    self.MUedition["signal"]["auxiliaryname"] = np.array([auxname_list])

    self.MUedition["signal"]["auxiliary"] = self.MUedition["signal"]["auxiliary"].T
