"""
Simulation scenarios.

Each scenario builds a per-node signal PROFILE: callables tilt(t), displacement(t),
vibration(t) giving the *true* signal (noise is added by SensorSimulator).

Tilt angle profiles are shaped so that dθ/dt (computed downstream) crosses the
report thresholds θ_min=0.02 and θ_crit=0.10 deg/s at demonstrable times. A tilt
angle of  0.5 * k * (t-onset)^2  yields a linearly rising rate  k*(t-onset).

NOTE on time: the simulation advances by a fixed base timestep so the mesh shows
demonstrable dynamics within a short run. The per-state adaptive sampling
intervals (60 s / 5 s / 0.1 s) are reported as telemetry values; they are not
the simulator's wall-clock step. This is a compressed-time software demo.

Scenarios: normal, gradual_subsidence, sudden_subsidence, vibration_noise,
single_node_fault, multi_node_correlated_event, recovery.
"""

SCENARIOS = [
    "normal", "gradual_subsidence", "sudden_subsidence", "vibration_noise",
    "single_node_fault", "multi_node_correlated_event", "recovery",
]


def _flat(v=0.0):
    return lambda t: v


def _ramp(onset, k):
    """Tilt angle giving rate k*(t-onset) after onset; flat before."""
    def f(t):
        dt = t - onset
        return 0.5 * k * dt * dt if dt > 0 else 0.0
    return f


def _step(onset, rate, hold=1.0):
    """Sudden: near-instant tilt rise (large rate over a short hold)."""
    def f(t):
        dt = t - onset
        if dt <= 0:
            return 0.0
        if dt < hold:
            return rate * dt          # steep linear rise -> high dθ/dt
        return rate * hold            # plateau
    return f


def _ramp_then_recover(onset, k, peak_t, plateau_t):
    """Rise (rate k) until peak_t, then plateau (rate ~0) from plateau_t on."""
    peak_angle = 0.5 * k * (peak_t - onset) ** 2

    def f(t):
        dt = t - onset
        if dt <= 0:
            return 0.0
        if t < peak_t:
            return 0.5 * k * dt * dt
        return peak_angle             # plateau -> dθ/dt returns below θ_min
    return f


def build(scenario, node_ids, positions, seed=0):
    """
    Return {node_id: profile_dict}. positions: {node_id: (x, y)} (unused for
    signal shape here but kept so scenarios could be position-driven later).
    """
    n = len(node_ids)
    profiles = {}

    if scenario == "normal":
        for nid in node_ids:
            profiles[nid] = _profile(_flat(), _flat(), _flat(0.05))

    elif scenario == "gradual_subsidence":
        # A front sweeps along the line: each node onsets 8 s after the previous.
        for i, nid in enumerate(node_ids):
            onset = 4.0 + i * 8.0
            profiles[nid] = _profile(_ramp(onset, 0.02), _ramp(onset, 0.01), _flat(0.06))

    elif scenario == "sudden_subsidence":
        for i, nid in enumerate(node_ids):
            onset = 6.0 + i * 3.0
            profiles[nid] = _profile(_step(onset, 0.20, hold=12.0),
                                      _step(onset, 0.10, hold=12.0), _flat(0.08))

    elif scenario == "vibration_noise":
        # One node: high vibration, negligible tilt -> must NOT become CRITICAL.
        target = node_ids[n // 2]
        for nid in node_ids:
            if nid == target:
                profiles[nid] = _profile(_flat(), _flat(), _flat(0.9))
            else:
                profiles[nid] = _profile(_flat(), _flat(), _flat(0.05))

    elif scenario == "single_node_fault":
        # One node ramps hard; neighbours stay flat -> no corroboration -> FAULT.
        target = node_ids[n // 2]
        for nid in node_ids:
            if nid == target:
                profiles[nid] = _profile(_ramp(4.0, 0.03), _ramp(4.0, 0.015), _flat(0.1))
            else:
                profiles[nid] = _profile(_flat(), _flat(), _flat(0.05))

    elif scenario == "multi_node_correlated_event":
        # Several adjacent nodes ramp together -> mutual corroboration.
        onset = 5.0
        for nid in node_ids:
            profiles[nid] = _profile(_ramp(onset, 0.025), _ramp(onset, 0.012), _flat(0.07))

    elif scenario == "recovery":
        # Rise into WARNING/CRITICAL, then plateau so rate falls below θ_min and
        # the 30 s recovery dwell returns the node to NORMAL.
        for nid in node_ids:
            profiles[nid] = _profile(
                _ramp_then_recover(onset=4.0, k=0.03, peak_t=14.0, plateau_t=14.0),
                _flat(), _flat(0.06))

    else:
        raise ValueError(f"unknown scenario: {scenario}")

    return profiles


def _profile(tilt, disp, vib):
    return {"tilt": tilt, "displacement": disp, "vibration": vib}
