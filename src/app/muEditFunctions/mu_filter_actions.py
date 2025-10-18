# Import custom components
from ui.components import (
    ErrorDialog,
)
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from core.utils.manual_editing.extendfilter import extendfilter
from app.muEditFunctions.plotting import update_spike_train_plot
from app.muEditFunctions.mu_selection import (
    calculate_silval,
    update_display_mus 
)

def update_mu_filter_button_pushed(self):
    """Update the motor unit filter using the current discharge times."""
    if not self.MUedition:
        return

    # Ask whether lock spikes
    # if self.Backup["lock_changable"] == 1:
    #     dialog = MessageDialog(text="Do you want to lock splikes? ", HelpButtonTip="When updating the filter, the spikes in the non-edge part of the current display area are retained and not deleted.")
    #     result = dialog.exec_()
    #     if result == QDialog.Accepted:
    #         print("Yes: lock")
    #         print("push lock spikes")
    #         self.Backup["lock"] = 1
    #     elif dialog.user_clicked_no:
    #         print("No: no lock")
    #     elif dialog.user_closed_window:
    #         print("cancel operation")
    #         return
    #     if dialog.checkbox_selected:
    #         print("no ask again")
    #         self.Backup["lock_changable"] = 0

    # Get the first checked MU
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())
            break

    if not checked_mus:
        ErrorDialog(text="Please select a MU first!")
        return

    mu_text = checked_mus[0]
    parts = mu_text.split("_")
    if len(parts) < 4:
        ErrorDialog(text="Data loading error!")
        return


    # Set Mouse State to Wait
    QApplication.setOverrideCursor(Qt.WaitCursor)

    try:
        array_idx = int(parts[1]) - 1
        mu_idx = int(parts[3]) - 1

        # Store current state for undo
        self._push_undo(array_idx, mu_idx)

        # Get the indices for the current view
        idx = np.where(
            (self.MUedition["edition"]["time"] > self.graphstart) & (self.MUedition["edition"]["time"] < self.graphend)
        )[0]

        if len(idx) == 0:
            return

        # Get EMG data for the current array and view
        emg_data = self.MUedition["signal"]["data"][self.MUedition["edition"]["arraynb"] == array_idx, :]
        emg_mask = self.MUedition["signal"]["EMGmask"][0]
        emg_mask = emg_mask[array_idx].squeeze()
        emg_data = emg_data[(emg_mask == 0).squeeze(), :]  # Use only non-rejected channels

        #get EMG type
        emg_type = "surface"
        if(self.MUedition["signal"]["emgtype"][0,array_idx]==2):
            emg_type = "intra"

        #get fsamp
        fsamp = self.MUedition["signal"]["fsamp"][0][0]

        # Get the MUAP templates using extendfilter
        old_sil = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)

        # Apply filter update
        updated_pulse_train, updated_discharge_times, locked_spikes = extendfilter(
            emg_data,
            emg_mask,
            self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :],
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx],
            idx,
            fsamp,
            emg_type,
        )

        # Handle spike locking
        if self.Backup["lock"] == 1:
            aligned_locked_spikes = []
            for s in locked_spikes:
                search_range = updated_pulse_train[s - 10 : s + 11]
                if len(search_range) == 21:
                    peak_offset = np.argmax(search_range)
                    aligned_locked_spikes.append(s - 10 + peak_offset)

            aligned_locked_spikes = np.array(aligned_locked_spikes)
            all_spikes = np.union1d(updated_discharge_times, aligned_locked_spikes)
            all_spikes.sort()

            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = all_spikes

            # Reset the lock
            if self.Backup["lock_changable"] == 0:
                self.Backup["lock"] = 0
            print("Reset lock")
        else:
            # Update both pulse train and discharge times
            self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = updated_pulse_train
            self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = updated_discharge_times

        # Recalculate SIL values
        calculate_silval(self, array_idx, mu_idx)

        new_sil = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)
        # Update the display
        if (new_sil >= old_sil):
            update_display_mus(self, pluse_train_color="#8ACD69")
        else:
            update_display_mus(self, pluse_train_color="#698CCD")

        QApplication.restoreOverrideCursor()

        self.show_tip("Update filter successfully! Green means SIL improve. Blue means SIL decrease.", duration_ms=4000)
        #SuccessDialog(text="Update filter successfully!\nGreen means SIL improve. Blue means SIL decrease.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        QApplication.restoreOverrideCursor()
        print(e)
        ErrorDialog(text="Fail to update filter.")
    self.update_save_button()

