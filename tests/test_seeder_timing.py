import time
import pytest
from core.models import Parameter, ParameterList, RecordSpec
from core.seeder import SeedingEngine

class DummySignals:
    def __init__(self):
        self.events = []
    def sample_generated(self, name, t, value):
        # mimic a Qt signal's emit by a normal method
        self.events.append((name, t, value))

def test_seeder_timing_major_and_minor():
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
    buf = engine.seed_record(start)

    # inspect collected events from DummySignals
    # We expect P0 sample at start + 0
    # P1 samples at start + 1.0 + [0.0,0.1,0.2,0.3,0.4]
    names = [e[0] for e in signals.events]
    times = [e[1] for e in signals.events]
    p0_times = [t for n,t,v in signals.events if n == 'P0']
    p1_times = [t for n,t,v in signals.events if n == 'P1']

    assert len(p0_times) == 1
    assert abs(p0_times[0] - (start + 0.0)) < 1e-6

    assert len(p1_times) == 5
    expected_p1 = [start + 1.0 + i*0.1 for i in range(5)]
    for got, exp in zip(p1_times, expected_p1):
        assert abs(got - exp) < 1e-6
