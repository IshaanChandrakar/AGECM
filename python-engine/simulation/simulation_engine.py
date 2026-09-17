"""
Simulation engine — orchestrates the AGECM mesh.

Builds a line of nodes, advances simulated time by a fixed base step, and runs
the full edge pipeline per node each step:

    sensor -> filter -> features -> threshold -> consensus -> state -> radio
            -> telemetry packet -> two-hop forwarding -> gateway / alert

Also drives the linear front-estimation prototype from escalation times, and
optionally forwards telemetry to the Spring Boot backend and/or the Packet
Tracer file bridge. Runs fully offline (PURE_PYTHON_SIMULATION) with neither.
"""

from config import (
    THETA_MIN, GATEWAY_ID, DEFAULT_TTL,
    BRIDGE_INCOMING, BRIDGE_OUTGOING, BRIDGE_PROCESSED,
    MODE_PACKET_TRACER,
)
from node.sensor_simulator import SensorSimulator
from node.feature_extractor import FeatureExtractor
from node.state_machine import StateMachine, NORMAL, WARNING, CRITICAL, FAULT
from consensus.consensus_engine import ConsensusEngine
from networking.adaptive_radio import AdaptiveRadio
from networking.routing import Router
from networking.forwarding import Forwarder
from networking.packet import Packet, TELEMETRY, ALERT
from networking.packet_tracer_adapter import PacketTracerAdapter
from gateway.front_estimator import FrontEstimator
from simulation import scenarios


class _Node:
    """One simulated AGECM node: the full edge stack in software."""

    def __init__(self, node_id, position, profile, seed, logger):
        self.node_id = node_id
        self.position = position
        self.sensor = SensorSimulator(node_id, profile, seed=seed)
        self.features_ex = FeatureExtractor()
        self.state_machine = StateMachine(node_id, logger=logger)
        self.consensus = ConsensusEngine(node_id, logger=logger)
        self.radio = AdaptiveRadio(node_id)
        self.router = Router(node_id)
        self.forwarder = Forwarder(node_id)
        self.seq = 0
        self.last_features = None
        self.state = NORMAL
        self.escalated_at = None      # first WARNING/CRITICAL time (front est.)


