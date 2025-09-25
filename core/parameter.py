class Parameter:
    def __init__(self, packet_id, name, p_type, offset, length, 
                 min_val=-1.0, max_val=1.0, enabled=False):
        self.packet_id = packet_id
        self.name = name
        self.type = p_type
        self.offset = offset
        self.length = length
        self.min_val = min_val
        self.max_val = max_val
        self.enabled = enabled
        self.instantaneous_value = 0.0
        self.timestamp = 0.0

    def __repr__(self):
        return (f"<Parameter {self.name} (id={self.packet_id}, "
                f"offset={self.offset}, len={self.length})>")
