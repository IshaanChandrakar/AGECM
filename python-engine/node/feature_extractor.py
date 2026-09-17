"""
Feature extraction over an 8-sample window (report design).

Consumes filtered readings and derives the features the state machine needs:
  tilt_rate            dθ/dt   (deg/s)  -- rate of change of filtered tilt angle
  displacement_velocity dd/dt  (mm/s)   -- rate of change of filtered displacement
  vibration            A_vib   (g)      -- latest filtered vibration amplitude

Rates use a first-difference over the feature window (least-squares-free, simple
and explainable): (last - first) / (t_last - t_first).
"""

from collections import deque
from dataclasses import dataclass

from config import FEATURE_WINDOW, MA_WINDOW
from node.filter import MovingAverageFilter


@dataclass
class Features:
    t: float
    tilt_rate: float             # dθ/dt  deg/s
    displacement_velocity: float  # dd/dt  mm/s
    vibration: float             # A_vib  g
    ready: bool                  # True once the window is full


class FeatureExtractor:
    def __init__(self, window=FEATURE_WINDOW, ma_window=MA_WINDOW):
        self.window = window
        self._tilt_ma = MovingAverageFilter(ma_window)
        self._disp_ma = MovingAverageFilter(ma_window)
        self._vib_ma = MovingAverageFilter(ma_window)
        # window buffers of (t, filtered_value)
        self._tilt = deque(maxlen=window)
        self._disp = deque(maxlen=window)
        self._vib = deque(maxlen=window)

    def update(self, reading):
        """Feed one raw SensorReading, return Features."""
        ft = self._tilt_ma.update(reading.tilt_angle)
        fd = self._disp_ma.update(reading.displacement)
        fv = self._vib_ma.update(reading.vibration)

        self._tilt.append((reading.t, ft))
        self._disp.append((reading.t, fd))
        self._vib.append((reading.t, fv))

        ready = len(self._tilt) == self.window
        tilt_rate = self._rate(self._tilt)
        disp_vel = self._rate(self._disp)

        return Features(
            t=reading.t,
            tilt_rate=tilt_rate,
            displacement_velocity=disp_vel,
            vibration=fv,
            ready=ready,
        )

    @staticmethod
    def _rate(buf):
        """First-difference rate over the buffer; 0 if too short / zero dt."""
        if len(buf) < 2:
            return 0.0
        t0, v0 = buf[0]
        t1, v1 = buf[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0
        return (v1 - v0) / dt
