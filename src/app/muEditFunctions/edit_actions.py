from core.utils.manual_editing.smart_button_pushed import smart_button_pushed
from core.utils.manual_editing.selection_tools import SelectionTool, process_selection
from app.muEditFunctions.mu_selection import (
    mu_checkbox_state_changed
)
import numpy as np
from ui.components import (

    ErrorDialog,

)
from app.muEditFunctions.batch_processing import remove_outliers
@smart_button_pushed
def add_spikes_button_pushed(self):
    """Add spikes by drawing a selection rectangle."""

    # Get the first checked MU
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())
            break

    if not checked_mus:
        return

    mu_text = checked_mus[0]
    parts = mu_text.split("_")

    if len(parts) < 4:
        return

    array_idx = int(parts[1]) - 1
    mu_idx = int(parts[3]) - 1

    # Store current state for undo
    # self._push_undo(array_idx, mu_idx)

    self.selection_tool = SelectionTool(
        self.spiketrain_plot,
        "add_spikes",
        lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
            "add_spikes", array_idx, mu_idx, x_min, x_max, y_min, y_max
        ),
        lambda: self._push_undo(array_idx, mu_idx),
    )

@smart_button_pushed
def delete_spikes_button_pushed(self):
    """Delete spikes by drawing a selection rectangle."""

    # Get the first checked MU
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())
            break

    if not checked_mus:
        return

    mu_text = checked_mus[0]
    parts = mu_text.split("_")

    if len(parts) < 4:
        return

    array_idx = int(parts[1]) - 1
    mu_idx = int(parts[3]) - 1

    # Store current state for undo
    # self._push_undo(array_idx, mu_idx)

    # Create selection tool
    self.selection_tool = SelectionTool(
        self.spiketrain_plot,
        "delete_spikes",
        lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
            "delete_spikes", array_idx, mu_idx, x_min, x_max, y_min, y_max
        ),
        lambda: self._push_undo(array_idx, mu_idx),
    )

@smart_button_pushed
def delete_dr_button_pushed(self):
    """Delete discharge rates by drawing a selection rectangle in the DR plot."""

    # Get the first checked MU
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())
            break

    if not checked_mus:
        return

    mu_text = checked_mus[0]
    parts = mu_text.split("_")

    if len(parts) < 4:
        return

    array_idx = int(parts[1]) - 1
    mu_idx = int(parts[3]) - 1

    # Store current state for undo
    # self._push_undo(array_idx, mu_idx)

    # Create selection tool
    self.selection_tool = SelectionTool(
        self.dr_plot,
        "delete_dr",
        lambda x_min, x_max, y_min, y_max: self.handle_selection_complete(
            "delete_dr", array_idx, mu_idx, x_min, x_max, y_min, y_max
        ),
        lambda: self._push_undo(array_idx, mu_idx),
    )

def lock_spikes_button_pushed(self):
    """Lock the current spikes to keep them during filter updates."""
    print("push lock spikes")
    if self.action_buttons["lock_spikes_button_pushed"].get_active():
        self.Backup["lock"] = 0
        self.action_buttons["lock_spikes_button_pushed"].set_active(False)
    else:
        self.Backup["lock"] = 1
        self.action_buttons["lock_spikes_button_pushed"].set_active(True)

def remove_outliers_button_pushed(self):
    """Remove outliers from the current motor unit."""
    if not self.MUedition:
        return

    # Get the first checked MU
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())

    if not checked_mus:
        ErrorDialog(text="Please select a MU first!")
        return
    removal_summary = {}
    for mu_text in checked_mus:
        parts = mu_text.split("_")
        if len(parts) < 4:
            continue

        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store state for undo
        self._push_undo(array_idx, mu_idx)

        if (array_idx, mu_idx) not in self.MUedition["edition"]["Dischargetimes"] or len(
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]) <= 1:
            continue

        # Prepare input for remove_outliers
        pulse_trains = np.zeros((1, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[1]))
        pulse_trains[0, :] = self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]
        distime_list = [self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]]

        # Call the function
        filtered_distime, removal_dict = remove_outliers(
            self, pulse_trains, distime_list, self.MUedition["signal"]["fsamp"], [mu_text]
        )

        self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = filtered_distime[0]
        mu_checkbox_state_changed(self)
        self.update_save_button()
        removal_summary.update(removal_dict)
    if removal_summary:
        summary_lines = [f"{mu}: Removed {cnt} outliers" for mu, cnt in removal_summary.items()]
        self.show_tip("Remove outlier successfully!".join(summary_lines), duration_ms=4000)
        #SuccessDialog(text="Remove outlier successfully!\n\n" + "\n".join(summary_lines))
    else:
        self.show_tip("No outliers were removed.", duration_ms=4000)
        #SuccessDialog(text="No outliers were removed.")