class SimulationEngine:
    def __init__(self, scenario, node_count=6, duration=120.0, dt=1.0,
                 seed=0, logger=None, mode="pure_python",
                 backend_client=None, run_id=None):
        self.scenario = scenario
        self.node_count = node_count
        self.duration = duration
        self.dt = dt
        self.seed = seed
        self.log = logger
        self.mode = mode
        self.backend = backend_client
        self.run_id = run_id

        self.node_ids = [f"node_{i+1:02d}" for i in range(node_count)]
        self.positions = {nid: (i * 10.0, 0.0) for i, nid in enumerate(self.node_ids)}
        profiles = scenarios.build(scenario, self.node_ids, self.positions, seed)

        self.nodes = []
        for i, nid in enumerate(self.node_ids):
            self.nodes.append(_Node(nid, self.positions[nid], profiles[nid],
                                    seed + i, logger))
        self._wire_topology()

        self.front = FrontEstimator(self.positions)
        self.telemetry = []           # collected telemetry dicts
        self.consensus_events = []
        self.network_events = []
        self.alerts = []
        self.front_estimate = {"active": False}

        # Packet Tracer file bridge (optional).
        self.bridge = None
        if mode == MODE_PACKET_TRACER:
            self.bridge = PacketTracerAdapter(
                BRIDGE_INCOMING, BRIDGE_OUTGOING, BRIDGE_PROCESSED, logger=logger)

    def _wire_topology(self):
        """Line topology. Neighbours = adjacent nodes. Static two-hop routes:
        even-index nodes report directly to the gateway; odd-index nodes relay
        through their lower neighbour (node -> relay -> gateway)."""
        by_id = {n.node_id: n for n in self.nodes}
        for i, n in enumerate(self.nodes):
            if i > 0:
                n.router.add_neighbour(self.nodes[i - 1].node_id)
            if i < len(self.nodes) - 1:
                n.router.add_neighbour(self.nodes[i + 1].node_id)
            if i % 2 == 0:
                n.router.set_static_next_hop(GATEWAY_ID)
            else:
                n.router.set_static_next_hop(self.nodes[i - 1].node_id)
        self._by_id = by_id

    # ------------------------------------------------------------------ run
    def run(self):
        t = 0.0
        while t <= self.duration:
            self.step(t)
            t += self.dt
        # Final front estimate from all escalation times.
        self._update_front()
        return self.summary()

    def step(self, t):
        # 1. Sense + extract features for every node first (so consensus can see
        #    each neighbour's current features within the same step).
        for n in self.nodes:
            reading = n.sensor.sample(t)
            n.last_features = n.features_ex.update(reading)

        # 2. Per-node decision + networking.
        for n in self.nodes:
            f = n.last_features
            if not f.ready:
                continue

            # Consensus only when a local anomaly is present.
            c = None
            if f.tilt_rate >= THETA_MIN:
                neighbours = [(nid, self._by_id[nid].last_features)
                              for nid in n.router.neighbour_ids()]
                n.seq += 1
                c, event = n.consensus.request(n.seq, f, n.state, neighbours, t)
                self.consensus_events.append(event)
                if self.backend:
                    self.backend.post_consensus(event, self.run_id)

            prev = n.state
            n.state = n.state_machine.update(f, c)

            # Record first escalation (WARNING/CRITICAL) for front estimation.
            if n.escalated_at is None and n.state in (WARNING, CRITICAL):
                n.escalated_at = t

            # Adaptive radio follows the state.
            n.radio.apply(n.state)
            if prev != n.state and self.log:
                self.log.radio_change(n.node_id, n.radio, t)

            # Build + emit telemetry.
            pkt = self._build_packet(n, f, c, t)
            self._emit(n, pkt, t)

            # Live front estimate as escalations accumulate.
            self._update_front()

    def _build_packet(self, n, f, c, t):
        return Packet(
            packet_type=TELEMETRY,
            node_id=n.node_id,
            sequence=n.seq,
            state=n.state,
            tilt_rate=round(f.tilt_rate, 5),
            displacement_velocity=round(f.displacement_velocity, 5),
            vibration=round(f.vibration, 4),
            consensus_confidence=(None if c is None else round(c, 3)),
            sampling_interval=n.radio.sampling_interval,
            spreading_factor=n.radio.spreading_factor,
            tx_power_dbm=n.radio.tx_power_dbm,
            next_hop=n.router.next_hop(),
            ttl=DEFAULT_TTL,
        )

    def _emit(self, n, pkt, t):
        self.telemetry.append(pkt.to_dict())

        # Two-hop forwarding toward the gateway.
        nxt = n.router.next_hop()
        if nxt != GATEWAY_ID:
            relay = self._by_id[nxt]
            ev = relay.forwarder.forward(pkt, relay.router, self.log, t)
            if ev:
                self.network_events.append(ev)
                if self.backend:
                    self.backend.post_network(ev, self.run_id)
        else:
            self.network_events.append({
                "relay_node": n.node_id, "origin_node": n.node_id,
                "next_hop": GATEWAY_ID, "hop_count": 1, "ttl": pkt.ttl,
                "sequence": pkt.sequence, "delivered": True, "timestamp": t,
            })

        # CRITICAL raises an immediate gateway alert.
        if n.state == CRITICAL:
            alert = {"node_id": n.node_id, "state": CRITICAL,
                     "sequence": pkt.sequence, "timestamp": t}
            self.alerts.append(alert)
            if self.log:
                self.log.alert(n.node_id, CRITICAL, t)

        # Optional integrations.
        if self.backend:
            self.backend.post_telemetry(pkt, self.run_id)
        if self.bridge:
            self.bridge.write_telemetry(pkt)
            if n.state == CRITICAL:
                self.bridge.write_control(n.node_id, pkt.sequence,
                                          {"action": "ESCALATE", "state": CRITICAL})

    def _update_front(self):
        escalations = {n.node_id: n.escalated_at
                       for n in self.nodes if n.escalated_at is not None}
        self.front_estimate = self.front.estimate(escalations)
        if self.backend and self.front_estimate.get("active"):
            self.backend.post_front(self.front_estimate, self.run_id)

    def summary(self):
        states = {n.node_id: n.state for n in self.nodes}
        return {
            "scenario": self.scenario,
            "nodes": self.node_ids,
            "final_states": states,
            "telemetry_count": len(self.telemetry),
            "consensus_events": len(self.consensus_events),
            "network_events": len(self.network_events),
            "alerts": len(self.alerts),
            "front_estimate": self.front_estimate,
        }
