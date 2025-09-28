import csv
import struct
from core.models import Parameter

def load_parameters_from_file(filename):
    if filename.endswith('.csv'):
        return load_parameters_from_csv(filename)
    elif filename.endswith('.bin'):
        return load_parameters_from_binary(filename)
    elif filename.endswith('.dat'):
        return load_parameters_from_binary(filename)  # .dat files use same binary format as .bin
    else:
        raise ValueError("Unsupported file type")

def load_parameters_from_csv(filename):
    params = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                waveform_settings = {
                    'type': row['waveform_type'],
                    'frequency': float(row['frequency']),
                    'phase': float(row['phase']),
                    'amplitude': float(row['amplitude']),
                    'offset': float(row['offset_value'])
                }
                param = Parameter(
                    name=row['name'],
                    sl_no=int(row['sl_no']),
                    packet_id=int(row['packet_id']),
                    offset=int(row['offset']),
                    dtype=row['dtype'],
                    enabled=row['enabled'].lower() == 'true',
                    min_val=float(row['min_val']),
                    max_val=float(row['max_val']),
                    samples_per_500ms=int(row['samples_per_500ms']),
                    full_sweep=row['full_sweep'].lower() == 'true',
                    waveform_settings=waveform_settings
                )
                params.append(param)
            except KeyError as e:
                print(f"Missing field in CSV: {e}")
            except ValueError as e:
                print(f"Invalid value in CSV: {e}")
    return params

def load_parameters_from_binary(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    pos = 0
    num_params = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    params = []
    for _ in range(num_params):
        name = data[pos:pos+32].decode('utf-8').rstrip('\0')
        pos += 32
        sl_no = struct.unpack('>i', data[pos:pos+4])[0]
        pos += 4
        packet_id = struct.unpack('>i', data[pos:pos+4])[0]
        pos += 4
        offset = struct.unpack('>i', data[pos:pos+4])[0]
        pos += 4
        dtype = data[pos:pos+4].decode('utf-8').rstrip()
        pos += 4
        enabled = bool(struct.unpack('>B', data[pos:pos+1])[0])
        pos += 1
        min_val = struct.unpack('>f', data[pos:pos+4])[0]
        pos += 4
        max_val = struct.unpack('>f', data[pos:pos+4])[0]
        pos += 4
        samples_per_500ms = struct.unpack('>i', data[pos:pos+4])[0]
        pos += 4
        full_sweep = bool(struct.unpack('>B', data[pos:pos+1])[0])
        pos += 1
        waveform_type = data[pos:pos+16].decode('utf-8').rstrip('\0')
        pos += 16
        frequency = struct.unpack('>d', data[pos:pos+8])[0]
        pos += 8
        phase = struct.unpack('>d', data[pos:pos+8])[0]
        pos += 8
        amplitude = struct.unpack('>d', data[pos:pos+8])[0]
        pos += 8
        offset_value = struct.unpack('>d', data[pos:pos+8])[0]
        pos += 8
        waveform_settings = {
            'type': waveform_type,
            'frequency': frequency,
            'phase': phase,
            'amplitude': amplitude,
            'offset': offset_value
        }
        param = Parameter(name, sl_no, packet_id, offset, dtype, enabled, min_val, max_val, waveform_settings, samples_per_500ms, full_sweep)
        params.append(param)
    return params