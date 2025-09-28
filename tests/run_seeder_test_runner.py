import sys
import os
# Ensure project root is on path so 'core' package can be imported when running this script directly
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)
from core.models import Parameter, ParameterList, RecordSpec
from core.seeder import SeedingEngine

class DummySignals:
    def __init__(self):
        self.events = []
        class Sig:
            def __init__(self, events):
                self._events = events
            def emit(self, name, t, value):
                self._events.append((name, t, value))
        self.sample_generated = Sig(self.events)

def run_test():
    params = ParameterList()
    # Param 0: major
    p0 = Parameter(name='P0', sl_no=1, packet_id=0, offset=0, dtype='float')
    setattr(p0, 'cycle_type', 'major')
    p0.samples_per_500ms = 1
    params.add(p0)
    # Param 1: minor
    p1 = Parameter(name='P1', sl_no=2, packet_id=0, offset=4, dtype='float')
    setattr(p1, 'cycle_type', 'minor')
    p1.samples_per_500ms = 5
    params.add(p1)

    record_spec = RecordSpec()
    signals = DummySignals()
    engine = SeedingEngine(params, record_spec, signals=signals)

    start = 1000.0
    try:
        _ = engine.seed_record(start)
    except Exception as e:
        print('ERROR: seed_record raised exception:', e)
        return 2

    p0_times = [t for n,t,v in signals.events if n == 'P0']
    p1_times = [t for n,t,v in signals.events if n == 'P1']

    if len(p0_times) != 1:
        print('FAIL: expected 1 sample for P0, got', len(p0_times))
        return 3
    if abs(p0_times[0] - (start + 0.0)) >= 1e-6:
        print('FAIL: P0 time mismatch', p0_times[0], '!=', start + 0.0)
        return 4

    if len(p1_times) != 5:
        print('FAIL: expected 5 samples for P1, got', len(p1_times))
        return 5
    expected_p1 = [start + 1.0 + i*0.1 for i in range(5)]
    for got, exp in zip(p1_times, expected_p1):
        if abs(got - exp) >= 1e-6:
            print('FAIL: P1 time mismatch got', got, 'expected', exp)
            return 6

    print('PASS: seeder timing test')
    return 0

if __name__ == '__main__':
    # Ensure project root is on path
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    exit_code = run_test()
    sys.exit(exit_code)
