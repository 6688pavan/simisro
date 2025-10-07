import pyqtgraph as pg
from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QPushButton
from PyQt5.QtCore import QTimer
from collections import deque
from core.waveform import make_waveform

class WaveformPlotWidget(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.setBackground('k')  # Black background
        self.showGrid(x=True, y=True)
        self.setLabel('left', 'Value')
        self.setLabel('bottom', 'Time (s)')
        self.curves = {}  # name -> (plotItem, data_deque)
        self.marker = None
        self.window_seconds = 10.0  # Rolling time window for display

    def update_waveform(self, params, current_time, time_increment=1.0):
        for p in params:
            if p.enabled_in_graph:
                if p.samples_per_500ms == 1:  # Major cycle - single value
                    if p.dtype == "float":
                        # Float major: continuous waveform
                        wf = make_waveform(p.waveform, p.freq, p.phase, p.full_sweep)
                        y = wf.value(current_time, p.min_v, p.max_v)
                        self.update_sample(p.name, current_time, y)
                        self.set_marker(current_time, y)
                    else:
                        # Bit major: discrete min/max points only
                        wf = make_waveform(p.waveform, p.freq, p.phase, p.full_sweep)
                        analog = wf.value(current_time, p.min_v, p.max_v)
                        threshold = (p.min_v + p.max_v) / 2.0
                        y = p.min_v if analog < threshold else p.max_v
                        self.update_sample(p.name, current_time, y)
                        self.set_marker(current_time, y)
                else:  # Minor cycle - 5 samples without any phase-offset (display-only)
                    wf = make_waveform(p.waveform, p.freq, p.phase, p.full_sweep)
                    sample_spacing = time_increment / 5.0
                    for i in range(5):
                        sample_time = current_time + i * sample_spacing
                        if p.dtype == "float":
                            y = wf.value(sample_time, p.min_v, p.max_v)
                        else:
                            # Bit minor: discrete min/max at each sub-sample
                            analog = wf.value(sample_time, p.min_v, p.max_v)
                            threshold = (p.min_v + p.max_v) / 2.0
                            y = p.min_v if analog < threshold else p.max_v
                        self.update_sample(p.name, sample_time, y)
                    
                    # Set marker at the first sample time
                    if p.dtype == "float":
                        first_y = wf.value(current_time, p.min_v, p.max_v)
                    else:
                        analog = wf.value(current_time, p.min_v, p.max_v)
                        threshold = (p.min_v + p.max_v) / 2.0
                        first_y = p.min_v if analog < threshold else p.max_v
                    self.set_marker(current_time, first_y)
        # Keep only the last window worth of data and pan the view
        self._prune_window(current_time)
        start_x = current_time - self.window_seconds
        self.setXRange(start_x, current_time, padding=0)

    def update_sample(self, name, t, y):
        if name not in self.curves:
            self.add_param(name)
        plot, data = self.curves[name]
        data["t"].append(t)
        data["y"].append(y)
        plot.setData(list(data["t"]), list(data["y"]))

    def _prune_window(self, current_time):
        """Remove points older than the rolling window for all curves."""
        cutoff = current_time - self.window_seconds
        for name, (plot, data) in self.curves.items():
            # Pop from left while outside window
            while data["t"] and data["t"][0] < cutoff:
                data["t"].popleft()
                data["y"].popleft()
            # Update plot after pruning
            plot.setData(list(data["t"]), list(data["y"]))

    def add_param(self, name):
        """Add a new parameter curve to the plot"""
        if name not in self.curves:
            # Create a new plot item for this parameter
            color_index = len(self.curves) % 10  # Use cycling colors
            colors = ['b', 'r', 'g', 'm', 'c', 'y', 'w', '#FF6B6B', '#4ECDC4', '#45B7D1']
            
            # Use different symbols for each parameter
            symbols = ['o', 's', '^', 'v', 'd', 'p', '*', 'h', 'H', '+']
            symbol_index = len(self.curves) % len(symbols)
            
            pen_color = colors[color_index]
            symbol = symbols[symbol_index]
            
            plot_item = self.plot(pen=pg.mkPen(color=pen_color, width=2), 
                                 symbol=symbol, symbolSize=6, symbolBrush=pen_color, name=name)
            
            # Create data storage with deque for efficient updates
            data = {
                "t": deque(maxlen=1000),  # Keep last 1000 time points
                "y": deque(maxlen=1000)   # Keep last 1000 value points
            }
            
            # Store the plot item and data
            self.curves[name] = (plot_item, data)
            
            # Update legend
            self.addLegend()

    def set_marker(self, t, y):
        """Set instantaneous marker at current time"""
        if self.marker is None:
            # Create marker if it doesn't exist
            self.marker = self.plot([t], [y], pen=None, symbol='o', symbolSize=10, 
                                  symbolBrush='r', name='Current')
        else:
            # Update existing marker
            self.marker.setData([t], [y])

    def clear_plot(self):
        """Clear all curves and markers from the plot"""
        self.clear()
        self.curves.clear()
        self.marker = None
        
    def remove_param(self, name):
        """Remove a parameter curve from the plot"""
        if name in self.curves:
            plot_item, _ = self.curves[name]
            self.removeItem(plot_item)
            del self.curves[name]
            
    def _show_graph_popup(self):
        popup = QDialog(self)
        layout = QVBoxLayout(popup)
        zoom_in = QPushButton("Zoom In")
        zoom_out = QPushButton("Zoom Out")
        export_png = QPushButton("Export PNG")
        layout.addWidget(zoom_in)
        layout.addWidget(zoom_out)
        layout.addWidget(export_png)
        popup.exec_()