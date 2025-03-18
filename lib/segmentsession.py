import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
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
        self.data = {"data": [], "auxiliary": [], "target": [], "path": []}
        self.emg_amplitude_cache = None
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
        self.threshold_field = QDoubleSpinBox()
        self.threshold_field.setRange(0, 1)
        self.threshold_field.setSingleStep(0.1)
        self.threshold_field.setStyleSheet("color: #f0f0f0; background-color: #262626; font-family: 'Poppins';")
        self.threshold_field.valueChanged.connect(self.threshold_field_value_changed)
        self.threshold_field.setEnabled(False)

        # Windows field
        windows_label = QLabel("Windows")
        windows_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins';")
        self.windows_field = QSpinBox()
        self.windows_field.setRange(1, 10)
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

        # Canvas for plotting
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.axes.set_xlabel("Time (s)")
        self.canvas.axes.set_ylabel("Reference")

        # Add widgets to main layout
        main_layout.addWidget(top_panel)
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(self.pathname)

    def initialize_with_file(self):
        if self.pathname.text():
            try:
                self.file = sio.loadmat(self.pathname.text())
                self.reference_dropdown.clear()
                self.reference_dropdown.addItem("EMG amplitude")

                if "signal" in self.file and "auxiliaryname" in self.file["signal"][0, 0].dtype.names:
                    aux_names = self.file["signal"][0, 0]["auxiliaryname"]
                    # Handle various formats of auxiliaryname
                    if isinstance(aux_names, np.ndarray) and aux_names.ndim > 1:
                        try:
                            for name in aux_names[0, 0][0]:
                                self.reference_dropdown.addItem(str(name))
                        except:
                            # Fall back if structure is different
                            for name in np.array(aux_names).flatten():
                                self.reference_dropdown.addItem(str(name))
                    else:
                        for name in aux_names:
                            self.reference_dropdown.addItem(str(name))

                self.reference_dropdown_value_changed()
            except Exception as e:
                print(f"Error loading file: {e}")

    def calculate_emg_amplitude(self, signal_data, fsamp):
        if self.emg_amplitude_cache is not None:
            return self.emg_amplitude_cache

        channels = min(signal_data.shape[0], signal_data.shape[0] // 2)
        if channels <= 0:
            raise ValueError("Not enough channels to calculate EMG amplitude")

        window_size = int(fsamp)
        window = np.ones(window_size) / window_size

        channel_envelopes = np.zeros((channels, signal_data.shape[1]))

        for i in range(channels):
            rectified = np.abs(signal_data[i, :])
            channel_envelopes[i, :] = np.convolve(rectified, window, mode="same")

        # Calculate mean across channels
        mean_envelope = np.mean(channel_envelopes, axis=0)

        # Cache the results
        self.emg_amplitude_cache = {
            "channel_envelopes": channel_envelopes[:16],
            "mean_envelope": mean_envelope,
            "y_min": np.min(channel_envelopes),
            "y_max": np.max(channel_envelopes),
        }

        return self.emg_amplitude_cache

    def set_safe_ylim(self, y_min, y_max):
        if y_min == y_max:
            y_margin = abs(y_min) * 0.1 if y_min != 0 else 0.1
            self.canvas.axes.set_ylim(y_min - y_margin, y_max + y_margin)
        else:
            self.canvas.axes.set_ylim(y_min, y_max)

    def reference_dropdown_value_changed(self):
        if not self.pathname.text() or not hasattr(self, "file") or self.file is None:
            return

        self.canvas.axes.clear()

        if "EMG amplitude" in self.reference_dropdown.currentText():
            try:
                signal_data = self.file["signal"][0, 0]["data"]
                fsamp = self.file["signal"][0, 0]["fsamp"][0, 0]

                emg_data = self.calculate_emg_amplitude(signal_data, fsamp)

                # Store in the signal structure
                self.file["signal"][0, 0]["target"] = emg_data["mean_envelope"]
                self.file["signal"][0, 0]["path"] = emg_data["mean_envelope"]

                # Plot data - plot only a subset of channels to improve performance
                for i in range(emg_data["channel_envelopes"].shape[0]):
                    self.canvas.axes.plot(emg_data["channel_envelopes"][i, :], color=(0.5, 0.5, 0.5), linewidth=0.25)

                # Plot the mean envelope
                self.canvas.axes.plot(emg_data["mean_envelope"], color=(0.85, 0.33, 0.10), linewidth=2)

                self.set_safe_ylim(emg_data["y_min"], emg_data["y_max"])
                self.threshold_field.setEnabled(False)

            except Exception as e:
                print(f"Error calculating EMG amplitude: {e}")
                self.canvas.axes.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center", color="red")
        else:
            try:
                signal = self.file["signal"][0, 0]
                aux_names = signal["auxiliaryname"]

                if isinstance(aux_names, np.ndarray) and aux_names.ndim > 1:
                    try:
                        aux_names = aux_names[0, 0][0]
                    except:
                        aux_names = np.array(aux_names).flatten()

                idx = None
                for i, name in enumerate(aux_names):
                    if self.reference_dropdown.currentText() in str(name):
                        idx = i
                        break

                if idx is None:
                    raise ValueError(f"Auxiliary signal '{self.reference_dropdown.currentText()}' not found")

                signal["target"] = signal["auxiliary"][idx, :]
                self.canvas.axes.plot(signal["target"], color=(0.95, 0.95, 0.95), linewidth=2)

                if not np.any(np.isnan(signal["target"])):
                    self.set_safe_ylim(np.min(signal["target"]), np.max(signal["target"]))

                self.threshold_field.setEnabled(True)
            except Exception as e:
                print(f"Error accessing auxiliary signal: {e}")
                self.canvas.axes.text(
                    0.5, 0.5, "Error accessing auxiliary signal", ha="center", va="center", color="red"
                )

        self.canvas.draw()

    def threshold_field_value_changed(self):
        if not self.file or "signal" not in self.file or "EMG amplitude" in self.reference_dropdown.currentText():
            return

        try:
            signal = self.file["signal"][0, 0]
            self.coordinates = segmenttargets(signal["target"], 1, self.threshold_field.value())

            fsamp = signal["fsamp"][0, 0]
            for i in range(len(self.coordinates) // 2):
                self.coordinates[i * 2] = self.coordinates[i * 2] - fsamp
                self.coordinates[i * 2 + 1] = self.coordinates[i * 2 + 1] + fsamp

            # Clamp coordinates to valid range
            self.coordinates = np.clip(self.coordinates, 1, len(signal["target"]))

            # Update plot
            self.canvas.axes.clear()
            self.canvas.axes.plot(signal["target"], color=(0.95, 0.95, 0.95), linewidth=2)

            # Add vertical lines for segments
            for i in range(len(self.coordinates) // 2):
                cmap = plt.get_cmap("winter")
                color = cmap(i / float(len(self.coordinates) // 2))
                self.canvas.axes.axvline(x=self.coordinates[i * 2], color=color, linewidth=2)
                self.canvas.axes.axvline(x=self.coordinates[i * 2 + 1], color=color, linewidth=2)

            self.set_safe_ylim(np.min(signal["target"]), np.max(signal["target"]))

            self.canvas.draw()
        except Exception as e:
            print(f"Error in threshold_field_value_changed: {e}")

    def windows_field_value_changed(self):
        if not self.file or "signal" not in self.file:
            return

        try:
            windows = self.windows_field.value()
            self.coordinates = np.zeros(windows * 2, dtype=int)
            signal = self.file["signal"][0, 0]

            # Update plot
            self.canvas.axes.clear()
            self.canvas.axes.plot(signal["target"], color=(0.95, 0.95, 0.95), linewidth=2)
            self.canvas.draw()

            # Set up the rectangle selector for each window
            for nwin in range(windows):

                def on_select(eclick, erelease, nwin=nwin):
                    if not hasattr(eclick, "xdata") or not hasattr(erelease, "xdata"):
                        return

                    x1, x2 = int(eclick.xdata), int(erelease.xdata)
                    x1, x2 = sorted([x1, x2])
                    x1 = max(1, x1)
                    x2 = min(len(signal["target"]), x2)

                    self.coordinates[nwin * 2] = x1
                    self.coordinates[nwin * 2 + 1] = x2

                    # Draw vertical lines
                    cmap = plt.get_cmap("winter")
                    color = cmap(nwin / float(windows))
                    self.canvas.axes.axvline(x=x1, color=color, linewidth=2)
                    self.canvas.axes.axvline(x=x2, color=color, linewidth=2)
                    self.canvas.draw()

                rect_selector = RectangleSelector(
                    self.canvas.axes,
                    on_select,
                    useblit=True,
                    button=MouseButton(MouseButton.LEFT),
                    minspanx=5,
                    minspany=5,
                    spancoords="pixels",
                    interactive=True,
                )

                print(f"Please select region {nwin+1} of {windows}")
                plt.waitforbuttonpress()
        except Exception as e:
            print(f"Error in windows_field_value_changed: {e}")

    def split_button_pushed(self):
        if not self.file or "signal" not in self.file or len(self.coordinates) == 0:
            return

        try:
            signal = self.file["signal"][0, 0]
            num_segments = len(self.coordinates) // 2
            data_segments = []
            aux_segments = []
            target_segments = []

            # Extract segments
            for i in range(num_segments):
                start, end = int(self.coordinates[i * 2]), int(self.coordinates[i * 2 + 1])
                data_segments.append(signal["data"][:, start:end])
                aux_segments.append(signal["auxiliary"][:, start:end])
                target_segments.append(signal["target"][start:end])

            # Save each segment
            pathname_base = self.pathname.text().replace(".mat", "")
            for i in range(num_segments):
                signal["data"] = data_segments[i]
                signal["auxiliary"] = aux_segments[i]
                signal["target"] = target_segments[i]
                signal["path"] = target_segments[i]

                savename = f"{pathname_base}_{i+1}.mat"
                sio.savemat(savename, {"signal": signal}, do_compression=True)

            # Update pathname and plot with first segment
            self.pathname.setText(f"{pathname_base}_1.mat")
            self.canvas.axes.clear()
            self.canvas.axes.plot(target_segments[0], color=(0.95, 0.95, 0.95), linewidth=2)
            if not np.any(np.isnan(target_segments[0])):
                self.set_safe_ylim(np.min(target_segments[0]), np.max(target_segments[0]))
            self.canvas.draw()

            self.concatenate_button.setEnabled(False)
            self.split_button.setEnabled(False)
            self.emg_amplitude_cache = None

        except Exception as e:
            print(f"Error in split_button_pushed: {e}")

    def concatenate_button_pushed(self):
        if not self.file or "signal" not in self.file or len(self.coordinates) == 0:
            return

        try:
            signal = self.file["signal"][0, 0]
            num_segments = len(self.coordinates) // 2
            data_segments = []
            aux_segments = []
            target_segments = []

            # Collect segments
            for i in range(num_segments):
                start, end = int(self.coordinates[i * 2]), int(self.coordinates[i * 2 + 1])
                data_segments.append(signal["data"][:, start:end])
                aux_segments.append(signal["auxiliary"][:, start:end])
                target_segments.append(signal["target"][start:end])

            # Concatenate data
            signal["data"] = np.hstack(data_segments)
            signal["auxiliary"] = np.hstack(aux_segments)
            signal["target"] = np.concatenate(target_segments)
            signal["path"] = signal["target"]

            # Update plot
            self.canvas.axes.clear()
            self.canvas.axes.plot(signal["target"], color=(0.95, 0.95, 0.95), linewidth=2)
            if not np.any(np.isnan(signal["target"])):
                self.set_safe_ylim(np.min(signal["target"]), np.max(signal["target"]))
            self.canvas.draw()

            # Save the concatenated file
            sio.savemat(self.pathname.text(), {"signal": signal}, do_compression=True)

            self.concatenate_button.setEnabled(False)
            self.split_button.setEnabled(False)
            self.emg_amplitude_cache = None

        except Exception as e:
            print(f"Error in concatenate_button_pushed: {e}")

    def ok_button_pushed(self):
        self.close()
