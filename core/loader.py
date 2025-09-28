import csv
import struct
from core.models import Parameter

class Loader:
    def load_dat(self, filepath):
        with open(filepath, "rb") as f:
            # Read parameter count
            param_count_bytes = f.read(4)
            if len(param_count_bytes) < 4:
                # Old format file, read as binary data only
                f.seek(0)
                return f.read(1400 * 10)
            
            param_count = struct.unpack('<I', param_count_bytes)[0]
            
            # Read parameters
            parameters = []
            for _ in range(param_count):
                # Read parameter name
                name_len_bytes = f.read(4)
                if len(name_len_bytes) < 4:
                    break
                name_len = struct.unpack('<I', name_len_bytes)[0]
                name_bytes = f.read(name_len)
                name = name_bytes.decode('utf-8')
                
                # Read parameter data
                packet_id = struct.unpack('<I', f.read(4))[0]
                offset = struct.unpack('<I', f.read(4))[0]
                type_flag = struct.unpack('<I', f.read(4))[0]
                dtype = "float" if type_flag == 1 else "bit"
                min_v = struct.unpack('<f', f.read(4))[0]
                max_v = struct.unpack('<f', f.read(4))[0]
                freq = struct.unpack('<f', f.read(4))[0]
                phase = struct.unpack('<f', f.read(4))[0]
                samples_per_500ms = struct.unpack('<I', f.read(4))[0]
                enabled_flag = struct.unpack('<I', f.read(4))[0]
                enabled = enabled_flag == 1
                bit_width = struct.unpack('<I', f.read(4))[0]
                
                param = Parameter(
                    name=name,
                    packet_id=packet_id,
                    offset=offset,
                    dtype=dtype,
                    min_v=min_v,
                    max_v=max_v,
                    waveform="Sine",  # Default waveform
                    freq=freq,
                    phase=phase,
                    samples_per_500ms=samples_per_500ms,
                    enabled=enabled,
                    start_time=-900.0,
                    end_time=1200.0,
                    bit_width=bit_width
                )
                parameters.append(param)
            
            # Read separator
            separator = f.read(10)
            if separator != b'END_PARAMS':
                # Old format file, read as binary data only
                f.seek(0)
                return f.read(1400 * 10), []
            
            # Read binary data
            binary_data = f.read()
            
            return binary_data, parameters

    def load_csv(self, filepath):
        params = []
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                param = Parameter(
                    sl_no=int(row.get("sl_no", 0)),
                    name=row["name"],
                    packet_id=int(row["packet_id"]),
                    dtype=row["type"],
                    offset=int(row["offset"]),
                    min_v=float(row.get("min", -1)),
                    max_v=float(row.get("max", 1)),
                    waveform=row.get("waveform", "Sine"),
                    freq=float(row.get("freq", 1.0)),
                    phase=float(row.get("phase", 0.0)),
                    samples_per_500ms=int(row.get("samples_per_500ms", 1)),
                    full_sweep=bool(row.get("full_sweep", True)),
                    start_time=float(row.get("start_time", -900.0)),
                    end_time=float(row.get("end_time", 1200.0)),
                    fixed_value=float(row.get("fixed_value", 0.0)) if row.get("fixed_value") else None,
                    bit_width=int(row.get("bit_width", 8))
                )
                param.enabled = True
                params.append(param)
        return params