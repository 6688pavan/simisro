#!/usr/bin/env python3
"""
Generate a test .dat file for the telemetry simulator.
Creates a binary file with 10 packets × 1400 bytes per record.
"""

import struct
import random
import os

def generate_test_dat(filename="test_data.dat", num_records=1):
    """
    Generate a test .dat file with embedded parameter definitions.
    The file will contain parameter metadata at the beginning, followed by the binary data.
    
    Args:
        filename: Output filename for the .dat file
        num_records: Number of records to generate (default: 1)
    """
    packet_length = 1400
    packets_per_record = 10
    time_field_offset = 24  # Time field at offset 24 in each packet
    
    # Define parameters that will be embedded in the file
    parameters = [
        {
            "name": "temperature",
            "packet_id": 0,
            "offset": 4,
            "type": "float",
            "min": 20.0,
            "max": 100.0,
            "waveform": "Sine",
            "freq": 0.1,
            "phase": 0.0,
            "samples_per_500ms": 1,
            "enabled": True,
            "bit_width": 8
        },
        {
            "name": "pressure", 
            "packet_id": 0,
            "offset": 8,
            "type": "float",
            "min": 0.0,
            "max": 50.0,
            "waveform": "Triangle",
            "freq": 0.2,
            "phase": 0.0,
            "samples_per_500ms": 5,
            "enabled": True,
            "bit_width": 8
        },
        {
            "name": "voltage",
            "packet_id": 1,
            "offset": 0,
            "type": "float",
            "min": -10.0,
            "max": 10.0,
            "waveform": "Square",
            "freq": 1.0,
            "phase": 0.0,
            "samples_per_500ms": 1,
            "enabled": True,
            "bit_width": 8
        }
    ]
    
    print(f"Generating {num_records} record(s) with {packets_per_record} packets of {packet_length} bytes each...")
    print(f"Embedding {len(parameters)} parameters in the file...")
    
    with open(filename, 'wb') as f:
        # Write parameter count first
        f.write(struct.pack('<I', len(parameters)))
        
        # Write each parameter definition
        for param in parameters:
            # Write parameter name length and name
            name_bytes = param["name"].encode('utf-8')
            f.write(struct.pack('<I', len(name_bytes)))
            f.write(name_bytes)
            
            # Write parameter data
            f.write(struct.pack('<I', param["packet_id"]))
            f.write(struct.pack('<I', param["offset"]))
            f.write(struct.pack('<I', 1 if param["type"] == "float" else 0))  # 1 for float, 0 for bit
            f.write(struct.pack('<f', param["min"]))
            f.write(struct.pack('<f', param["max"]))
            f.write(struct.pack('<f', param["freq"]))
            f.write(struct.pack('<f', param["phase"]))
            f.write(struct.pack('<I', param["samples_per_500ms"]))
            f.write(struct.pack('<I', 1 if param["enabled"] else 0))
            f.write(struct.pack('<I', param.get("bit_width", 8)))  # Add missing bit_width field
        
        # Write separator to mark end of parameters
        f.write(b'END_PARAMS')
        
        # Generate binary data records
        for record_idx in range(num_records):
            print(f"Generating record {record_idx + 1}...")
            
            # Generate each packet in the record
            for packet_id in range(packets_per_record):
                # Create packet data
                packet_data = bytearray(packet_length)
                
                # Fill with some test data
                for i in range(0, packet_length, 4):
                    if i < packet_length - 3:
                        value = random.uniform(-100.0, 100.0)
                        packet_data[i:i+4] = struct.pack('<f', value)
                
                # Set time field at offset 24
                record_time = record_idx * 0.5
                time_bytes = struct.pack('<f', record_time)
                packet_data[time_field_offset:time_field_offset+4] = time_bytes
                
                # Write packet to file
                f.write(packet_data)
    
    print(f"Generated {filename} successfully!")
    print(f"File size: {os.path.getsize(filename)} bytes")
    print(f"Parameters embedded: {[p['name'] for p in parameters]}")

def create_sample_parameters_csv(filename="test_params.csv"):
    """
    Create a sample parameters CSV file to go with the .dat file.
    """
    import csv
    
    parameters = [
        {
            "sl_no": 1,
            "name": "test_param_1",
            "packet_id": 0,
            "offset": 4,
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "waveform": "Sine",
            "freq": 1.0,
            "phase": 0.0,
            "samples_per_500ms": 1,
            "full_sweep": True,
            "start_time": -900.0,
            "end_time": 1200.0,
            "fixed_value": 1.0
        },
        {
            "sl_no": 2,
            "name": "test_param_2", 
            "packet_id": 0,
            "offset": 8,
            "type": "float",
            "min": 0.0,
            "max": 20.0,
            "waveform": "Triangle",
            "freq": 0.5,
            "phase": 0.0,
            "samples_per_500ms": 5,
            "full_sweep": True,
            "start_time": -900.0,
            "end_time": 1200.0,
            "fixed_value": None
        },
        {
            "sl_no": 3,
            "name": "test_param_3",
            "packet_id": 1,
            "offset": 0,
            "type": "float", 
            "min": -50.0,
            "max": 50.0,
            "waveform": "Square",
            "freq": 2.0,
            "phase": 0.0,
            "samples_per_500ms": 1,
            "full_sweep": True,
            "start_time": -900.0,
            "end_time": 1200.0,
            "fixed_value": 0.0
        }
    ]
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = parameters[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parameters)
    
    print(f"Generated {filename} with {len(parameters)} parameters")

if __name__ == "__main__":
    # Generate the .dat file
    generate_test_dat("test_data.dat", num_records=1)
    
    # Generate the parameters CSV
    create_sample_parameters_csv("test_params.csv")
    
    print("\nTest files generated:")
    print("- test_data.dat: Binary data file (1 record, 10 packets × 1400 bytes)")
    print("- test_params.csv: Parameter definitions for testing")
    print("\nYou can now load these files in the telemetry simulator!")
