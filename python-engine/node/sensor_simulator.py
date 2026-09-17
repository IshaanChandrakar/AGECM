"""
Simulated sensors for one AGECM node.

Software models of the PROPOSED hardware sensors. No physical sensor is read.
Each model exposes a `sample(t)` that returns a raw reading with configurable
noise, so a real driver (MPU6050 / VL53L0X / vibration) can replace it later.

  MPU6050  -> tilt angle (deg) and, via the pipeline, tilt rate dθ/dt
  VL53L0X  -> relative displacement (mm) and displacement velocity dd/dt
  vibration-> vibration amplitude A_vib (g, arbitrary units)
"""

import random
from dataclasses import dataclass


@dataclass
class SensorReading:
    """One raw multi-sensor reading at simulated time t (seconds)."""
    t: float
    tilt_angle: float          # deg   (MPU6050)
    displacement: float        # mm    (VL53L0X)
    vibration: float           # g     (vibration sensor)


class SensorSimulator:
    """
    Produces raw readings for one node. Behaviour is driven by a scenario
    profile: callables that return the *true* signal at time t, on top of which
    Gaussian noise is added.
    """

    def __init__(self, node_id, profile, noise=None, seed=None):
        """
        profile: dict with keys 'tilt', 'displacement', 'vibration', each a
                 callable f(t) -> float giving the true signal.
        noise:   dict with the same keys giving the noise std-dev.
        """
        self.node_id = node_id
        self.profile = profile
        self.noise = noise or {"tilt": 0.01, "displacement": 0.05, "vibration": 0.02}
        # Per-node RNG so runs are reproducible and nodes are independent.
        self._rng = random.Random(seed)

    def sample(self, t):
        tilt = self.profile["tilt"](t) + self._rng.gauss(0, self.noise["tilt"])
        disp = self.profile["displacement"](t) + self._rng.gauss(0, self.noise["displacement"])
        vib = self.profile["vibration"](t) + self._rng.gauss(0, self.noise["vibration"])
        # Vibration amplitude is non-negative.
        vib = max(0.0, vib)
        return SensorReading(t=t, tilt_angle=tilt, displacement=disp, vibration=vib)
