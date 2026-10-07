"""Core hysteresis gate logic.

A hysteresis gate has two thresholds: a high (rise) threshold and a low
(fall) threshold separated by a band. A signal must cross the high threshold
from below to turn the gate ON, and must cross the low threshold from above
to turn the gate OFF. While the signal stays within the band the gate holds
its current state, which is the whole point: small fluctuations around a
single threshold no longer cause chatter.

Design decisions, stated plainly:

- The gate operates on discrete sample values fed in via ``update``. It does
  not read a stream itself, so the caller controls timing and batching. This
  keeps the object trivially testable and side-effect free.

- ``__init__`` takes the rise and fall thresholds plus the initial state. We
  do NOT infer the initial state from the first sample: doing so would make
  the first output depend on the threshold ordering in a way that surprises
  people. Instead the caller states the starting state, and the first
  threshold crossing after that changes it.

- ``update`` returns the gate state AFTER applying the new sample. Returning
  the new value (rather than mutating and requiring a separate read) matches
  how most callers use it: one sample in, one decision out.

- When ``rise == fall`` the band collapses to zero and the gate degenerates to
  a plain threshold. We allow this because it is well-defined and useful, and
  forbidding it would just push the "equal thresholds" case into caller code.

- ``upper`` is the larger of the two thresholds and ``lower`` is the smaller.
  The constructor accepts them in either order so a caller does not have to
  remember which is which; we normalize internally. A ``ValueError`` is
  raised only when the two thresholds are the same object value but the caller
  also passes an initial state that is already inconsistent — actually, no:
  we raise ``ValueError`` only for NaN thresholds, which make comparison
  meaningless. We deliberately do not raise for equal numeric thresholds.
"""

import math
from enum import Enum


class GateState(Enum):
    """The two output states of the gate."""

    OFF = 0
    ON = 1


class HysteresisGate:
    """A change-detection gate with separate rise and fall thresholds.

    Parameters
    ----------
    rise_threshold:
        Value the input must exceed to turn the gate ON.
    fall_threshold:
        Value the input must drop below to turn the gate OFF.
    initial_state:
        State the gate reports until the first threshold crossing.

    The gate stores ``upper`` and ``lower`` as the sorted pair so callers can
    pass the thresholds in either order without surprise.
    """

    __slots__ = ("_upper", "_lower", "_state")

    def __init__(self, rise_threshold, fall_threshold, initial_state=GateState.OFF):
        if isinstance(rise_threshold, float) and math.isnan(rise_threshold):
            raise ValueError("rise_threshold must not be NaN")
        if isinstance(fall_threshold, float) and math.isnan(fall_threshold):
            raise ValueError("fall_threshold must not be NaN")
        if not isinstance(initial_state, GateState):
            raise TypeError("initial_state must be a GateState")

        # Normalize so _upper >= _lower. This lets callers pass (low, high)
        # or (high, low) interchangeably; the band is what matters.
        if rise_threshold >= fall_threshold:
            self._upper = rise_threshold
            self._lower = fall_threshold
        else:
            self._upper = fall_threshold
            self._lower = rise_threshold

        self._state = initial_state

    @property
    def upper(self):
        """The larger of the two thresholds."""
        return self._upper

    @property
    def lower(self):
        """The smaller of the two thresholds."""
        return self._lower

    @property
    def state(self):
        """Current gate state."""
        return self._state

    def update(self, value):
        """Feed one sample and return the resulting gate state.

        Crossing rules:
        - If OFF and value > upper  -> ON.
        - If ON  and value < lower  -> OFF.
        - Otherwise state is unchanged.

        We use strict inequality on both edges so that a signal exactly on a
        threshold is treated as "still in the band". This is the only choice
        that is symmetric: using >= on the rise and < on the fall would make
        the band asymmetric and surprise users who swap the threshold order.
        """
        if isinstance(value, float) and math.isnan(value):
            raise ValueError("value must not be NaN")

        if self._state is GateState.OFF:
            if value > self._upper:
                self._state = GateState.ON
        else:  # ON
            if value < self._lower:
                self._state = GateState.OFF
        return self._state

    def reset(self, state=GateState.OFF):
        """Force the gate back to a known state without a sample.

        Useful when the input source changes discontinuously (e.g. a sensor
        swap) and the historical band no longer applies.
        """
        if not isinstance(state, GateState):
            raise TypeError("state must be a GateState")
        self._state = state

    def __repr__(self):
        return (
            f"HysteresisGate(upper={self._upper!r}, lower={self._lower!r}, "
            f"state={self._state!r})"
        )
