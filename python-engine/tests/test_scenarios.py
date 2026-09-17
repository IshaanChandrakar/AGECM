"""
Scenario-level behaviour.

T3 — Vibration noise: high vibration on one node must NOT cause CRITICAL.
T4 — Single-node fault: an isolated anomaly reaches FAULT, never CRITICAL.
Plus: gradual subsidence drives at least one node to CRITICAL with corroboration,
and front estimation becomes active.
"""

from logger import EventLogger
from simulation.simulation_engine import SimulationEngine
from node.state_machine import CRITICAL, FAULT


def run(scenario, nodes=6, duration=140.0):
    eng = SimulationEngine(scenario=scenario, node_count=nodes,
                           duration=duration, dt=1.0, seed=1,
                           logger=EventLogger(echo=False))
    return eng.run(), eng


def test_gradual_reaches_critical_and_front_active():
    summary, _ = run("gradual_subsidence", nodes=6, duration=160.0)
    states = summary["final_states"].values()
    assert CRITICAL in states, "gradual subsidence should drive a node CRITICAL"
    assert summary["front_estimate"]["active"] is True


def test_vibration_noise_no_false_critical():
    summary, _ = run("vibration_noise", nodes=6, duration=120.0)
    assert CRITICAL not in summary["final_states"].values()


def test_single_node_fault_is_fault_not_critical():
    summary, eng = run("single_node_fault", nodes=6, duration=120.0)
    states = summary["final_states"]
    assert FAULT in states.values(), "isolated anomaly should reach FAULT"
    assert CRITICAL not in states.values(), "isolated anomaly must not be CRITICAL"


def test_normal_stays_normal():
    summary, _ = run("normal", nodes=6, duration=60.0)
    assert set(summary["final_states"].values()) == {"NORMAL"}
