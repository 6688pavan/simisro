# Telemetry Listener Programs

This directory contains three different telemetry listener programs that can receive and display multicast telemetry data from the telemetry simulator.

## Programs Available

### 1. Simple Command-Line Listener (`simple_listener.py`)
A lightweight command-line tool for quick testing and monitoring.

**Usage:**
```bash
python simple_listener.py [multicast_ip] [port]
```

**Examples:**
```bash
# Use default settings (239.0.0.1:12345)
python simple_listener.py

# Use custom multicast group and port
python simple_listener.py 239.0.0.2 54321
```

**Features:**
- Real-time packet reception
- Basic record parsing (10 packets per record)
- Float value extraction and display
- Simple statistics (packet count, record count)

### 2. Basic GUI Listener (`telemetry_listener.py`)
A PyQt5-based GUI application with basic packet display.

**Usage:**
```bash
python telemetry_listener.py
```

**Features:**
- Graphical user interface
- Real-time packet statistics
- Raw data table display
- Log window for monitoring
- Start/stop controls

### 3. Advanced GUI Listener (`advanced_telemetry_listener.py`)
A comprehensive PyQt5 application with parameter parsing capabilities.

**Usage:**
```bash
python advanced_telemetry_listener.py
```

**Features:**
- Loads parameter definitions from `.dat` files
- Parses actual parameter values (not just raw data)
- Multiple display tabs (Parameter Values, Raw Data, Log)
- Automatic parameter loading from `test_data.dat`
- Manual parameter definition support
- Real-time parameter value display

## How to Use

### Step 1: Start the Telemetry Simulator
1. Run the main telemetry simulator:
   ```bash
   python main.py
   ```

2. Load the test data file:
   - Click "Browse File" and select `test_data.dat`
   - The simulator will load 3 parameters: temperature, pressure, voltage

3. Configure network settings:
   - Set Multicast IP to `239.0.0.1` (default)
   - Set Port to `12345` (default)

4. Start the simulation:
   - Click "Start" to begin transmitting telemetry data

### Step 2: Start a Listener
Choose one of the listener programs:

**For quick testing:**
```bash
python simple_listener.py
```

**For GUI monitoring:**
```bash
python advanced_telemetry_listener.py
```

### Step 3: Monitor the Data
- The listener will start receiving packets immediately
- You'll see real-time updates of parameter values
- The advanced listener will show meaningful parameter names and values

## Network Configuration

### Default Settings
- **Multicast IP:** `239.0.0.1`
- **Port:** `12345`
- **Packet Size:** 1400 bytes
- **Packets per Record:** 10

### Custom Configuration
You can change the multicast group and port in both the simulator and listener:
- Use different multicast groups (239.0.0.1, 239.0.0.2, etc.)
- Use different ports (12345, 54321, etc.)
- Both programs must use the same settings to communicate

## Data Format

### Record Structure
- Each record contains 10 packets
- Each packet is 1400 bytes
- Time field is at offset 24 in each packet
- Parameters are embedded at specific offsets within packets

### Parameter Types
- **Float parameters:** 4-byte IEEE 754 floating point values
- **Digital parameters:** 8, 16, or 32-bit integer values
- **Major cycle:** 1 sample per record
- **Minor cycle:** 5 samples per record (100ms spacing)

## Troubleshooting

### No Data Received
1. Check that both programs are using the same multicast IP and port
2. Ensure the telemetry simulator is running and transmitting
3. Check Windows Firewall settings (may block multicast traffic)
4. Verify network interface supports multicast

### Parameter Values Not Displayed
1. Ensure `test_data.dat` is loaded in the simulator
2. Check that parameters are enabled in the simulator
3. Verify the listener is using the correct parameter definitions

### Performance Issues
1. Reduce transmission rate in the simulator (lower Hz setting)
2. Use the simple listener for better performance
3. Limit the number of parameters being transmitted

## Example Output

### Simple Listener Output:
```
Listening on 239.0.0.1:12345
Press Ctrl+C to stop...
------------------------------------------------------------

--- Record 1 ---
Record Time: 0.000s
Packet 0:
  Offset   4:    20.123456
  Offset   8:    15.789012
Packet 1:
  Offset   0:    -5.456789
```

### Advanced Listener Output:
- Parameter Values tab shows: temperature, pressure, voltage with their actual values
- Raw Data tab shows all float values from all packets
- Log tab shows connection status and errors

## Integration Notes

These listeners are designed to work with the telemetry simulator but can be adapted for other multicast telemetry systems by:
1. Modifying the packet format in the parser
2. Adjusting the parameter definitions
3. Changing the record structure (packets per record, packet size)

The advanced listener can load parameter definitions from `.dat` files, making it easy to adapt to different telemetry formats.
