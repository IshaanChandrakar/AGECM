"""
AGECM engine configuration.

All design values below come from the AGECM Review 1 & Review 2 report and are
the single source of truth for thresholds, sampling, and adaptive radio values.
These are SIMULATION / design values — no physical hardware was measured.
"""

# ---------------------------------------------------------------------------
# State-machine thresholds (report design values)
# ---------------------------------------------------------------------------
THETA_MIN = 0.02        # deg/s  -- WARNING lower bound for tilt rate dθ/dt
THETA_CRIT = 0.10       # deg/s  -- CRITICAL bound for tilt rate dθ/dt

# Consensus confidence thresholds
C_HIGH = 0.8            # strong corroboration
C_MED = 0.5            # moderate corroboration

# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------
FEATURE_WINDOW = 8      # samples used per feature window
MA_WINDOW = 5          # moving-average filter length

# ---------------------------------------------------------------------------
# Adaptive sampling per state (report values)
#   NORMAL   : 1 sample / 60 s
#   WARNING  : 1 sample / 5 s
#   CRITICAL : 10 Hz  -> 0.1 s interval
# ---------------------------------------------------------------------------
SAMPLING_INTERVAL = {
    "NORMAL": 60.0,
    "WARNING": 5.0,
    "CRITICAL": 0.1,
    "FAULT": 5.0,       # fault reports at the WARNING cadence
}

# Adaptive radio config per state. SIMULATED SX1276 parameters — no real radio.
RADIO_CONFIG = {
    "NORMAL":   {"spreading_factor": 12, "tx_power_dbm": 14, "routing": "neighbour"},
    "WARNING":  {"spreading_factor": 10, "tx_power_dbm": 17, "routing": "cluster"},
    "CRITICAL": {"spreading_factor": 9,  "tx_power_dbm": 20, "routing": "multihop"},
    "FAULT":    {"spreading_factor": 10, "tx_power_dbm": 17, "routing": "cluster"},
}

# ---------------------------------------------------------------------------
# Consensus / recovery timing
# ---------------------------------------------------------------------------
CONSENSUS_WINDOW_S = 2.0     # reply window before C is computed
MIN_REPLIES = 2            # fewer replies -> C undefined (no CRITICAL)
RECOVERY_DWELL_S = 30.0      # below-threshold dwell before returning to NORMAL
CONSECUTIVE_SAMPLES = 2      # two-consecutive-samples rule for escalation

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
DEFAULT_TTL = 3            # supports two-hop forwarding (node -> relay -> gateway)
GATEWAY_ID = "gateway"

# Neighbour corroboration: a neighbour corroborates if its tilt rate also
# exceeds THETA_MIN (i.e. it sees deformation too, not isolated noise).
CORROBORATION_TILT = THETA_MIN

# ---------------------------------------------------------------------------
# Operating modes
# ---------------------------------------------------------------------------
MODE_PURE = "pure_python"
MODE_PACKET_TRACER = "packet_tracer"

# Bridge directories (relative to repo root) for PACKET_TRACER_HYBRID mode.
BRIDGE_INCOMING = "../bridge/incoming"
BRIDGE_OUTGOING = "../bridge/outgoing"
BRIDGE_PROCESSED = "../bridge/processed"
