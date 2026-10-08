# Hysteresis Gate

A small, dependency-free change detector with separate rise and fall thresholds. A signal must exceed the upper threshold to turn the gate on, and must drop below the lower threshold to turn it off. While the signal sits in the band between the two thresholds the gate holds its previous state, which is what kills chatter from a noisy input hovering near a single threshold.

## Usage

```python
from hysteresis_gate import HysteresisGate, GateState

gate = HysteresisGate(rise_threshold=10, fall_threshold=5)

gate.update(8)    # GateState.OFF  -- inside the band, stays off
gate.update(11)   # GateState.ON   -- crossed the upper threshold
gate.update(7)    # GateState.ON   -- inside the band, holds on
gate.update(4)    # GateState.OFF  -- crossed the lower threshold

# Force the gate back to a known state without a sample
gate.reset(GateState.OFF)

# Read the current state at any time
print(gate.state)   # GateState.OFF
print(gate.upper)   # 10
print(gate.lower)   # 5
```

Pass the thresholds in either order; the constructor normalizes them so `upper` is always the larger and `lower` the smaller. The initial state defaults to `OFF` and is **not** inferred from the first sample — the caller states it, and the first threshold crossing after that changes it. Both edges use strict inequality (`>` for rise, `<` for fall), so a value sitting exactly on a threshold is treated as "still in the band".

## Why this exists

The problem is single-threshold change detection on a noisy signal: if you fire whenever the value crosses `T`, a value dithering around `T` produces a burst of on/off transitions. Splitting the crossing into a higher rise threshold and a lower fall threshold with a dead band between them collapses the dither to at most one transition. The trade-off is a small lag: the detector no longer reacts the instant the signal leaves the threshold, only once it has moved far enough to be a real level change.

## Edge you will hit

Equal thresholds (`rise == fall`) are allowed and collapse the band to zero; the gate then degenerates to a plain strict-threshold detector (`value > T` to go on, `value < T` to go off). `NaN` thresholds and `NaN` sample values raise `ValueError`, because every comparison against `NaN` is `False` and the gate would silently hang in its initial state forever.

## Layout

- `src/hysteresis_gate/__init__.py` exports `HysteresisGate` and `GateState`.
- `src/hysteresis_gate/core.py` holds the implementation.
- Tests run with `PYTHONPATH=src python -m unittest discover -s tests`.