def extend_mu_filter_button_pushed(self):
        """Extend the motor unit filter to the entire signal."""
        if not self.MUedition:
            return

        # Get the first checked MU
        checked_mus = []
        for checkbox in self.mu_checkboxes:
            if checkbox.isChecked():
                checked_mus.append(checkbox.objectName())
                break

        if not checked_mus:
            ErrorDialog(text="Please select a MU first!")
            return

        mu_text = checked_mus[0]
        parts = mu_text.split("_")

        if len(parts) < 4:
            ErrorDialog(text="Data loading error!")
            return

        # Set Mouse State to Wait
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            array_idx = int(parts[1]) - 1
            mu_idx = int(parts[3]) - 1

            # Store current state for undo
            self._push_undo(array_idx, mu_idx)

            # Get EMG data for the current array
            emg_data = self.MUedition["signal"]["data"][self.MUedition["edition"]["arraynb"] == array_idx, :]
            emg_mask = self.MUedition["signal"]["EMGmask"][0]
            emg_mask = emg_mask[array_idx].squeeze()
            emg_data = emg_data[emg_mask == 0, :]  # Use only non-rejected channels

            #get EMG type
            emg_type = "surface"
            if(self.MUedition["signal"]["emgtype"][0,array_idx]==2):
                emg_type = "intra"

            #get fsamp
            fsamp = self.MUedition["signal"]["fsamp"][0][0]

            # Get the current view indices
            current_idx = np.where(
                (self.MUedition["edition"]["time"] > self.graphstart) & (self.MUedition["edition"]["time"] < self.graphend)
            )[0]

            if len(current_idx) == 0:
                return

            # Save old SIL for later comparison
            old_sil = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)
            # Zoom out to full signal
            self.graphstart = self.MUedition["edition"]["time"][0]
            # moy
            if hasattr(self, "pan_slider"):
                self.center_pan_slider()
            self.graphend = self.MUedition["edition"]["time"][-1]
            self.update_plot_limits()
            self._sync_pan_slider()#moy

            # Process the signal in windows to extend the filter
            signal_length = self.MUedition["edition"]["time"].shape[0]
            step = current_idx.shape[0] // 2

            # First extend forward
            idx = current_idx.copy()
            for j in range(int((signal_length - idx[-1]) / step)):
                # Move idx forward
                idx = idx + step
                idx = idx[idx < signal_length]

                if len(idx) == 0:
                    break

                # Apply extendfilter
                updated_pulse_train, updated_discharge_times, spikes1 = extendfilter(
                    emg_data,
                    emg_mask,
                    self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :],
                    self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx],
                    idx,
                    fsamp,
                    emg_type,
                )

                # Update the data
                self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = updated_pulse_train
                self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = updated_discharge_times

                # Update the display
                update_spike_train_plot(self, array_idx, mu_idx, updated_pulse_train)
                QApplication.processEvents()

            # Then extend backward
            idx = current_idx.copy()
            for j in range(int(idx[0] / step)):
                # Move idx backward
                idx = idx - step
                idx = idx[idx >= 0]

                if len(idx) == 0:
                    break

                # Apply extendfilter
                updated_pulse_train, updated_discharge_times, spikes1 = extendfilter(
                    emg_data,
                    emg_mask,
                    self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :],
                    self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx],
                    idx,
                    fsamp,
                    emg_type,
                )

                # Update the data
                self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = updated_pulse_train
                self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = updated_discharge_times

                # Update the display
                update_spike_train_plot(self, array_idx, mu_idx, updated_pulse_train)
                QApplication.processEvents()

            # Recalculate SIL values
            calculate_silval(self, array_idx, mu_idx)
            new_sil = self.MUedition["edition"]["silval"].get((array_idx, mu_idx), 0)
            # Final display update

            if(new_sil >= old_sil):
                update_display_mus(self, pluse_train_color="#8ACD69")
            else:
                update_display_mus(self, pluse_train_color="#698CCD")

            QApplication.processEvents()

            QApplication.restoreOverrideCursor()

            self.show_tip("Extend filter successfully! Green means SIL improve. Blue means SIL decrease.", duration_ms=4000)
            #SuccessDialog(text="extend filter successfully!\nGreen means SIL improve. Blue means SIL decrease.")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            print(e)
            ErrorDialog(text="Fail to extend filter.")
        self.update_save_button()