# AGECM Architecture

Software demonstration of the Adaptive Geotechnical Edge-Consensus Mesh. All
sensors and radios are **simulated**; no physical hardware was built or tested.

## Layers

```
Cisco Packet Tracer (optional) ── network-topology simulation
        │  local JSON/file bridge (bridge/incoming, bridge/outgoing)
        ▼
Python AGECM engine ── edge intelligence
        │  REST/JSON  (POST /api/telemetry, /api/consensus, /api/network, /api/front-estimation)
        ▼
Spring Boot gateway ── validate · persist · alert · broadcast
        │  JPA
        ▼
PostgreSQL ── telemetry, nodes, consensus_events, network_events, alerts,
        │      simulation_runs, front_estimations
        ▼  STOMP WebSocket  /topic/telemetry /topic/alerts /topic/front
React dashboard ── live tables, graphs, controls
```

## Python engine — edge pipeline (per node, per sample)

```
sensor_simulator → filter (moving average) → feature_extractor (dθ/dt, dd/dt, A_vib)
   → threshold check → consensus_engine (request/reply, C = corrob/received)
   → state_machine (NORMAL/WARNING/CRITICAL/FAULT) → adaptive_radio (SF, Tx, sampling)
   → packet → forwarding (two-hop, TTL, dup-detect) → gateway
```

Modules:

| File | Responsibility |
|------|----------------|
| `node/sensor_simulator.py` | simulated MPU6050 / VL53L0X / vibration readings |
| `node/filter.py` | moving-average filter |
| `node/feature_extractor.py` | 8-sample window → tilt rate, disp. velocity, vibration |
| `node/state_machine.py` | 4-state machine, two-consecutive-samples rule, recovery dwell |
| `consensus/consensus_engine.py` | request/reply, confidence C, min-replies rule |
| `networking/adaptive_radio.py` | simulated SF / Tx / sampling per state |
| `networking/routing.py` | neighbour table, static two-hop next hop |
| `networking/forwarding.py` | two-hop forwarding, TTL, duplicate detection |
| `networking/packet_tracer_adapter.py` | local JSON/file bridge (optional) |
| `gateway/front_estimator.py` | linear front-estimation prototype |
| `simulation/scenarios.py` | 7 scenario signal profiles |
| `simulation/simulation_engine.py` | orchestrates the mesh |

## State machine (report design values)

- `θ_min = 0.02 °/s`, `θ_crit = 0.10 °/s`
- `C_high = 0.8`, `C_med = 0.5`
- Sampling: NORMAL 1/60 s · WARNING 1/5 s · CRITICAL 10 Hz
- Recovery dwell: 30 s · two-consecutive-samples escalation rule

Rules: `NORMAL` below θ_min; `WARNING` θ_min ≤ dθ/dt < θ_crit or moderate
evidence; `CRITICAL` dθ/dt ≥ θ_crit **and** sufficient consensus (C ≥ C_med);
`FAULT` when a strong local anomaly is **not** corroborated. Insufficient
neighbour evidence never auto-escalates to CRITICAL.

## Database tables

`nodes` · `telemetry` · `consensus_events` · `network_events` · `alerts` ·
`simulation_runs` · `front_estimations`. JPA creates them (`ddl-auto=update`).

## Operating modes

- **PURE_PYTHON_SIMULATION** — engine only, fully offline. Add `--backend` to stream to Spring Boot.
- **PACKET_TRACER_HYBRID** — `--mode packet_tracer` also writes the file bridge.

## Deferred (Review 3)

Dynamic multi-hop route selection · cluster-head election · graph-based front
prediction · 20–50 node scale · real-strata threshold calibration · all hardware
work. See the README's Review 3 section.
