import argparse
import math


def main():
    parser = argparse.ArgumentParser(description="Generate minor-cycle instantaneous values for a sine parameter and write a debug txt.")
    parser.add_argument("--min_v", type=float, default=-10.0, help="Minimum value of sine range")
    parser.add_argument("--max_v", type=float, default=10.0, help="Maximum value of sine range")
    parser.add_argument("--freq", type=float, default=2.307, help="Sine frequency in Hz")
    parser.add_argument("--phase", type=float, default=5.0, help="Phase in radians")
    parser.add_argument("--hz", type=float, default=2.0, help="Transmission records per second")
    parser.add_argument("--duration", type=float, default=100.0, help="Total duration in seconds")
    parser.add_argument("--start_time", type=float, default=0.0, help="Start time (sim time) in seconds")
    parser.add_argument("--out", default="instantaneous_debug.txt", help="Output debug file path")
    args = parser.parse_args()

    dt_record = 1.0 / args.hz if args.hz > 0 else 0.0
    dt_minor = dt_record / 5.0 if dt_record > 0 else 0.0

    def sine_value(t: float) -> float:
        # Map sine [-1,1] to [min_v, max_v]
        norm = math.sin(2 * math.pi * args.freq * t + args.phase)
        return args.min_v + (args.max_v - args.min_v) * (norm + 1.0) / 2.0

    t = args.start_time
    record_idx = 0
    num_records = int(args.duration / dt_record) if dt_record > 0 else 0

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"# Minor-cycle instantaneous values\n")
        f.write(f"# params: min_v={args.min_v}, max_v={args.max_v}, freq={args.freq}, phase={args.phase}, hz={args.hz}, duration={args.duration}, start_time={args.start_time}\n")
        f.write(f"{'rec':>4} | {'t0':>8} {'v0':>8} | {'t1':>8} {'v1':>8} | {'t2':>8} {'v2':>8} | {'t3':>8} {'v3':>8} | {'t4':>8} {'v4':>8}\n")
        for r in range(num_records):
            times = [t + i * dt_minor for i in range(5)]
            values = [sine_value(tt) for tt in times]
            f.write(
                f"{r:4d} | "
                f"{times[0]:8.3f} {values[0]:8.3f} | {times[1]:8.3f} {values[1]:8.3f} | "
                f"{times[2]:8.3f} {values[2]:8.3f} | {times[3]:8.3f} {values[3]:8.3f} | {times[4]:8.3f} {values[4]:8.3f}\n"
            )
            t += dt_record
            record_idx += 1


if __name__ == "__main__":
    main()


