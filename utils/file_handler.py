import json
import csv
import struct
from core.parameter import Parameter

class FileHandler:
    def __init__(self):
        self.parameters = []

    # -----------------------
    # Load Parameters from CSV
    # -----------------------
    def load_csv(self, filepath):
        self.parameters = []
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                param = Parameter(
                    name=row["parameter"],
                    packet_id=int(row["packet_id"]),
                    offset=int(row["offset"]),
                    ptype=row["type"]
                )
                self.parameters.append(param)
        return self.parameters

    # -----------------------
    # Load Parameters from Binary
    # -----------------------
    def load_binary_record(self, filepath):
        record_size = 1400 * 10
        with open(filepath, "rb") as f:
            raw = f.read(record_size)

        values = {}
        for param in self.parameters:
            start = (param.packet_id * 1400) + param.offset

            if param.ptype.lower() == "float":
                chunk = raw[start:start+4]
                val = struct.unpack("<f", chunk)[0]
            elif param.ptype.lower() == "bit":
                byte = raw[start]
                val = 1 if byte & 0x01 else 0
            else:
                raise ValueError(f"Unknown type {param.ptype}")

            values[param.name] = val

        return values

    # -----------------------
    # Save Config to JSON
    # -----------------------
    def save_config(self, filepath, simulation_settings):
        config = {
            "simulation_settings": simulation_settings,
            "parameters": [
                {
                    "name": p.name,
                    "packet_id": p.packet_id,
                    "offset": p.offset,
                    "type": p.ptype,
                    "enabled": p.enabled,
                    "min": getattr(p, "min_val", None),
                    "max": getattr(p, "max_val", None),
                }
                for p in self.parameters
            ]
        }
        with open(filepath, "w") as f:
            json.dump(config, f, indent=4)

    # -----------------------
    # Load Config from JSON
    # -----------------------
    def load_config(self, filepath):
        with open(filepath, "r") as f:
            config = json.load(f)

        self.parameters = []
        for p in config["parameters"]:
            param = Parameter(
                name=p["name"],
                packet_id=p["packet_id"],
                offset=p["offset"],
                ptype=p["type"]
            )
            param.enabled = p.get("enabled", False)
            param.min_val = p.get("min", None)
            param.max_val = p.get("max", None)
            self.parameters.append(param)

        return config["simulation_settings"], self.parameters
