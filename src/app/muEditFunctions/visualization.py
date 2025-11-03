from ui.components import (
    ErrorDialog,
    PlotDialog,
    CleanTheme
)
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# Visualization methods
def plot_mu_spiketrains_button_pushed(self):
    """Plot all motor unit spike trains in a new window."""
    if not self.MUedition:
        return

    # Create a new window for the plot
    dialog = PlotDialog("")

    # Create a figure with subplots for each array
    # Some arrays might be empty
    mu_array_length = len(self.MUedition["edition"]["Pulsetrain"])
    for mu_array in self.MUedition["edition"]["Pulsetrain"]:
        if mu_array.shape[0] == 0:
            mu_array_length -= 1
    fig, axes = plt.subplots(1, mu_array_length,
                                figsize=(15, 8),
                                constrained_layout=True)

    if len(self.MUedition["edition"]["Pulsetrain"]) == 1:
        axes = [axes]

    # Set figure background color
    fig.patch.set_facecolor("#ffffff")


    # Plot each array
    for array_idx, ax in enumerate(axes):
        # Set axes properties
        ax.set_facecolor("#ffffff")
        ax.tick_params(colors=CleanTheme.TEXT_PRIMARY)
        ax.spines["bottom"].set_color(CleanTheme.TEXT_PRIMARY)
        ax.spines["top"].set_color(CleanTheme.TEXT_PRIMARY)
        ax.spines["left"].set_color(CleanTheme.TEXT_PRIMARY)
        ax.spines["right"].set_color(CleanTheme.TEXT_PRIMARY)

        # Plot target reference
        if "target" in self.MUedition["signal"] and self.MUedition["signal"]["target"].size > 0:
            # Get target data and ensure it's a 1D array
            target_data = self.MUedition["signal"]["target"]
            if target_data.ndim > 1:
                target_data = target_data[0]  # Get the first row if it's a 2D array

            # Normalize target to 0-1 range
            target_max = np.max(target_data)
            if target_max > 0:
                target_normalized = target_data / target_max
                ax.plot(
                    self.MUedition["edition"]["time"],
                    target_normalized * self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0],
                    "--",
                    linewidth=1,
                    color="#D95535",
                    zorder=10 # change it to the top layer moy
                )

        arr_sorted_index = list(range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]))

        def quicksort(arr, low, high, discharge_times):
            if low >= high:
                return

            pivot = arr[high]
            i = low
            for j in range(low, high):
                if min(discharge_times[array_idx, arr[j]]) < min(discharge_times[array_idx, pivot]):
                    arr[j], arr[i] = arr[i], arr[j]
                    i += 1

            arr[i], arr[high] = arr[high], arr[i]

            quicksort(arr, low, i-1, self.MUedition["edition"]["Dischargetimes"])
            quicksort(arr, i+1, high, self.MUedition["edition"]["Dischargetimes"])

        quicksort(arr_sorted_index, 0, len(arr_sorted_index)-1, self.MUedition["edition"]["Dischargetimes"])

        if not self.spike_train_plot_sort_mode:
            arr_sorted_index = arr_sorted_index[::-1]
        # for idx in arr_sorted_index:
        #     dis = min(self.MUedition["edition"]["Dischargetimes"][array_idx, idx])
        #     print(f"{array_idx} + {idx}: {dis}")

        # Create firing times array
        firings = np.full(
            (self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0], len(self.MUedition["edition"]["time"])),
            np.nan,
        )


        # Fill with MU indices at discharge times
        for mu_idx in range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]):
            if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                firings[mu_idx, self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]] = mu_idx + 1

        # Plot as raster plot
        # MU has different color with jet scheme
        cmap = cm.get_cmap("jet", len(arr_sorted_index))

        for plot_idx, mu_idx in enumerate(arr_sorted_index):
            # Looks like time_indices is the same as ["Dischargetimes"][array_idx, mu_idx], don't know why use this
            time_indices = np.where(~np.isnan(firings[mu_idx]))[0]
            ax.plot(
                self.MUedition["edition"]["time"][time_indices],
                np.ones_like(time_indices) * (plot_idx + 1),
                "|",
                markersize=10,
                color=cmap(plot_idx)
            )

        # Set labels
        ax.set_title(
            f'Array #{array_idx+1} with {self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]} MUs',
            color=CleanTheme.TEXT_PRIMARY,
            fontsize=12
        )
        ax.set_xlabel("Time (s)", color=CleanTheme.TEXT_PRIMARY)
        if array_idx == 0:
            ax.set_ylabel("MU #", color=CleanTheme.TEXT_PRIMARY)

        # Set y-axis limits with margin
        ax.set_ylim(0, self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0] + 1)

    # Add a overall title
    dialog.set_title(f'Raster plots for {mu_array_length} arrays')

    # Add the figure to the dialog
    canvas = FigureCanvas(fig)

    dialog.set_canvas(canvas)

    dialog.show()
    if self.RasterPlotDialog:
        self.RasterPlotDialog.deleteLater()
    self.RasterPlotDialog = dialog

