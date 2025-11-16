
import numpy as np
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from core.logger import logger

def safe_set_range(self, plot, xrange=None, yrange=None):
    if not plot:
        return
    self.update_plot_setRange = True
    if xrange:
        plot.setXRange(xrange[0], xrange[1])
    if yrange:
        plot.setYRange(yrange[0], yrange[1])
    self.update_plot_setRange = False

def update_spike_train_plot(
    self,
    array_idx,
    mu_idx,
    pulse_train,
    color="#D95535",
    overlay=False,
):
    """
    Update pulse train plot only without changing layout or other widgets.

    Overlay plot will change the scatter plot to be green on top of 
    red with slight opacity.
    """

    logger.debug(f"update_spike_train_plot {'(overlay)' if overlay else ''}")

    time_vector = self.MUedition["edition"]["time"]

    # Clear existing plots only if not overlaying
    if not overlay:
        self.spiketrain_plot.clear()

    # Create the main pen
    pen_main = pg.mkPen(
        color= "#333333",
        width=1 if not overlay else 2,
        style=Qt.PenStyle.SolidLine if not overlay else Qt.PenStyle.DashLine,
    )

    # Handles anti-aliasing toggle
    curve_aa = pg.PlotDataItem(
        time_vector,
        pulse_train,
        pen=pen_main,
        autoDownsample=True,
        antialias=True,
    )
    curve_not_aa = pg.PlotDataItem(
        time_vector,
        pulse_train,
        pen=pen_main,
        autoDownsample=True,
        antialias=False,
    )

    # Set configuration of anti-alias
    if pg.getConfigOption("antialias"):
        self.spiketrain_plot.addItem(curve_aa)
    else:
        self.spiketrain_plot.addItem(curve_not_aa)
    
    # Resets the plot if not overlay
    if not overlay:
        self.spiketrainCurves = [curve_aa, curve_not_aa]
        if self.resetPlot:
            safe_set_range(
                self,
                self.spiketrain_plot,
                yrange=[min(pulse_train) * 1.2, max(pulse_train) * 1.2],
            )
    else:
        self.spiketrainCurves.extend([curve_aa, curve_not_aa])

    # Plots reference signal
    if (
        "target" in self.MUedition["signal"]
        and self.MUedition["signal"]["target"].size > 0
    ):
        target_data = self.MUedition["signal"]["target"]
        if target_data.ndim > 1:
            target_data = target_data[0]
        if (
            isinstance(target_data, np.ndarray)
            and len(target_data) == len(time_vector)
        ):
            target_max = np.max(target_data)
            if target_max > 0:
                target_normalized = target_data / target_max
                curve_target = self.spiketrain_plot.plot(
                    time_vector,
                    target_normalized,
                    pen=pg.mkPen(
                        color="#1B5E20",
                        width=2,
                        style=Qt.PenStyle.DashLine,
                    ),
                    antialias=True,
                )
                curve_target.setDownsampling(auto=True, method="subsample")
                curve_target.setClipToView(True)
                self.spiketrainCurves.append(curve_target)

    # Plot discharge times
    discharge_times = self.MUedition["edition"]["Dischargetimes"].get(
        (array_idx, mu_idx), np.array([])
    )
    if len(discharge_times) > 0:
        scatter = pg.ScatterPlotItem()
        x_values, y_values = [], []
        window_size = 10

        for dt in discharge_times:
            if 0 <= dt < len(pulse_train):
                start = int(max(0, dt - window_size))
                end = int(min(len(pulse_train), dt + window_size + 1))
                window = pulse_train[start:end]
                if len(window) > 0:
                    local_max_idx = start + np.argmax(window)
                    x_values.append(time_vector[local_max_idx])
                    y_values.append(pulse_train[local_max_idx])

            brush_color = pg.mkColor(color if overlay else "#D95535")

            scatter.addPoints(
                x=x_values,
                y=y_values,
                pen=None,
                brush=pg.mkBrush(brush_color),
                size=10 if not overlay else 8,
            )
            self.spiketrain_plot.addItem(scatter)
            self.spiketrainCurves.append(scatter)

def update_dr_plot(self, discharge_times, color="#D95535", overlay=False):
    """
    Update or overlay discharge rate plot.
    """
    if not overlay:
        self.dr_plot.clear()

    if len(discharge_times) > 1:
        # Calculate discharge times for plotting
        fsamp = float(self.MUedition["signal"]["fsamp"][0, 0])
        distime = np.zeros(len(discharge_times) - 1)
        for i in range(len(discharge_times) - 1):
            midpoint = (discharge_times[i + 1] - discharge_times[i]) // 2 + discharge_times[i]
            distime[i] = midpoint / fsamp

        # Calculate discharge rates
        dr = 1.0 / (np.diff(discharge_times) / fsamp)

        # Plot as scatter plot
        scatter_dr = pg.ScatterPlotItem()
        scatter_dr.addPoints(
            x=distime,
            y=dr,
            pen=None,
            brush=pg.mkBrush(color if overlay else "#D95535"),
            size=10 if not overlay else 8
        )
        self.dr_plot.addItem(scatter_dr)

        # Set y-axis range with margin
        if not overlay and len(dr) > 0:
            dr_max = np.max(dr)
            if self.resetPlot:
                safe_set_range(self, self.dr_plot, yrange=[0, dr_max * 1.5])
