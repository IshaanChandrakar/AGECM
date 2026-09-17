"""
State-machine rules: WARNING transition, CRITICAL gated by consensus, and the
FAULT path (strong local anomaly without corroboration must NOT become CRITICAL).
"""

from node.feature_extractor import Features
from node.state_machine import StateMachine, NORMAL, WARNING, CRITICAL, FAULT
from config import THETA_MIN, THETA_CRIT, C_HIGH


def feat(rate, t):
    return Features(t=t, tilt_rate=rate, displacement_velocity=0.0,
                    vibration=0.0, ready=True)


def test_normal_to_warning():
    sm = StateMachine("n")
    # Moderate rate on two consecutive ready samples -> WARNING.
    sm.update(feat(0.05, 1.0))
    sm.update(feat(0.05, 2.0))
    assert sm.state == WARNING


def test_critical_requires_consensus():
    sm = StateMachine("n")
    # Strong local rate but NO consensus (C undefined) -> FAULT, not CRITICAL.
    sm.update(feat(0.20, 1.0), consensus_confidence=None)
    sm.update(feat(0.20, 2.0), consensus_confidence=None)
    assert sm.state == FAULT
    assert sm.state != CRITICAL


def test_critical_with_consensus():
    sm = StateMachine("n")
    # Strong local rate WITH high corroboration -> CRITICAL.
    sm.update(feat(0.20, 1.0), consensus_confidence=C_HIGH)
    sm.update(feat(0.20, 2.0), consensus_confidence=C_HIGH)
    assert sm.state == CRITICAL


def test_fault_not_critical_on_low_consensus():
    sm = StateMachine("n")
    # Strong local anomaly, low corroboration (below C_MED) -> FAULT.
    sm.update(feat(0.20, 1.0), consensus_confidence=0.2)
    sm.update(feat(0.20, 2.0), consensus_confidence=0.2)
    assert sm.state == FAULT
