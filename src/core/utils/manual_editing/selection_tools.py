import pyqtgraph as pg
from PyQt5.QtCore import Qt
import numpy as np
from scipy.signal import find_peaks


class SelectionTool:
    """
    Tool for drawing selection rectangles on PyQtGraph plots.
    """

    def __init__(self, plot_widget, action_type, callback):
        self.plot_widget = plot_widget
        self.action_type = action_type
        self.callback = callback

        # Points in scene coordinates
        self.start_point = None
        self.current_point = None

        # Rectangle item to show the selection
        self.selection_rect = None

        # Connect event handlers
        self.original_mouse_press = plot_widget.mousePressEvent
        self.original_mouse_move = plot_widget.mouseMoveEvent
        self.original_mouse_release = plot_widget.mouseReleaseEvent

        plot_widget.mousePressEvent = self.mousePressEvent
        plot_widget.mouseMoveEvent = self.mouseMoveEvent
        plot_widget.mouseReleaseEvent = self.mouseReleaseEvent

        # Visual feedback to show this mode is active
        self.cursor_original = plot_widget.cursor()
        # Use the proper cursor enum value
        plot_widget.setCursor(Qt.CursorShape.CrossCursor)

        # Add text item to guide the user
        self.guide_text = pg.TextItem(
            text=f"Drag to draw {action_type.replace('_', ' ')} selection", color=(215, 85, 55), anchor=(0, 0)
        )
        self.guide_text.setPos(plot_widget.viewRect().left(), plot_widget.viewRect().top())
        plot_widget.addItem(self.guide_text)

    def mousePressEvent(self, event):
        """Handle mouse press to start drawing rectangle."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert mouse position to scene coordinates
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(event.pos())
            self.start_point = mouse_point
            self.current_point = mouse_point

            # Create rectangle item if not exists
            if self.selection_rect is None:
                self.selection_rect = pg.ROI(
                    pos=(self.start_point.x(), self.start_point.y()),
                    size=(0, 0),  # type:ignore
                    pen=pg.mkPen(color="#D95535", width=2),
                    movable=False,
                    resizable=False,
                )
                self.plot_widget.addItem(self.selection_rect)
            else:
                # Reset existing rectangle
                self.selection_rect.setPos(self.start_point.x(), self.start_point.y())
                self.selection_rect.setSize((0, 0))  # Using a tuple

            event.accept()
        else:
            # Pass other buttons to original handler
            self.original_mouse_press(event)

    def mouseMoveEvent(self, event):
        """Update rectangle as mouse moves."""
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self.start_point is not None
            and self.selection_rect is not None
        ):
            # Get current position in scene coordinates
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(event.pos())
            self.current_point = mouse_point

            # Calculate rectangle properties
            x = min(self.start_point.x(), self.current_point.x())
            y = min(self.start_point.y(), self.current_point.y())
            width = abs(self.current_point.x() - self.start_point.x())
            height = abs(self.current_point.y() - self.start_point.y())

            # Update rectangle
            self.selection_rect.setPos(x, y)
            self.selection_rect.setSize((width, height))  # Using a tuple

            event.accept()
        else:
            # Pass other moves to original handler
            self.original_mouse_move(event)

    def mouseReleaseEvent(self, event):
        """Finalize the selection on mouse release."""
        if event.button() == Qt.MouseButton.LeftButton and self.start_point is not None:
            # Get final position in scene coordinates
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(event.pos())
            self.current_point = mouse_point

            # Calculate final rectangle
            x_min = min(self.start_point.x(), self.current_point.x())
            x_max = max(self.start_point.x(), self.current_point.x())
            y_min = min(self.start_point.y(), self.current_point.y())
            y_max = max(self.start_point.y(), self.current_point.y())

            # Call the callback with the selection bounds
            self.cleanup()
            self.callback(x_min, x_max, y_min, y_max)

            event.accept()
        else:
            self.original_mouse_release(event)

    def cleanup(self):
        """Remove the selection tool and restore original handlers."""
        # Remove the rectangle from the plot
        if self.selection_rect is not None:
            self.plot_widget.removeItem(self.selection_rect)
            self.selection_rect = None

        # Remove the guide text
        if self.guide_text is not None:
            self.plot_widget.removeItem(self.guide_text)
            self.guide_text = None

        # Restore original event handlers
        self.plot_widget.mousePressEvent = self.original_mouse_press
        self.plot_widget.mouseMoveEvent = self.original_mouse_move
        self.plot_widget.mouseReleaseEvent = self.original_mouse_release

        # Restore cursor
        self.plot_widget.setCursor(self.cursor_original)


def process_selection(MUedition, action_type, array_idx, mu_idx, x_min, x_max, y_min, y_max):
    """
    Process the selection rectangle based on the action type.

    Args:
        MUedition: The MUedition data structure
        action_type: Type of action to perform (add_spikes, delete_spikes, delete_dr)
        array_idx: Index of the current array
        mu_idx: Index of the current MU
        x_min, x_max, y_min, y_max: Bounds of the selection rectangle
    """
    if not MUedition:
        return

    # Extract the sampling frequency as a scalar
    if MUedition["signal"]["fsamp"].ndim > 1:
        fsamp = float(MUedition["signal"]["fsamp"][0, 0])
    else:
        fsamp = float(MUedition["signal"]["fsamp"][0])

    if action_type == "add_spikes":
        # Add spikes in the selected region
        pulse_train = MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]
        time = MUedition["edition"]["time"]

        # Create a mask for the time and amplitude range
        time_mask = (time >= x_min) & (time <= x_max)
        amp_mask = (pulse_train >= y_min) & (pulse_train <= y_max)
        combined_mask = time_mask & amp_mask

        # Find peaks in the selected region
        peaks, _ = find_peaks(pulse_train[combined_mask], height=y_min, distance=round(0.005 * fsamp))

        # Convert peak indices to original signal indices
        if len(peaks) > 0:
            original_indices = np.where(combined_mask)[0][peaks]

            # Add new peaks to discharge times
            if (array_idx, mu_idx) not in MUedition["edition"]["Dischargetimes"]:
                MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = np.array([], dtype=int)

            MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = np.append(
                MUedition["edition"]["Dischargetimes"][array_idx, mu_idx], original_indices
            )

            # Sort and remove duplicates
            MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = np.unique(
                MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]
            )

    elif action_type == "delete_spikes":
        # Delete spikes in the selected region
        if (array_idx, mu_idx) in MUedition["edition"]["Dischargetimes"]:
            discharge_times = MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]
            time = MUedition["edition"]["time"]

            # Create masks for time and amplitude ranges
            time_mask = (time[discharge_times] >= x_min) & (time[discharge_times] <= x_max)
            pulse_train = MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :]
            amp_mask = (pulse_train[discharge_times] >= y_min) & (pulse_train[discharge_times] <= y_max)

            # Combine masks to find spikes to delete
            delete_mask = time_mask & amp_mask

            if np.any(delete_mask):
                # Keep only spikes that are not in the delete mask
                MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = discharge_times[~delete_mask]

    elif action_type == "delete_dr":
        # Delete discharge rates in the selected region
        if (array_idx, mu_idx) in MUedition["edition"]["Dischargetimes"]:
            discharge_times = MUedition["edition"]["Dischargetimes"][array_idx, mu_idx]

            if len(discharge_times) <= 1:
                return

            # Calculate discharge rate data
            distime = np.zeros(len(discharge_times) - 1)
            for i in range(len(discharge_times) - 1):
                midpoint = (discharge_times[i + 1] - discharge_times[i]) // 2 + discharge_times[i]
                distime[i] = midpoint / fsamp

            dr = 1.0 / (np.diff(discharge_times) / fsamp)

            # Find discharge rates within the selected region
            time_mask = (distime >= x_min) & (distime <= x_max)
            rate_mask = (dr >= y_min) & (dr <= y_max)

            # Combine masks to find discharge rates to delete
            delete_mask = time_mask & rate_mask

            if np.any(delete_mask):
                # For each interval to delete, determine which spike to remove
                delete_indices = []
                for i in range(len(delete_mask)):
                    if delete_mask[i]:
                        # Decide whether to delete first or second spike based on amplitude
                        if (
                            MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, discharge_times[i]]
                            < MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, discharge_times[i + 1]]
                        ):
                            delete_indices.append(i)
                        else:
                            delete_indices.append(i + 1)

                # Convert to numpy array and ensure unique
                delete_indices = np.unique(delete_indices)

                # Remove the spikes
                keep_mask = np.ones(len(discharge_times), dtype=bool)
                keep_mask[delete_indices] = False
                MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = discharge_times[keep_mask]

    return MUedition
