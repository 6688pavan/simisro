def validate_offset(offset, dtype):
    if dtype == 'float' and offset % 4 != 0:
        raise ValueError("Float offset must be 4-byte aligned")
    if offset < 0:
        raise ValueError("Offset must be non-negative")