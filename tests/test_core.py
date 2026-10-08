import math
import unittest

from hysteresis_gate import HysteresisGate, GateState


class TestConstruction(unittest.TestCase):

    def test_default_state_is_off(self):
        gate = HysteresisGate(10, 5)
        self.assertEqual(gate.state, GateState.OFF)

    def test_initial_state_is_respected(self):
        gate = HysteresisGate(10, 5, initial_state=GateState.ON)
        self.assertEqual(gate.state, GateState.ON)

    def test_thresholds_normalized_when_passed_low_first(self):
        gate = HysteresisGate(5, 10)
        self.assertEqual(gate.upper, 10)
        self.assertEqual(gate.lower, 5)

    def test_thresholds_normalized_when_passed_high_first(self):
        gate = HysteresisGate(10, 5)
        self.assertEqual(gate.upper, 10)
        self.assertEqual(gate.lower, 5)

    def test_equal_thresholds_allowed(self):
        gate = HysteresisGate(7, 7)
        self.assertEqual(gate.upper, 7)
        self.assertEqual(gate.lower, 7)

    def test_nan_rise_rejected(self):
        with self.assertRaises(ValueError):
            HysteresisGate(float("nan"), 5)

    def test_nan_fall_rejected(self):
        with self.assertRaises(ValueError):
            HysteresisGate(5, float("nan"))

    def test_bad_initial_state_rejected(self):
        with self.assertRaises(TypeError):
            HysteresisGate(10, 5, initial_state="ON")


class TestRiseAndFall(unittest.TestCase):

    def test_rises_only_above_upper(self):
        gate = HysteresisGate(10, 5)
        self.assertIs(gate.update(8), GateState.OFF)   # in band
        self.assertIs(gate.update(10), GateState.OFF)  # exactly at upper
        self.assertIs(gate.update(10.0001), GateState.ON)  # just over

    def test_falls_only_below_lower(self):
        gate = HysteresisGate(10, 5, initial_state=GateState.ON)
        self.assertIs(gate.update(7), GateState.ON)   # in band
        self.assertIs(gate.update(5), GateState.ON)   # exactly at lower
        self.assertIs(gate.update(4.9999), GateState.OFF)  # just under

    def test_holds_through_band_after_rise(self):
        gate = HysteresisGate(10, 5)
        self.assertIs(gate.update(20), GateState.ON)
        self.assertIs(gate.update(9), GateState.ON)
        self.assertIs(gate.update(6), GateState.ON)
        self.assertIs(gate.update(5), GateState.ON)
        self.assertIs(gate.update(4), GateState.OFF)

    def test_holds_through_band_after_fall(self):
        gate = HysteresisGate(10, 5, initial_state=GateState.ON)
        self.assertIs(gate.update(1), GateState.OFF)
        self.assertIs(gate.update(6), GateState.OFF)
        self.assertIs(gate.update(9), GateState.OFF)
        self.assertIs(gate.update(10), GateState.OFF)
        self.assertIs(gate.update(11), GateState.ON)

    def test_equal_thresholds_degenerate(self):
        gate = HysteresisGate(7, 7)
        self.assertIs(gate.update(7), GateState.OFF)   # not strictly greater
        self.assertIs(gate.update(8), GateState.ON)
        self.assertIs(gate.update(7), GateState.ON)    # not strictly less
        self.assertIs(gate.update(6), GateState.OFF)

    def test_negative_thresholds(self):
        gate = HysteresisGate(-5, -10)
        self.assertEqual(gate.upper, -5)
        self.assertEqual(gate.lower, -10)
        self.assertIs(gate.update(-6), GateState.OFF)
        self.assertIs(gate.update(-4), GateState.ON)
        self.assertIs(gate.update(-11), GateState.OFF)

    def test_int_and_float_mix(self):
        gate = HysteresisGate(10, 5)
        self.assertIs(gate.update(11.0), GateState.ON)
        self.assertIs(gate.update(4), GateState.OFF)

    def test_update_returns_state_not_other(self):
        gate = HysteresisGate(10, 5)
        result = gate.update(20)
        self.assertIs(result, gate.state)

    def test_nan_value_rejected(self):
        gate = HysteresisGate(10, 5)
        with self.assertRaises(ValueError):
            gate.update(float("nan"))


class TestReset(unittest.TestCase):

    def test_reset_to_off(self):
        gate = HysteresisGate(10, 5, initial_state=GateState.ON)
        gate.reset()
        self.assertIs(gate.state, GateState.OFF)

    def test_reset_to_on(self):
        gate = HysteresisGate(10, 5)
        gate.update(20)  # ON
        gate.reset(GateState.ON)
        self.assertIs(gate.state, GateState.ON)

    def test_reset_bad_type_rejected(self):
        gate = HysteresisGate(10, 5)
        with self.assertRaises(TypeError):
            gate.reset(0)

    def test_reset_then_update_works(self):
        gate = HysteresisGate(10, 5, initial_state=GateState.ON)
        gate.reset(GateState.OFF)
        self.assertIs(gate.update(6), GateState.OFF)
        self.assertIs(gate.update(11), GateState.ON)


class TestRepr(unittest.TestCase):

    def test_repr_contains_thresholds_and_state(self):
        gate = HysteresisGate(10, 5, initial_state=GateState.ON)
        r = repr(gate)
        self.assertIn("upper=10", r)
        self.assertIn("lower=5", r)
        self.assertIn("ON", r)


if __name__ == "__main__":
    unittest.main()
