import pyqtgraph as pg
from PyQt5.QtWidgets import QFileDialog

class WaveformPlotWidget(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.setBackground('w')
        self.showGrid(x=True, y=True)
        self.addLegend()
        self.plot_items = {}
        self.markers = {}
        self.setLabel('bottom', 'Time')
        self.setLabel('left', 'Amplitude')
        # Make axes lines bolder for visibility
        try:
            axis_pen = pg.mkPen(color=(0, 0, 0), width=2)
            self.getAxis('left').setPen(axis_pen)
            self.getAxis('bottom').setPen(axis_pen)
        except Exception:
            pass
        # For zoom/export, enable mouse
        self.setMouseEnabled(x=True, y=True)
        # sliding window in seconds for the x-axis (show last N seconds)
        self.window_seconds = 10

    def add_parameter_curve(self, param):
        if param.name in self.plot_items:
            return
        color = pg.intColor(len(self.plot_items))  # Cycle colors
        item = self.plotItem.plot([], [], pen=pg.mkPen(color=color, width=2), name=param.name)
        self.plot_items[param.name] = item
        # Create a scatter marker to show the instantaneous value
        # Markers use black color for contrast regardless of curve color
        marker = pg.ScatterPlotItem(size=8, brush=pg.mkBrush((0, 0, 0)), pen=pg.mkPen((0, 0, 0)))
        try:
            self.plotItem.addItem(marker)
        except Exception:
            # fallback: add to plot directly
            self.addItem(marker)
        self.markers[param.name] = marker
        item.setVisible(param.enabled)
        marker.setVisible(param.enabled)

    def remove_curve(self, param_name):
        # remove line if present
        if param_name in self.plot_items:
            try:
                self.removeItem(self.plot_items[param_name])
            except Exception:
                pass
            try:
                del self.plot_items[param_name]
            except KeyError:
                pass

        # remove marker if present
        if param_name in self.markers:
            try:
                self.removeItem(self.markers[param_name])
            except Exception:
                pass
            try:
                del self.markers[param_name]
            except KeyError:
                pass

    def toggle_curve(self, param_name, enabled):
        if param_name in self.plot_items:
            self.plot_items[param_name].setVisible(enabled)
        if param_name in self.markers:
            self.markers[param_name].setVisible(enabled)

    def update_curve(self, param_name, new_time, new_value):
        # If curve doesn't exist yet (e.g., sample arrived before curve was created), create it
        if param_name not in self.plot_items:
            # create a default param-like object for plotting
            class _P:
                def __init__(self, name):
                    self.name = name
                    self.enabled = True
            self.add_parameter_curve(_P(param_name))

        if param_name in self.plot_items:
            item = self.plot_items[param_name]
            x, y = item.getData()
            # Convert to lists in case numpy arrays are returned
            if x is None:
                x = []
                y = []
            else:
                try:
                    x = list(x)
                    y = list(y)
                except Exception:
                    x = [x]
                    y = [y]
            x.append(new_time)
            y.append(new_value)
            if len(x) > 10000:  # Limit for performance
                x = x[-10000:]
                y = y[-10000:]
            item.setData(x, y)
            # Update marker to show instantaneous value
            marker = self.markers.get(param_name)
            if marker is not None:
                try:
                    marker.setData([x[-1]], [y[-1]])
                except Exception:
                    pass
            # Auto-scroll to latest (show last N seconds)
            try:
                start_x = new_time - self.window_seconds
                self.setXRange(start_x, new_time)
            except Exception:
                # fallback
                self.setXRange(max(0, new_time - self.window_seconds), new_time)

    def clear_data(self):
        """Clear plotted data points (keeps curve objects in place)."""
        for name, item in list(self.plot_items.items()):
            try:
                item.setData([], [])
            except Exception:
                pass
        for name, marker in list(self.markers.items()):
            try:
                marker.setData([], [])
            except Exception:
                pass

    def update_curve_settings(self, param):
        # Refresh if needed, e.g., color or name change
        pass

    def export_png(self):
        filename, _ = QFileDialog.getSaveFileName(None, "Export PNG", "", "PNG (*.png)")
        if filename:
            exporter = pg.exporters.ImageExporter(self.plotItem)
            exporter.export(filename)