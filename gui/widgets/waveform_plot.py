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
        print(f"DEBUG: WaveformPlotWidget.update_waveform called with {len(params)} parameters")
        print(f"DEBUG: Parameter names: {[p.name for p in params]}")
        print(f"DEBUG: Parameter enabled_in_graph states: {[p.enabled_in_graph for p in params]}")
        processed_count = 0
        marker_set = False  # Track if marker has been set
        for p in params:
            print(f"DEBUG: Processing param {p.name}, enabled_in_graph={p.enabled_in_graph}")
            if p.enabled_in_graph:
                processed_count += 1
                if p.samples_per_500ms == 1:  # Major cycle - single value
                    if p.dtype == "float":
                        # Float major: continuous waveform
                        wf = make_waveform(p.waveform, p.freq, p.phase, p.full_sweep)
                        y = wf.value(current_time, p.min_v, p.max_v)
                        self.update_sample(p.name, current_time, y)
                        if not marker_set:
                            self.set_marker(current_time, y)
                            marker_set = True
                    else:
                        # Bit major: discrete min/max points only
                        wf = make_waveform(p.waveform, p.freq, p.phase, p.full_sweep)
                        analog = wf.value(current_time, p.min_v, p.max_v)
                        threshold = (p.min_v + p.max_v) / 2.0
                        y = p.min_v if analog < threshold else p.max_v
                        self.update_sample(p.name, current_time, y)
                        if not marker_set:
                            self.set_marker(current_time, y)
                            marker_set = True
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
                    
                    # Set marker at the first sample time (only once)
                    if not marker_set:
                        if p.dtype == "float":
                            first_y = wf.value(current_time, p.min_v, p.max_v)
                        else:
                            analog = wf.value(current_time, p.min_v, p.max_v)
                            threshold = (p.min_v + p.max_v) / 2.0
                            first_y = p.min_v if analog < threshold else p.max_v
                        self.set_marker(current_time, first_y)
                        marker_set = True
        print(f"DEBUG: Processed {processed_count} enabled parameters, total curves: {len(self.curves)}")
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
        print(f"DEBUG: add_param called for {name}")
        if name not in self.curves:
            print(f"DEBUG: Creating new curve for {name} (total curves: {len(self.curves)})")
            # Define colors and symbols arrays
            colors = [
                # Basic colors
                'b', 'r', 'g', 'm', 'c', 'y', 'w',
                # Extended colors
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
                '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2',
                '#A9DFBF', '#F9E79F', '#D5DBDB', '#AED6F1', '#A3E4D7',
                # More vibrant colors
                '#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6',
                '#1ABC9C', '#34495E', '#E67E22', '#95A5A6', '#F1C40F',
                '#E91E63', '#00BCD4', '#4CAF50', '#FF9800', '#673AB7',
                '#009688', '#795548', '#607D8B', '#FF5722', '#3F51B5',
                '#8BC34A', '#FFC107', '#9C27B0', '#00BCD4', '#CDDC39',
                '#FFEB3B', '#FF9800', '#2196F3', '#4CAF50', '#FF5722'
            ]
            
            # Use different symbols for each parameter (only most reliable pyqtgraph symbols)
            symbols = [
                'o', 's', 'd', 'p', '+', 'x', 'o', 's', 'd', 'p',
                '+', 'x', 'o', 's', 'd', 'p', '+', 'x', 'o', 's',
                'd', 'p', '+', 'x', 'o', 's', 'd', 'p', '+', 'x',
                'o', 's', 'd', 'p', '+', 'x', 'o', 's', 'd', 'p',
                '+', 'x', 'o', 's', 'd', 'p', '+', 'x', 'o', 's'
            ]
            
            # Create a new plot item for this parameter
            color_index = len(self.curves) % len(colors)  # Use cycling colors
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
        # Clear all plot items
        self.clear()
        
        # Clear the curves dictionary
        self.curves.clear()
        
        # Reset marker
        self.marker = None
        
        # Reset the view to default
        self.enableAutoRange()
        self.autoRange()
        
        # Force a repaint
        self.update()
        
    def remove_param(self, name):
        """Remove a parameter curve from the plot"""
        if name in self.curves:
            plot_item, _ = self.curves[name]
            self.removeItem(plot_item)
            del self.curves[name]
            
    def _show_graph_popup(self):
        popup = QDialog(self)
        popup.setWindowTitle("Graph Options")
        layout = QVBoxLayout(popup)
        
        zoom_in = QPushButton("Zoom In")
        zoom_out = QPushButton("Zoom Out")
        export_png = QPushButton("Export PNG")
        
        layout.addWidget(zoom_in)
        layout.addWidget(zoom_out)
        layout.addWidget(export_png)
        
        # Connect button signals
        zoom_in.clicked.connect(self._zoom_in)
        zoom_out.clicked.connect(self._zoom_out)
        export_png.clicked.connect(self._export_png)
        
        popup.exec_()
    
    def _zoom_in(self):
        """Zoom in on the current view"""
        self.getViewBox().scaleBy((0.5, 0.5))
    
    def _zoom_out(self):
        """Zoom out from the current view"""
        self.getViewBox().scaleBy((2.0, 2.0))
    
    def _export_png(self):
        """Export the current plot as PNG"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Plot as PNG", "waveform_plot.png", "PNG Files (*.png)"
        )
        if filename:
            try:
                # Export the plot widget as PNG
                exporter = pg.exporters.ImageExporter(self.plotItem)
                exporter.export(filename)
                print(f"Plot exported to {filename}")
            except Exception as e:
                print(f"Error exporting plot: {e}")