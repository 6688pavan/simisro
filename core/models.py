from dataclasses import dataclass, field

@dataclass
class Parameter:
    sl_no: int = 0
    name: str = "param"
    packet_id: int = 0
    offset: int = 0
    dtype: str = "float"  # 'float' or 'bit'
    min_v: float = 0.0
    max_v: float = 1.0
    waveform: str = "Sine"  # Sine, Triangle, Square, Step, Noise
    freq: float = 1.0
    phase: float = 0.0
    full_sweep: bool = True
    samples_per_500ms: int = 1  # 5 for minor cycle, 1 for major
    enabled_in_graph: bool = False
    enabled: bool = True  # For seeding
    start_time: float = None  # Custom seeding window
    end_time: float = None
    fixed_value: float = None  # For major cycle
    bit_width: int = 8  # 8, 16, or 32 for digital parameters

    def to_dict(self):
        return vars(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

class ParameterList:
    def __init__(self):
        self.parameters = []

    def add(self, param):
        self.parameters.append(param)

    def find_by_name(self, name):
        for p in self.parameters:
            if p.name == name:
                return p
        return None

    def enabled_list(self):
        return [p for p in self.parameters if p.enabled]

    def to_dict(self):
        return [p.to_dict() for p in self.parameters]

    @classmethod
    def from_dict(cls, d):
        obj = cls()
        obj.parameters = [Parameter.from_dict(pd) for pd in d]
        return obj

@dataclass
class RecordSpec:
    packet_length: int = 1400
    packets_per_record: int = 10
    timestamp_packet_id: int = 0
    timestamp_offset: int = 24  # 7th float slot (6*4=24)
    timestamp_format: str = '>f'  # big-endian float