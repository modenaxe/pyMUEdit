import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QScrollArea,
)
import scipy.io as sio
from core.utils.config_and_input.segmenttargets import segmenttargets

# Import custom UI components
from ui.components import (
    CleanTheme,
    ActionButton,
    CleanCard,
    CollapsiblePanel,
    FormField,
    FormDropdown,
    FormSpinBox,
    FormDoubleSpinBox,
    SectionHeader,
    CleanScrollBar,
)


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
        self.setGeometry(100, 100, 900, 750)  # Increased size for better visualization
        self.setStyleSheet(f"background-color: {CleanTheme.BG_MAIN};")

        # Create scroll area for main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        CleanScrollBar.apply(scroll_area)

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Set the widget for the scroll area and set as central widget
        scroll_area.setWidget(main_widget)
        self.setCentralWidget(scroll_area)

        # Section header
        header = SectionHeader("Segment Session")
        main_layout.addWidget(header)

        # Settings card with controls
        settings_card = CleanCard()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(15)

        # Create input fields
        # Reference dropdown
        self.reference_panel = CollapsiblePanel("Reference Signal")
        self.reference_field = FormDropdown("Select reference signal")
        self.reference_dropdown = self.reference_field.dropdown
        self.reference_dropdown.addItem("EMG amplitude")
        self.reference_dropdown.currentIndexChanged.connect(self.reference_dropdown_value_changed)
        self.reference_panel.add_widget(self.reference_field)

        # Parameters panel
        self.params_panel = CollapsiblePanel("Segmentation Parameters")

        # Threshold field
        self.threshold_form_field = FormDoubleSpinBox("Threshold", 0.8, 0, 1, 0.1)
        self.threshold_field = self.threshold_form_field.spinbox
        self.threshold_field.valueChanged.connect(self.threshold_field_value_changed)
        self.threshold_field.setEnabled(False)
        self.params_panel.add_widget(self.threshold_form_field)

        # Windows field
        self.windows_form_field = FormSpinBox("Windows", 1, 1, 10)
        self.windows_field = self.windows_form_field.spinbox
        self.windows_field.valueChanged.connect(self.windows_field_value_changed)
        self.params_panel.add_widget(self.windows_form_field)

        # Add panels to settings layout
        settings_layout.addWidget(self.reference_panel)
        settings_layout.addWidget(self.params_panel)

        # Add settings layout to card
        settings_card.content_layout.addLayout(settings_layout)
        main_layout.addWidget(settings_card)

        # Visualization Card
        viz_card = CleanCard()
        viz_card.setMinimumHeight(400)  # Ensure card has enough height for plot
        viz_layout = QVBoxLayout()
        viz_layout.setSpacing(10)

        # Plot title
        plot_title = QLabel("Signal Visualization")
        plot_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        viz_layout.addWidget(plot_title)

        # Plot widget
        plot_container = QFrame()
        plot_container.setStyleSheet(
            f"""
            background-color: {CleanTheme.BG_CARD};
            border: 1px solid {CleanTheme.BORDER};
            border-radius: 5px;
            padding: 2px;
        """
        )
        plot_container_layout = QVBoxLayout(plot_container)
        plot_container_layout.setContentsMargins(5, 5, 5, 5)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(CleanTheme.BG_VISUALIZATION)
        self.plot_widget.setLabel("left", "Reference")
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.getAxis("left").setPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(color=CleanTheme.TEXT_PRIMARY))
        self.plot_widget.setMinimumHeight(350)  # Set minimum height to prevent squishing
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)  # Add grid for better readability

        plot_container_layout.addWidget(self.plot_widget)
        viz_layout.addWidget(plot_container)

        # Add a frame for the select button
        select_frame = QFrame()
        select_layout = QHBoxLayout(select_frame)

        # Create select button for manual ROI selection
        self.select_button = ActionButton("Select Region", primary=False)
        self.select_button.clicked.connect(self.create_roi)
        self.select_button.setVisible(False)
        select_layout.addWidget(self.select_button)
        select_layout.addStretch(1)  # Push button to the left

        viz_layout.addWidget(select_frame)

        # Add visualization layout to card
        viz_card.content_layout.addLayout(viz_layout)
        main_layout.addWidget(viz_card)

        # Actions card
        actions_card = CleanCard()
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        # Create action buttons
        self.concatenate_button = ActionButton("Concatenate", primary=False)
        self.concatenate_button.clicked.connect(self.concatenate_button_pushed)

        self.split_button = ActionButton("Split", primary=False)
        self.split_button.clicked.connect(self.split_button_pushed)

        self.ok_button = ActionButton("OK", primary=True)
        self.ok_button.clicked.connect(self.ok_button_pushed)

        # Add buttons to layout
        actions_layout.addWidget(self.concatenate_button)
        actions_layout.addWidget(self.split_button)
        actions_layout.addStretch(1)  # Push OK button to the right
        actions_layout.addWidget(self.ok_button)

        # Add actions layout to card
        actions_card.content_layout.addLayout(actions_layout)
        main_layout.addWidget(actions_card)

        # Hidden pathname field
        pathname_frame = QFrame()
        pathname_layout = QHBoxLayout(pathname_frame)
        pathname_label = QLabel("File Path:")
        pathname_label.setStyleSheet(f"color: {CleanTheme.TEXT_SECONDARY};")
        self.pathname = QLineEdit()
        self.pathname.setStyleSheet(
            f"""
            QLineEdit {{
                color: {CleanTheme.TEXT_SECONDARY};
                background-color: {CleanTheme.BG_CARD};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                padding: 6px;
            }}
            """
        )
        pathname_layout.addWidget(pathname_label)
        pathname_layout.addWidget(self.pathname)
        pathname_frame.setVisible(False)  # Hide by default
        main_layout.addWidget(pathname_frame)

        # Add stretch to push content to the top
        main_layout.addStretch(1)

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
                self.plot_widget.plot(emg_data["mean_envelope"], pen=pg.mkPen(color="#D95535", width=2))

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
                self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=CleanTheme.TEXT_PRIMARY, width=2))

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
            self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=CleanTheme.TEXT_PRIMARY, width=2))

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
            self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=CleanTheme.TEXT_PRIMARY, width=2))

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
            self.plot_widget.plot(target_segments[0], pen=pg.mkPen(color=CleanTheme.TEXT_PRIMARY, width=2))
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
            self.plot_widget.plot(signal["target"], pen=pg.mkPen(color=CleanTheme.TEXT_PRIMARY, width=2))
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
