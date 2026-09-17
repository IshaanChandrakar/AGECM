"""
AGECM JSON packet format.

One small dataclass covers all packet types. Types:
  TELEMETRY, CONSENSUS_REQUEST, CONSENSUS_REPLY, CONTROL, ALERT, FORWARD, HEARTBEAT
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

TELEMETRY = "TELEMETRY"
CONSENSUS_REQUEST = "CONSENSUS_REQUEST"
CONSENSUS_REPLY = "CONSENSUS_REPLY"
CONTROL = "CONTROL"
ALERT = "ALERT"
FORWARD = "FORWARD"
HEARTBEAT = "HEARTBEAT"

PACKET_TYPES = {TELEMETRY, CONSENSUS_REQUEST, CONSENSUS_REPLY, CONTROL, ALERT, FORWARD, HEARTBEAT}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Packet:
    packet_type: str
    node_id: str
    sequence: int
    state: str = "NORMAL"
    tilt_rate: float = 0.0
    displacement_velocity: float = 0.0
    vibration: float = 0.0
    consensus_confidence: float = None      # may be None (undefined)
    sampling_interval: float = 60.0
    spreading_factor: int = 12
    tx_power_dbm: int = 14
    next_hop: str = None
    hop_count: int = 0
    ttl: int = 3
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self):
        return asdict(self)

    def to_backend_payload(self):
        """camelCase payload matching the Spring Boot /api/telemetry contract."""
        return {
            "nodeId": self.node_id,
            "timestamp": self.timestamp,
            "tiltRate": self.tilt_rate,
            "displacementVelocity": self.displacement_velocity,
            "vibration": self.vibration,
            "state": self.state,
            "consensusConfidence": self.consensus_confidence,
            "samplingInterval": self.sampling_interval,
            "spreadingFactor": self.spreading_factor,
            "txPowerDbm": self.tx_power_dbm,
            "nextHop": self.next_hop,
            "sequence": self.sequence,
            "hopCount": self.hop_count,
        }
