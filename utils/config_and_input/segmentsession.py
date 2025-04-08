import numpy as np
import pyqtgraph as pg
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
import scipy.io as sio
from utils.config_and_input.segmenttargets import segmenttargets


class SegmentSession(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file = None
        self.coordinates = []
        self.data = {"data": [], "auxiliary": [], "target": [], "path": []}
        self.emg_amplitude_cache = None
        self.roi = None
        self.current_window = 0
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

        # Canvas for plotting - use PyQtGraph instead of matplotlib
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#262626")
        self.plot_widget.setLabel("left", "Reference")
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.getAxis("left").setPen(pg.mkPen(color="#f0f0f0"))
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(color="#f0f0f0"))
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(color="#f0f0f0"))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(color="#f0f0f0"))

        # Create select button for manual ROI selection
        self.select_button = QPushButton("Select Region")
        self.select_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-weight: bold;"
        )
        self.select_button.clicked.connect(self.create_roi)
        self.select_button.setVisible(False)

        # Add widgets to main layout
        main_layout.addWidget(top_panel)
        main_layout.addWidget(self.plot_widget)
        main_layout.addWidget(self.select_button)
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
            self.plot_widget.setYRange(y_min - y_margin, y_max + y_margin)
        else:
            self.plot_widget.setYRange(y_min, y_max)

    def reference_dropdown_value_changed(self):
        if not self.pathname.text() or not hasattr(self, "file") or self.file is None:
            return

        self.plot_widget.clear()

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
                    self.plot_widget.plot(
                        emg_data["channel_envelopes"][i, :], pen=pg.mkPen(color=(128, 128, 128, 128), width=0.25)
                    )

                # Plot the mean envelope
                self.plot_widget.plot(emg_data["mean_envelope"], pen=pg.mkPen(color=(217, 84, 26), width=2))

                self.set_safe_ylim(emg_data["y_min"], emg_data["y_max"])
                self.threshold_field.setEnabled(False)

            except Exception as e:
                print(f"Error calculating EMG amplitude: {e}")
                text_item = pg.TextItem(text=f"Error: {str(e)}", color=(255, 0, 0))
                text_item.setPos(50, 50)
                self.plot_widget.addItem(text_item)
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
                self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=(242, 242, 242), width=2))

                if not np.any(np.isnan(signal["target"])):
                    self.set_safe_ylim(np.min(signal["target"]), np.max(signal["target"]))

                self.threshold_field.setEnabled(True)
            except Exception as e:
                print(f"Error accessing auxiliary signal: {e}")
                text_item = pg.TextItem(text="Error accessing auxiliary signal", color=(255, 0, 0))
                text_item.setPos(50, 50)
                self.plot_widget.addItem(text_item)

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
            self.plot_widget.clear()
            self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=(242, 242, 242), width=2))

            # Add vertical lines for segments
            for i in range(len(self.coordinates) // 2):
                # Create a gradient of colors for different segments
                hue = 0.6 - (i / (len(self.coordinates) // 2) * 0.3)  # Blue-ish hues
                color = pg.hsvColor(hue, 0.8, 0.9)

                # Add vertical lines using PyQtGraph's InfiniteLine
                line1 = pg.InfiniteLine(pos=self.coordinates[i * 2], angle=90, pen=pg.mkPen(color=color, width=2))
                line2 = pg.InfiniteLine(pos=self.coordinates[i * 2 + 1], angle=90, pen=pg.mkPen(color=color, width=2))
                self.plot_widget.addItem(line1)
                self.plot_widget.addItem(line2)

            self.set_safe_ylim(np.min(signal["target"]), np.max(signal["target"]))

        except Exception as e:
            print(f"Error in threshold_field_value_changed: {e}")

    def create_roi(self):
        """Create a PyQtGraph region of interest for selection"""
        if not self.file or "signal" not in self.file:
            return

        signal = self.file["signal"][0, 0]

        # Create a new ROI for selection using PyQtGraph's LinearRegionItem
        roi = pg.LinearRegionItem(orientation="vertical")
        roi.setBounds([0, len(signal["target"])])

        # Store reference to ROI
        self.roi = roi
        self.plot_widget.addItem(roi)

        # Connect signal for ROI change
        roi.sigRegionChangeFinished.connect(self.on_roi_change)

    def on_roi_change(self):
        """Handle changes to the region of interest"""
        if self.roi is None or not self.file or "signal" not in self.file:
            return

        # Get selected region
        region = self.roi.getRegion()
        x1, x2 = int(region[0]), int(region[1])  # type:ignore
        x1, x2 = sorted([x1, x2])

        signal = self.file["signal"][0, 0]
        x1 = max(1, x1)
        x2 = min(len(signal["target"]), x2)

        # Update coordinates for the current window
        nwin = self.current_window
        if len(self.coordinates) < (nwin + 1) * 2:
            # Expand coordinates array if needed
            self.coordinates = np.pad(self.coordinates, (0, (nwin + 1) * 2 - len(self.coordinates)))

        self.coordinates[nwin * 2] = x1
        self.coordinates[nwin * 2 + 1] = x2

        # Draw vertical lines to mark the selection
        hue = 0.6 - (nwin / self.windows_field.value() * 0.3)
        color = pg.hsvColor(hue, 0.8, 0.9)

        # We'll use a tag in the name to identify lines for each window
        line_tag = f"window_{nwin}_line"

        # Find and remove any existing lines for this window
        for item in self.plot_widget.items():
            if isinstance(item, pg.InfiniteLine) and hasattr(item, "name") and item.name() == line_tag:
                self.plot_widget.removeItem(item)

        # Add new lines with PyQtGraph's InfiniteLine
        line1 = pg.InfiniteLine(pos=x1, angle=90, pen=pg.mkPen(color=color, width=2), name=line_tag)
        line2 = pg.InfiniteLine(pos=x2, angle=90, pen=pg.mkPen(color=color, width=2), name=line_tag)

        self.plot_widget.addItem(line1)
        self.plot_widget.addItem(line2)

        # Remove the ROI after selection is done
        self.plot_widget.removeItem(self.roi)
        self.roi = None

        # Move to next window if we're not done
        self.current_window += 1
        if self.current_window < self.windows_field.value():
            # Create another ROI for the next selection
            self.create_roi()
        else:
            # Reset for future selections
            self.current_window = 0
            self.select_button.setVisible(False)

    def windows_field_value_changed(self):
        if not self.file or "signal" not in self.file:
            return

        try:
            windows = self.windows_field.value()
            self.coordinates = np.zeros(windows * 2, dtype=int)
            signal = self.file["signal"][0, 0]

            # Update plot
            self.plot_widget.clear()
            self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=(242, 242, 242), width=2))

            # Reset current window counter and show select button
            self.current_window = 0
            self.select_button.setVisible(True)

            # Start the selection process with PyQtGraph ROI
            self.create_roi()

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
            self.plot_widget.clear()
            self.plot_widget.plot(target_segments[0], pen=pg.mkPen(color=(242, 242, 242), width=2))
            if not np.any(np.isnan(target_segments[0])):
                self.set_safe_ylim(np.min(target_segments[0]), np.max(target_segments[0]))

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

            # Update plot with PyQtGraph
            self.plot_widget.clear()
            self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=(242, 242, 242), width=2))
            if not np.any(np.isnan(signal["target"])):
                self.set_safe_ylim(np.min(signal["target"]), np.max(signal["target"]))

            # Save the concatenated file
            sio.savemat(self.pathname.text(), {"signal": signal}, do_compression=True)

            self.concatenate_button.setEnabled(False)
            self.split_button.setEnabled(False)
            self.emg_amplitude_cache = None

        except Exception as e:
            print(f"Error in concatenate_button_pushed: {e}")

    def ok_button_pushed(self):
        self.close()
