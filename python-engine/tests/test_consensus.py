"""
Consensus engine: C = corroborating/received, undefined below MIN_REPLIES.
"""

from consensus.consensus_engine import ConsensusEngine
from node.feature_extractor import Features
from config import THETA_MIN, MIN_REPLIES


def feat(rate):
    return Features(t=0.0, tilt_rate=rate, displacement_velocity=0.0,
                    vibration=0.0, ready=True)


def test_confidence_full_corroboration():
    ce = ConsensusEngine("a")
    neighbours = [("b", feat(0.05)), ("c", feat(0.06))]   # both above θ_min
    c, event = ce.request(1, feat(0.2), "CRITICAL", neighbours, now=0.0)
    assert c == 1.0
    assert event["corroborating"] == 2


def test_confidence_partial():
    ce = ConsensusEngine("a")
    neighbours = [("b", feat(0.05)), ("c", feat(0.0))]    # one corroborates
    c, _ = ce.request(1, feat(0.2), "CRITICAL", neighbours, now=0.0)
    assert c == 0.5


def test_confidence_undefined_below_min_replies():
    ce = ConsensusEngine("a")
    # Only one neighbour reachable (other is silent) -> fewer than MIN_REPLIES.
    neighbours = [("b", feat(0.05)), ("c", None)]
    c, event = ce.request(1, feat(0.2), "CRITICAL", neighbours, now=0.0)
    assert MIN_REPLIES == 2
    assert c is None
    assert event["replies_received"] == 1
