import csv
import struct
from .parameter import Parameter

class Loader:
    def __init__(self):
        self.parameters = []

    def load_csv(self, filepath):
        """
        Expects CSV header like:
        packet_id,name,type,offset,length,min,max
        """
        params = []
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                param = Parameter(
                    packet_id=int(row["packet_id"]),
                    name=row["name"],
                    p_type=row["type"],
                    offset=int(row["offset"]),
                    length=int(row["length"]),
                    min_val=float(row.get("min", -1)),
                    max_val=float(row.get("max", 1)),
                    enabled=False
                )
                params.append(param)
        self.parameters = params
        return params

    def load_binary(self, filepath, mapping_rules):
        """
        mapping_rules = [
          {"packet_id": 1, "name": "Temp", "type": "int16", "offset": 0, "length": 2, "min":-50, "max":50},
          {"packet_id": 2, "name": "Voltage", "type": "float", "offset": 2, "length": 4, "min":0, "max":5}
        ]
        """
        params = []
        with open(filepath, "rb") as f:
            raw = f.read()

        for rule in mapping_rules:
            offset = rule["offset"]
            length = rule["length"]
            chunk = raw[offset:offset+length]

            if rule["type"] == "int16":
                value = struct.unpack("<h", chunk)[0]
            elif rule["type"] == "uint16":
                value = struct.unpack("<H", chunk)[0]
            elif rule["type"] == "float":
                value = struct.unpack("<f", chunk)[0]
            else:
                value = int.from_bytes(chunk, "little")

            param = Parameter(
                packet_id=rule["packet_id"],
                name=rule["name"],
                p_type=rule["type"],
                offset=offset,
                length=length,
                min_val=rule.get("min", -1),
                max_val=rule.get("max", 1),
                enabled=False
            )
            param.instantaneous_value = value
            params.append(param)

        self.parameters = params
        return params
