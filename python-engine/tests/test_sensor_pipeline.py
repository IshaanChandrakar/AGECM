"""
T1 — Gradual ramp: filtering + feature extraction + WARNING transition.

Verifies the moving-average filter smooths noise and the feature extractor
produces a rising tilt rate that crosses θ_min.
"""

from config import THETA_MIN, THETA_CRIT, MA_WINDOW
from node.filter import MovingAverageFilter
from node.feature_extractor import FeatureExtractor
from node.sensor_simulator import SensorReading


def test_moving_average_smooths():
    ma = MovingAverageFilter(MA_WINDOW)
    # Alternating noise around 10 should average near 10.
    vals = [9, 11, 9, 11, 9, 11, 9, 11]
    out = [ma.update(v) for v in vals]
    assert abs(out[-1] - 10) < 0.5


def test_feature_rate_rises_and_crosses_theta_min():
    fx = FeatureExtractor()
    # Ramp angle so dθ/dt ≈ 0.05 deg/s (between θ_min and θ_crit).
    dt = 1.0
    rate = 0.05
    last = None
    for i in range(20):
        t = i * dt
        angle = rate * t
        last = fx.update(SensorReading(t=t, tilt_angle=angle,
                                       displacement=0.0, vibration=0.0))
    assert last.ready
    assert THETA_MIN <= last.tilt_rate < THETA_CRIT


def test_feature_flat_is_below_theta_min():
    fx = FeatureExtractor()
    last = None
    for i in range(20):
        last = fx.update(SensorReading(t=i * 1.0, tilt_angle=0.0,
                                       displacement=0.0, vibration=0.0))
    assert last.tilt_rate < THETA_MIN
