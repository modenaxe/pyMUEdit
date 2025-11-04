
import numpy as np
from PyQt5.QtCore import Qt
import pyqtgraph as pg



def safe_set_range(self, plot, xrange=None, yrange=None):
    if not plot:
        return
    self.update_plot_setRange = True
    if xrange:
        plot.setXRange(xrange[0], xrange[1])
    if yrange:
        plot.setYRange(yrange[0], yrange[1])
    self.update_plot_setRange = False

def update_spike_train_plot(self, array_idx, mu_idx, pulse_train, color="#D95535"):
    """Update pulse train plot only without changing layout or other widgets."""
    print("update_spike_train_plot")

    # Clear existing plots
    self.spiketrain_plot.clear()

    # Show and update spike train plot
    time_vector = self.MUedition["edition"]["time"]
    curve_aa = pg.PlotDataItem(
        time_vector,
        pulse_train,
        pen=pg.mkPen(color="#333333", width=1),
        autoDownsample=True,
        antialias=True,
    )
    curve_not_aa = pg.PlotDataItem(
        time_vector,
        pulse_train,
        pen=pg.mkPen(color="#333333", width=1),
        antialias=False,
        autoDownsample=True
    )
    self.spiketrainCurves = [curve_aa, curve_not_aa]
    if pg.getConfigOption('antialias'):
        self.spiketrain_plot.addItem(curve_aa)
    else:
        self.spiketrain_plot.addItem(curve_not_aa)

    if self.resetPlot:
        safe_set_range(self, self.spiketrain_plot, yrange=[min(pulse_train)*1.2, max(pulse_train)*1.2])

    # Plot reference signal if available
    if "target" in self.MUedition["signal"] and self.MUedition["signal"]["target"].size > 0:
        target_data = self.MUedition["signal"]["target"]
        if target_data.ndim > 1:
            target_data = target_data[0]
        if isinstance(target_data, np.ndarray) and len(target_data) == len(time_vector):
            target_max = np.max(target_data)
            if target_max > 0:
                target_normalized = target_data / target_max
                curve = self.spiketrain_plot.plot(
                    time_vector,
                    target_normalized,
                    pen=pg.mkPen(color="#1B5E20", width=2, style=Qt.PenStyle.DashLine),
                    antialias=True,
                )
                curve.setDownsampling(auto=True, method="subsample")
                curve.setClipToView(True)
                self.spiketrainCurves.append(curve)

    # Plot discharge times
    discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))
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

        if x_values:
            scatter.addPoints(x=x_values, y=y_values, pen=None, brush=pg.mkBrush(color), size=10)
            self.spiketrain_plot.addItem(scatter)
        self.spiketrainCurves.append(scatter)

def update_dr_plot(self, discharge_times):
    self.dr_plot.clear()

    if len(discharge_times) > 1:
        # Calculate discharge times for plotting
        distime = np.zeros(len(discharge_times) - 1)
        for i in range(len(discharge_times) - 1):
            midpoint = (discharge_times[i + 1] - discharge_times[i]) // 2 + discharge_times[i]
            distime[i] = midpoint / float(self.MUedition["signal"]["fsamp"][0, 0])

        # Calculate discharge rates
        dr = 1.0 / (np.diff(discharge_times) / float(self.MUedition["signal"]["fsamp"][0, 0]))

        # Plot as scatter plot
        scatter_dr = pg.ScatterPlotItem()
        scatter_dr.addPoints(x=distime, y=dr, pen=None, brush=pg.mkBrush("#D95535"), size=10)
        self.dr_plot.addItem(scatter_dr)

        # Set y-axis range with margin
        if len(dr) > 0:
            dr_max = np.max(dr)
            if self.resetPlot:
                safe_set_range(self, self.dr_plot, yrange=[0, dr_max * 1.5])
            # self.dr_plot.setYRange(0, dr_max * 1.5)
