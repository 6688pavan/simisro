import argparse
import socket
import struct
import sys
import time
import os
from typing import Optional, Dict, Any, Tuple


def join_multicast(group: str, port: int, iface: Optional[str] = None) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", port))
    except OSError:
        # Windows may require binding to group
        sock.bind((group, port))
    mreq = socket.inet_aton(group) + socket.inet_aton(iface or "0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(1.0)
    return sock


def default_param(packet_length: int, time_field_offset: int) -> Dict[str, Any]:
    """
    Auto-select a parameter location: packet 0, immediately after the timestamp field.
    Assumes float data; for minor cycles, five floats are laid out contiguously.
    """
    return {
        "sl_no": 1,
        "packet_id": 0,
        "offset": 100,  # fixed offset as per requirement
        "dtype": "float",
        "samples_per_500ms": 5,
        "bit_width": 32,
    }


def extract_param_values(record_bytes: bytes, param: Dict[str, Any],
                         packet_length: int) -> Tuple[float, Tuple[float, ...]]:
    """Return (t_value_placeholder, tuple_of_values). For minor cycle, return 5 values."""
    packet_id = int(param.get("packet_id", 0))
    base_offset = int(param.get("offset", 0))
    dtype = param.get("dtype", "float")
    samples = int(param.get("samples_per_500ms", 1) or 1)
    bit_width = int(param.get("bit_width", 8)) if dtype != "float" else 32

    # Absolute start index in the concatenated record
    abs_base = packet_id * packet_length + base_offset

    if dtype == "float":
        if samples == 1:
            value_bytes = record_bytes[abs_base:abs_base + 4]
            if len(value_bytes) < 4:
                return (0.0, (float("nan"),))
            value = struct.unpack('<f', value_bytes)[0]
            return (0.0, (float(value),))
        else:
            vals = []
            for i in range(5):
                o = abs_base + i * 4
                value_bytes = record_bytes[o:o + 4]
                if len(value_bytes) < 4:
                    vals.append(float("nan"))
                else:
                    vals.append(float(struct.unpack('<f', value_bytes)[0]))
            return (0.0, tuple(vals))
    else:
        if samples == 1:
            if bit_width == 8:
                value_bytes = record_bytes[abs_base:abs_base + 1]
                if not value_bytes:
                    return (0.0, (float("nan"),))
                value = value_bytes[0]
            elif bit_width == 16:
                value_bytes = record_bytes[abs_base:abs_base + 2]
                if len(value_bytes) < 2:
                    return (0.0, (float("nan"),))
                value = struct.unpack('<H', value_bytes)[0]
            else:
                value_bytes = record_bytes[abs_base:abs_base + 4]
                if len(value_bytes) < 4:
                    return (0.0, (float("nan"),))
                value = struct.unpack('<I', value_bytes)[0]
            return (0.0, (float(value),))
        else:
            # Minor cycle digital: 5 x uint64; return low 8 bits of each
            vals = []
            for i in range(5):
                o = abs_base + i * 8
                value_bytes = record_bytes[o:o + 8]
                if len(value_bytes) < 8:
                    vals.append(float("nan"))
                else:
                    u64 = struct.unpack('<Q', value_bytes)[0]
                    vals.append(float(u64 & 0xFF))
            return (0.0, tuple(vals))


def main():
    parser = argparse.ArgumentParser(description="Multicast listener and logger for Telemetry Simulator")
    parser.add_argument("--group", default="239.0.0.1", help="Multicast group IP")
    parser.add_argument("--port", type=int, default=12345, help="UDP port")
    parser.add_argument("--iface", default=None, help="Local interface IP to join group from")
    parser.add_argument("--out_dat", default="received.dat", help="Output .dat file path (overwrites on start)")
    parser.add_argument("--out_txt", default="param_log.txt", help="Output table file path for parameter (overwrites on start)")
    parser.add_argument("--idle_timeout", type=float, default=5.0, help="Seconds of no packets before auto-stop")
    parser.add_argument("--packet_length", type=int, default=1400, help="Packet length in bytes")
    parser.add_argument("--packets_per_record", type=int, default=10, help="Packets per record")
    parser.add_argument("--time_field_offset", type=int, default=24, help="Absolute time offset in packet 0")
    args = parser.parse_args()

    # Auto-select parameter after timestamp in packet 0 (float, up to 5 samples)
    param = default_param(args.packet_length, args.time_field_offset)

    sock = join_multicast(args.group, args.port, args.iface)
    print(f"Listening on {args.group}:{args.port} ... Ctrl+C to stop")

    packets = []
    last_record_idx = 0

    try:
        # Overwrite any existing output files on each run
        with open(args.out_dat, "wb") as fdat, open(args.out_txt, "w", encoding="utf-8") as ftxt:
            # Write table header if file empty
            if ftxt.tell() == 0:
                header = (
                    f"{'sl.no':>5} | {'time':>8} | {'v0':>8} | {'v1':>8} | {'v2':>8} | {'v3':>8} | {'v4':>8} | {'valid':>6}\n"
                    + "-" * 5 + "+" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 8 + "\n"
                )
                ftxt.write(header)

            last_rx_time = time.time()
            while True:
                try:
                    data, _addr = sock.recvfrom(65535)
                except socket.timeout:
                    if (time.time() - last_rx_time) > args.idle_timeout:
                        print("Idle timeout reached; stopping and saving files.")
                        break
                    else:
                        continue

                # Accumulate packets into records of size packets_per_record
                # Assumes sender emits exactly packet_length-sized UDP payloads, 10 per record
                if len(data) != args.packet_length:
                    # Ignore unexpected packet sizes
                    continue
                last_rx_time = time.time()
                packets.append(data)

                if len(packets) >= args.packets_per_record:
                    # Build record and write to .dat
                    record = b"".join(packets[:args.packets_per_record])
                    fdat.write(record)
                    fdat.flush()

                    # Extract timestamp from packet 0 at time_field_offset (float32 little-endian)
                    t_bytes = packets[0][args.time_field_offset:args.time_field_offset + 4]
                    t_value = struct.unpack('<f', t_bytes)[0] if len(t_bytes) == 4 else 0.0

                    # Extract parameter values at default offset (five floats, duplicating first if missing)
                    _t_off, values = extract_param_values(record, param, args.packet_length)
                    # Ensure 5 values for table
                    vals = list(values)
                    if len(vals) == 1:
                        vals = [vals[0]] * 5
                    elif len(vals) < 5:
                        vals += [vals[-1] if vals else float('nan')] * (5 - len(vals))
                    # Use running record index as sl.no (1-based)
                    sl_no = last_record_idx + 1
                    line = (
                        f"{sl_no:5d} | {t_value:8.3f} | {vals[0]:8.3f} | {vals[1]:8.3f} | {vals[2]:8.3f} | {vals[3]:8.3f} | {vals[4]:8.3f} | {1:6d}\n"
                    )
                    # Write to file and also print to terminal
                    ftxt.write(line)
                    ftxt.flush()
                    print(line.strip())

                    last_record_idx += 1
                    packets = packets[args.packets_per_record:]
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


