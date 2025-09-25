from dataclasses import dataclass, field

@dataclass
class Parameter:
    name: str
    sl_no: int
    packet_id: int
    offset: int
    dtype: str  # 'float' or 'bit'
    enabled: bool = False
    min_val: float = 0.0
    max_val: float = 1.0
    waveform_settings: dict = field(default_factory=dict)
    samples_per_500ms: int = 1
    full_sweep: bool = True

    def to_dict(self):
        return self.__dict__.copy()

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