def plot_mu_firingrates_button_pushed(self):
    """Plot all motor unit firing rates in a new window."""
    if not self.MUedition:
        return

    dialog = PlotDialog("")

    # Create a figure with subplots for each array
    # Some arrays might be empty
    mu_array_length = len(self.MUedition["edition"]["Pulsetrain"])
    for mu_array in self.MUedition["edition"]["Pulsetrain"]:
        if mu_array.shape[0] == 0:
            mu_array_length -= 1
    if mu_array_length == 0:
        ErrorDialog("You don't have any MU, Please Check Your Data!")
    fig, axes = plt.subplots(1, mu_array_length,
                                figsize=(15, 8),
                                constrained_layout=True)
    if len(self.MUedition["edition"]["Pulsetrain"]) == 1:
        axes = [axes]

    # Set figure background color
    fig.patch.set_facecolor("#ffffff")

    # Get the currently selected MUs
    checked_mus = []
    for checkbox in self.mu_checkboxes:
        if checkbox.isChecked():
            checked_mus.append(checkbox.objectName())

    # Extract the sampling frequency as a scalar
    if self.MUedition["signal"]["fsamp"].ndim > 1:
        fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])
    else:
        fsamp = float(self.MUedition["signal"]["fsamp"][0])

    # Create window for smoothing
    window_size = int(fsamp)
    hann_window = np.hanning(window_size)

    # Plot each array
    for array_idx, ax in enumerate(axes):
        # Set axes properties
        ax.set_facecolor("#ffffff")
        ax.tick_params(colors=CleanTheme.TEXT_PRIMARY)
        ax.spines["bottom"].set_color(CleanTheme.TEXT_PRIMARY)
        ax.spines["top"].set_color(CleanTheme.TEXT_PRIMARY)
        ax.spines["left"].set_color(CleanTheme.TEXT_PRIMARY)
        ax.spines["right"].set_color(CleanTheme.TEXT_PRIMARY)

        # MU has different color with jet scheme
        cmap = cm.get_cmap("jet", self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0])
        # Process each MU in this array
        for mu_idx in range(self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]):
            # Create binary spike train
            firing = np.zeros(len(self.MUedition["edition"]["time"]))

            if (array_idx, mu_idx) in self.MUedition["edition"]["Dischargetimes"]:
                discharge_times = self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]
                if len(discharge_times) > 0:
                    firing[discharge_times] = 1

            # Smooth using convolution
            smoothed_dr = np.convolve(firing, hann_window, mode="same")

            # Determine line style - highlight current MUs
            mu_text = f"Array_{array_idx+1}_MU_{mu_idx+1}"
            if mu_text in checked_mus:
                ax.plot(self.MUedition["edition"]["time"], smoothed_dr, color=cmap(mu_idx), linewidth=3)
            else:
                ax.plot(self.MUedition["edition"]["time"], smoothed_dr, color=cmap(mu_idx), linewidth=1, alpha=0.7)

        # Set labels
        ax.set_title(
            f'Array #{array_idx+1} with {self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]} MUs',
            color=CleanTheme.TEXT_PRIMARY,
            fontsize=12,
        )
        ax.set_xlabel("Time (s)", color=CleanTheme.TEXT_PRIMARY)
        if array_idx == 0:
            ax.set_ylabel("Smoothed discharge rates", color=CleanTheme.TEXT_PRIMARY)

    # Add the figure to the dialog
    canvas = FigureCanvas(fig)
    dialog.set_canvas(canvas)

    # Add a overall title
    dialog.set_title(f'Smoothed discharge rates for {mu_array_length} arrays')

    dialog.show()
    if self.DischagePlotDialog:
        self.DischagePlotDialog.deleteLater()
    self.DischagePlotDialog = dialog
