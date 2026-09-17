"""
Consensus message structures (AGECM request/reply mechanism).

A requesting node broadcasts a CONSENSUS_REQUEST to its neighbours carrying its
current anomaly evidence. Each neighbour returns a CONSENSUS_REPLY stating
whether it corroborates (i.e. it also observes deformation).
"""

from dataclasses import dataclass


@dataclass
class ConsensusRequest:
    node_id: str
    sequence: int
    timestamp: float
    tilt_rate: float
    displacement_velocity: float
    vibration: float
    state: str                 # requesting node's anomaly/state indication


@dataclass
class ConsensusReply:
    node_id: str               # responding neighbour
    request_node_id: str       # who asked
    sequence: int              # echoes the request sequence
    timestamp: float
    corroborated: bool         # neighbour also sees deformation
    tilt_rate: float           # neighbour's own tilt rate (evidence)
