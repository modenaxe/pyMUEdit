import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QSpinBox,
)
from matplotlib.widgets import RectangleSelector
from matplotlib.backend_bases import MouseButton
import scipy.io as sio
from lib.segmenttargets import segmenttargets


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#262626")
        self.axes.set_facecolor("#262626")
        self.axes.xaxis.label.set_color("#f0f0f0")
        self.axes.yaxis.label.set_color("#f0f0f0")
        self.axes.tick_params(colors="#f0f0f0", which="both")
        super(MplCanvas, self).__init__(self.fig)


class SegmentSession(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file = None
        self.coordinates = []
        self.data = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Segment Session")
        self.setGeometry(100, 100, 600, 331)
        self.setStyleSheet("background-color: #262626;")

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Top control panel
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # Reference dropdown
        reference_label = QLabel("Reference")
        reference_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins';")
        self.reference_dropdown = QComboBox()
        self.reference_dropdown.addItem("No ref")
        self.reference_dropdown.currentIndexChanged.connect(self.reference_dropdown_value_changed)
        self.reference_dropdown.setStyleSheet("color: #f0f0f0; background-color: #262626; font-family: 'Poppins';")

        # Threshold field
        threshold_label = QLabel("Threshold")
        threshold_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins';")
        self.threshold_field = QSpinBox()
        self.threshold_field.setStyleSheet("color: #f0f0f0; background-color: #262626; font-family: 'Poppins';")
        self.threshold_field.valueChanged.connect(self.threshold_field_value_changed)
        self.threshold_field.setEnabled(False)

        # Windows field
        windows_label = QLabel("Windows")
        windows_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins';")
        self.windows_field = QSpinBox()
        self.windows_field.setStyleSheet("color: #f0f0f0; background-color: #262626; font-family: 'Poppins';")
        self.windows_field.valueChanged.connect(self.windows_field_value_changed)

        # Buttons
        self.concatenate_button = QPushButton("Concatenate")
        self.concatenate_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-weight: bold;"
        )
        self.concatenate_button.clicked.connect(self.concatenate_button_pushed)

        self.split_button = QPushButton("Split")
        self.split_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-weight: bold;"
        )
        self.split_button.clicked.connect(self.split_button_pushed)

        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-weight: bold;"
        )
        self.ok_button.clicked.connect(self.ok_button_pushed)

        # Pathname field (hidden)
        self.pathname = QLineEdit()
        self.pathname.setStyleSheet("color: #f0f0f0; background-color: #262626; font-family: 'Poppins';")
        self.pathname.setVisible(False)

        # Add controls to top layout
        top_layout.addWidget(reference_label)
        top_layout.addWidget(self.reference_dropdown)
        top_layout.addWidget(threshold_label)
        top_layout.addWidget(self.threshold_field)
        top_layout.addWidget(windows_label)
        top_layout.addWidget(self.windows_field)
        top_layout.addWidget(self.concatenate_button)
        top_layout.addWidget(self.split_button)
        top_layout.addWidget(self.ok_button)
        top_layout.addStretch()

        # Canvas for plotting
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.axes.set_xlabel("Time (s)")
        self.canvas.axes.set_ylabel("Reference")

        # Add widgets to main layout
        main_layout.addWidget(top_panel)
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(self.pathname)

        self.rect_selector = None

    def reference_dropdown_opening(self):
        if self.pathname.text():
            try:
                self.file = sio.loadmat(self.pathname.text())
                self.reference_dropdown.clear()
                self.reference_dropdown.addItem("EMG amplitude")

                # Extract the signal data from the structured array
                if "signal" in self.file:
                    signal_struct = self.file["signal"]

                    if "auxiliaryname" in signal_struct.dtype.names:
                        auxnames = signal_struct["auxiliaryname"][0, 0]

                        name_list = []

                        if isinstance(auxnames, np.ndarray):
                            for name_obj in auxnames.flatten():
                                # For NumPy arrays with a single value
                                if isinstance(name_obj, np.ndarray) and name_obj.size == 1:
                                    name_str = str(name_obj.item())
                                # For regular strings or other objects
                                else:
                                    name_str = str(name_obj)
                                name_list.append(name_str.strip())

                        for name in name_list:
                            self.reference_dropdown.addItem(name)
            except Exception as e:
                print(f"Error loading file: {e}")
                import traceback

                traceback.print_exc()

    def reference_dropdown_value_changed(self):
        if not self.pathname.text() or not hasattr(self, "file") or self.file is None:
            return

        self.canvas.axes.clear()

        try:
            # Extract the signal structure
            signal = self.file["signal"][0, 0]

            if "EMG amplitude" in self.reference_dropdown.currentText():
                # Calculate EMG amplitude
                print("Calculating EMG amplitude")

                # Safely extract data
                data = signal["data"]
                if isinstance(data, np.ndarray) and data.ndim > 0:
                    if data.dtype == np.dtype("O") and data.size > 0:
                        data = data[0, 0]

                fsamp = float(signal["fsamp"][0, 0]) if signal["fsamp"].ndim > 1 else float(signal["fsamp"])

                # Create convolution window
                window_size = int(fsamp)
                window = np.ones(window_size) / window_size

                # Process channels
                channels = data.shape[0]
                tmp = np.zeros((channels, data.shape[1]))

                for i in range(channels):
                    abs_emg = np.abs(data[i, :])
                    tmp[i, :] = np.convolve(abs_emg, window, mode="same")

                # Calculate mean across channels for plotting
                emg_mean = np.mean(tmp, axis=0)

                # Downsample for better visualization performance
                downsample_factor = max(1, len(emg_mean) // 5000)
                x = np.arange(0, len(emg_mean), downsample_factor)
                y_mean = emg_mean[::downsample_factor]

                # Plot only a few representative channels
                for i in range(min(8, channels)):
                    y_channel = tmp[i, ::downsample_factor]
                    self.canvas.axes.plot(x, y_channel, color="gray", linewidth=0.2, alpha=0.3)

                # Plot mean with higher visibility
                self.canvas.axes.plot(x, y_mean, color="orangered", linewidth=1.5)

                y_min = float(np.min(emg_mean) * 0.9)
                y_max = float(np.max(emg_mean) * 1.1)
                self.canvas.axes.set_ylim(y_min, y_max)

                self.threshold_field.setEnabled(False)
            else:
                # Handle auxiliary signals
                selected_name = self.reference_dropdown.currentText().strip()

                # Get auxiliary data
                aux_data = signal["auxiliary"]
                if isinstance(aux_data, np.ndarray) and aux_data.ndim > 0:
                    if aux_data.dtype == np.dtype("O") and aux_data.size > 0:
                        aux_data = aux_data[0, 0]

                # Get auxiliary names
                aux_names = signal["auxiliaryname"]
                if isinstance(aux_names, np.ndarray) and aux_names.ndim > 0:
                    if aux_names.dtype == np.dtype("O") and aux_names.size > 0:
                        aux_names = aux_names[0, 0]

                # Find the signal index
                idx = None
                for i, name in enumerate(aux_names):
                    name_str = str(name).strip()
                    if selected_name in name_str:
                        idx = i
                        break

                if idx is not None:
                    # Extract the data
                    signal_data = aux_data[idx, :]

                    downsample_factor = max(1, len(signal_data) // 1000)
                    x = np.arange(0, len(signal_data), downsample_factor)
                    y = signal_data[::downsample_factor]

                    # Plot downsampled data as a line
                    self.canvas.axes.plot(x, y, color="orangered", linewidth=1.0)

                    # Set appropriate y-limits with padding
                    data_range = np.max(signal_data) - np.min(signal_data)
                    y_min = float(np.min(signal_data) - 0.05 * data_range)
                    y_max = float(np.max(signal_data) + 0.05 * data_range)
                    self.canvas.axes.set_ylim(y_min, y_max)

                    self.threshold_field.setEnabled(True)
                else:
                    print(f"Could not find matching auxiliary signal for: {selected_name}")
        except Exception as e:
            print(f"Error in reference_dropdown_value_changed: {e}")
            import traceback

            traceback.print_exc()

        # Add grid and style the plot
        self.canvas.axes.grid(True, alpha=0.5, color="dimgray")
        self.canvas.axes.set_facecolor("#262626")
        self.canvas.fig.set_facecolor("#262626")
        self.canvas.axes.set_xlabel("Time (samples)", color="white")
        self.canvas.axes.set_ylabel("Amplitude", color="white")
        self.canvas.axes.tick_params(axis="x", colors="white")
        self.canvas.axes.tick_params(axis="y", colors="white")
        self.canvas.draw()

    def threshold_field_value_changed(self):
        if not self.file or "signal" not in self.file or "EMG amplitude" in self.reference_dropdown.currentText():
            return

        self.coordinates = segmenttargets(self.file["signal"]["target"], 1, self.threshold_field.value())

        # Adjust coordinates
        for i in range(len(self.coordinates) // 2):
            self.coordinates[i * 2] = self.coordinates[i * 2] - self.file["signal"]["fsamp"]
            self.coordinates[i * 2 + 1] = self.coordinates[i * 2 + 1] + self.file["signal"]["fsamp"]

        # Clamp coordinates to valid range
        self.coordinates = np.clip(self.coordinates, 1, len(self.file["signal"]["target"]))

        # Update plot
        self.canvas.axes.clear()
        self.canvas.axes.plot(self.file["signal"]["target"], color=(0.95, 0.95, 0.95), linewidth=2)

        # Add vertical lines for segments
        for i in range(len(self.coordinates) // 2):
            ymin, ymax = float(np.min(self.file["signal"]["target"])), float(np.max(self.file["signal"]["target"]))
            cmap = plt.get_cmap("winter")
            color = cmap(i / float(len(self.coordinates) // 2))
            self.canvas.axes.axvline(x=self.coordinates[i * 2], color=color, linewidth=2)
            self.canvas.axes.axvline(x=self.coordinates[i * 2 + 1], color=color, linewidth=2)

        self.canvas.axes.set_ylim(
            float(np.min(self.file["signal"]["target"])), float(np.max(self.file["signal"]["target"]))
        )
        self.canvas.draw()

    def windows_field_value_changed(self):
        if not self.file or "signal" not in self.file:
            return

        self.coordinates = np.zeros(self.windows_field.value() * 2)

        # Update plot
        self.canvas.axes.clear()
        self.canvas.axes.plot(self.file["signal"]["target"], color=(0.95, 0.95, 0.95), linewidth=2)
        self.canvas.draw()

        # Let user select rectangles for windows
        for nwin in range(self.windows_field.value()):
            win_idx = nwin  # Create a local variable for the closure

            def onselect(eclick, erelease):
                if not hasattr(eclick, "xdata") or not hasattr(erelease, "xdata"):
                    return

                if self.file is None or "signal" not in self.file:
                    return

                x1, x2 = int(eclick.xdata), int(erelease.xdata)
                x1, x2 = sorted([x1, x2])
                x1 = max(1, x1)
                x2 = min(len(self.file["signal"]["target"]), x2)
                self.coordinates[win_idx * 2] = x1
                self.coordinates[win_idx * 2 + 1] = x2

                # Draw vertical lines
                ymin, ymax = float(np.min(self.file["signal"]["target"])), float(np.max(self.file["signal"]["target"]))
                cmap = plt.get_cmap("winter")
                color = cmap(win_idx / float(self.windows_field.value()))
                self.canvas.axes.axvline(x=x1, color=color, linewidth=2)
                self.canvas.axes.axvline(x=x2, color=color, linewidth=2)
                self.canvas.draw()

                # Remove the selector after use
                if self.rect_selector is not None:
                    self.rect_selector.disconnect_events()

            # Create rectangle selector
            self.rect_selector = RectangleSelector(
                self.canvas.axes,
                onselect,
                useblit=True,
                button=MouseButton.LEFT,
                minspanx=5,
                minspany=5,
                spancoords="pixels",
                interactive=True,
            )

            # Wait for selection
            while not (self.coordinates[nwin * 2] != 0 and self.coordinates[nwin * 2 + 1] != 0):
                plt.pause(0.1)

    def split_button_pushed(self):
        if not self.file or "signal" not in self.file or len(self.coordinates) == 0:
            return

        self.data = {"data": [], "auxiliary": [], "target": [], "path": []}

        # Split data into segments
        for i in range(len(self.coordinates) // 2):
            start, end = int(self.coordinates[i * 2]), int(self.coordinates[i * 2 + 1])
            self.data["data"].append(self.file["signal"]["data"][:, start:end])
            self.data["auxiliary"].append(self.file["signal"]["auxiliary"][:, start:end])
            self.data["target"].append(self.file["signal"]["target"][start:end])
            self.data["path"].append(self.file["signal"]["target"][start:end])

        # Save each segment as a separate file
        for i in range(len(self.coordinates) // 2):
            self.file["signal"]["data"] = self.data["data"][i]
            self.file["signal"]["auxiliary"] = self.data["auxiliary"][i]
            self.file["signal"]["target"] = self.data["target"][i]
            self.file["signal"]["path"] = self.data["target"][i]

            signal = self.file["signal"]
            sio.savemat(f"{self.pathname.text()}_{ i + 1 }", {"signal": signal}, do_compression=True)

        # Update pathname and plot with first segment
        self.pathname.setText(f"{self.pathname.text()}_1")

        self.canvas.axes.clear()
        self.canvas.axes.plot(self.data["target"][0], color=(0.95, 0.95, 0.95), linewidth=2)
        self.canvas.axes.set_ylim(np.min(self.data["target"][0]), np.max(self.data["target"][0]))
        self.canvas.draw()

        self.concatenate_button.setEnabled(False)
        self.split_button.setEnabled(False)

    def concatenate_button_pushed(self):
        if not self.file or "signal" not in self.file or len(self.coordinates) == 0:
            return

        # Initialize data containers
        data_segments = []
        aux_segments = []
        target_segments = []

        # Collect segments
        for i in range(len(self.coordinates) // 2):
            start, end = int(self.coordinates[i * 2]), int(self.coordinates[i * 2 + 1])
            data_segments.append(self.file["signal"]["data"][:, start:end])
            aux_segments.append(self.file["signal"]["auxiliary"][:, start:end])
            target_segments.append(self.file["signal"]["target"][start:end])

        # Concatenate along appropriate axis
        concatenated_data = np.hstack(data_segments)
        concatenated_auxiliary = np.hstack(aux_segments)
        concatenated_target = np.concatenate(target_segments)

        # Update the file with concatenated data
        self.file["signal"]["data"] = concatenated_data
        self.file["signal"]["auxiliary"] = concatenated_auxiliary
        self.file["signal"]["target"] = concatenated_target
        self.file["signal"]["path"] = concatenated_target

        # Update plot
        self.canvas.axes.clear()
        self.canvas.axes.plot(self.file["signal"]["target"], color=(0.95, 0.95, 0.95), linewidth=2)
        self.canvas.axes.set_ylim(
            float(np.min(self.file["signal"]["target"])), float(np.max(self.file["signal"]["target"]))
        )
        self.canvas.draw()

        # Save the updated file
        signal = self.file["signal"]
        sio.savemat(self.pathname.text(), {"signal": signal}, do_compression=True)

        self.concatenate_button.setEnabled(False)
        self.split_button.setEnabled(False)

    def ok_button_pushed(self):
        self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = SegmentSession()
    window.show()
    sys.exit(app.exec_())
