# Telemetry Data Simulator

A comprehensive real-time telemetry data generation and visualization system designed for testing and validation of data processing pipelines.

## Features

- **Real-time Data Generation**: Generate synthetic telemetry data at configurable rates (1-50 Hz)
- **Multiple Parameter Types**: Support for both analog (float) and digital (bit) parameters
- **Configurable Waveforms**: Sine, Triangle, Square, Step, and Noise patterns
- **Multicast Transmission**: Efficient UDP multicast data distribution
- **Real-time Visualization**: Live plotting of unlimited simultaneous parameters
- **Interactive GUI**: User-friendly interface for parameter management
- **Data Persistence**: Save/load configurations and parameter sets

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ddr4s
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

### Adding Parameters

1. Click "Add Parameter" to create a new parameter
2. Configure the parameter settings:
   - **Name**: Parameter identifier
   - **Type**: Float (analog) or Bit (digital)
   - **Range**: Min/max values
   - **Waveform**: Waveform type and frequency
   - **Timing**: Start/end times
3. Click "OK" to add the parameter

### Running Simulation

1. Configure simulation settings:
   - **Time Range**: Start and end times
   - **Transmission Rate**: Data generation frequency
   - **Network Settings**: Multicast group and port
2. Click "Start" to begin simulation
3. Use "Pause"/"Resume" to control simulation
4. Click "Reset" to stop and clear data

### Visualization

- **Real-time Plotting**: All enabled parameters are displayed simultaneously
- **Interactive Controls**: Zoom, pan, and export capabilities
- **Parameter Management**: Enable/disable parameters in the table
- **Live Statistics**: Current time, records sent, transmission rate

## Project Structure

```
ddr4s/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── TECHNICAL_REPORT.md    # Comprehensive technical documentation
├── core/                  # Core functionality
│   ├── models.py          # Data models and structures
│   ├── seeder.py          # Data generation engine
│   ├── loader.py          # Data loading utilities
│   ├── waveform.py        # Waveform generation
│   ├── packet_buffer.py   # Packet management
│   └── multicast_sender.py # Network transmission
├── gui/                   # User interface
│   ├── main_window.py     # Main application window
│   ├── parameter_editor.py # Parameter configuration dialog
│   └── widgets/           # UI components
│       ├── waveform_plot.py    # Real-time plotting
│       ├── param_table.py      # Parameter management table
│       └── log_view.py         # Logging display
├── threads/               # Threading components
│   ├── seeder_thread.py   # Data generation thread
│   ├── sender_thread.py   # Network transmission thread
│   └── worker_signals.py  # Thread communication
└── utils/                 # Utility functions
    ├── config.py          # Configuration management
    ├── validators.py      # Input validation
    ├── file_handler.py    # File operations
    ├── io_helpers.py      # I/O utilities
    ├── json_helpers.py    # JSON processing
    └── time_utils.py      # Time utilities
```

## Configuration

### Parameter Settings

- **Name**: Unique identifier for the parameter
- **Packet ID**: Network packet identifier (0-9)
- **Offset**: Byte offset within the packet
- **Type**: Data type (float or bit)
- **Range**: Minimum and maximum values
- **Waveform**: Waveform pattern (Sine, Triangle, Square, Step, Noise)
- **Frequency**: Waveform frequency in Hz
- **Phase**: Phase offset in degrees
- **Samples**: Major cycle (1) or Minor cycle (5)
- **Timing**: Start and end times for parameter activation
- **Bit Width**: Bit width for digital parameters (8, 16, 32)

### Network Settings

- **Multicast Group**: IP address for multicast transmission (default: 239.0.0.1)
- **Port**: UDP port number (default: 12345)
- **Transmission Rate**: Data generation frequency (1-50 Hz)

## Technical Details

### Architecture

The system uses a multi-threaded architecture with separate threads for:
- **GUI Thread**: User interface and visualization
- **Seeder Thread**: Data generation and parameter processing
- **Sender Thread**: Network transmission

### Data Format

- **Packet Size**: 1400 bytes per packet
- **Packets per Record**: 10 packets per data record
- **Header Size**: 24 bytes (timestamp, packet ID, sequence)
- **Data Payload**: Configurable parameter data

### Performance

- **Data Generation**: Up to 50 Hz sustained rate
- **Parameter Support**: Unlimited simultaneous parameters
- **Memory Usage**: < 100MB for typical configurations
- **Network Latency**: < 15ms end-to-end

## Troubleshooting

### Common Issues

1. **Symbol Errors**: Ensure only supported PyQtGraph symbols are used
2. **Memory Issues**: Monitor memory usage with many parameters
3. **Network Problems**: Check multicast group and port settings
4. **Performance**: Reduce parameter count or transmission rate if needed

### Performance Tuning

- **Reduce Parameters**: Limit number of active parameters
- **Lower Frequency**: Reduce transmission rate
- **Memory Management**: Enable automatic cleanup
- **Network Optimization**: Use local multicast groups

## Documentation

For detailed technical information, see:
- **TECHNICAL_REPORT.md**: Comprehensive technical documentation
- **Code Comments**: Inline documentation in source files
- **API Reference**: Class and method documentation

## License

This project is developed for educational and research purposes.

## Contributing

This is an internship project. For questions or issues, please contact the development team.

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Author**: [Your Name]  
**Institution**: [Your Institution]