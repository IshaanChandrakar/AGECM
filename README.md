# AGECM — Adaptive Geotechnical Edge-Consensus Mesh

Real-time mine subsidence monitoring and prediction. **College Computer Networks project.**

Software demonstration of an edge-consensus sensor mesh using **simulated sensor data** and **simulated networking**. No physical hardware has been built or tested — the proposed ESP32 / MPU6050 / VL53L0X / SX1276 node is a **hardware proposal only** (see [Hardware proposal vs software](#3-hardware-proposal-vs-software-implementation)).

---

## 1. Project overview

AGECM is a mesh of geotechnical sensor nodes that watch a mine roof/floor for subsidence. Each node:

1. Reads simulated tilt / displacement / vibration sensors.
2. Filters and extracts features at the edge.
3. Runs a 4-state machine (`NORMAL → WARNING → CRITICAL`, plus `FAULT`).
4. Asks neighbours for corroboration (**consensus**) before escalating to `CRITICAL`.
5. Adapts its radio + sampling to its state.
6. Forwards telemetry two hops to a gateway.

A Spring Boot gateway stores everything in PostgreSQL and pushes live updates to a React dashboard over WebSocket. A **linear front-estimation prototype** estimates the direction a subsidence front is moving.

## 2. Architecture

```
   Cisco Packet Tracer            (optional network-simulation layer)
   network simulation
          │  (local JSON/file bridge)
          ▼
   Python AGECM engine            sensors · filter · features · state
   (edge intelligence)            machine · consensus · adaptive radio ·
          │                       two-hop forwarding · front estimate
      REST / JSON
          ▼
   Spring Boot backend            REST API · validation · persistence ·
   (gateway)                      alerts · WebSocket broadcast
          │
      PostgreSQL                  telemetry · nodes · consensus · network ·
          │                       alerts · simulation_runs
      WebSocket
          ▼
   React dashboard                live nodes · alerts · consensus ·
                                  network · front estimate · controls · graphs
```

One Python app, one Spring Boot app, one React app, one database. No microservices.

## 3. Hardware proposal vs software implementation

| Proposed hardware (NOT built)      | Software model (this repo)                        |
|------------------------------------|---------------------------------------------------|
| ESP32-WROOM-32 node MCU            | `node/` Python modules per simulated node         |
| MPU6050 IMU                        | `sensor_simulator.py` tilt angle + tilt rate      |
| VL53L0X ToF                        | `sensor_simulator.py` displacement + velocity     |
| Vibration sensor                   | `sensor_simulator.py` vibration amplitude         |
| SX1276 LoRa radio                  | `adaptive_radio.py` — **simulated** SF / Tx values |
| TP4056 + 18650 power               | not modelled (energy is a design target only)     |

Nothing here transmits over a real radio or reads a real sensor. Interfaces are shaped so a real driver can replace a simulated one later.

## 4. Technology stack

Python 3.11+ · Java 17+ / Spring Boot 3 · React 18 + TypeScript + Vite · PostgreSQL 14+ · Cisco Packet Tracer (optional) · REST/JSON · WebSocket (STOMP). All local, no paid/cloud service.

## 5. Python AGECM engine

`python-engine/` — see [docs/architecture.md](docs/architecture.md). Runs standalone (`PURE_PYTHON_SIMULATION`) or reads/writes the Packet Tracer bridge (`PACKET_TRACER_HYBRID`).

## 6. Spring Boot backend

`backend/` — one application. Controllers, services, JPA repositories, models. STOMP WebSocket at `/ws`.

## 7. PostgreSQL

Tables: `nodes`, `telemetry`, `consensus_events`, `network_events`, `alerts`, `simulation_runs`. JPA auto-creates the schema (`ddl-auto=update`).

## 8. React dashboard

`frontend/` — Vite + TS. Node table, alerts, consensus, network view, front estimate, simulation controls, sensor graphs. Lightweight charts (custom SVG), no heavy UI framework.

## 9. Packet Tracer

Optional network-simulation layer. Represents topology / links / gateway. **Not** a faithful ESP32 or SX1276 emulator — no real LoRa transmission. See [docs/packet-tracer-setup.md](docs/packet-tracer-setup.md).

## 10. Local bridge

`bridge/incoming` `bridge/outgoing` `bridge/processed` — JSON files exchanged with Packet Tracer mode. Guaranteed fallback; the engine runs fine without it.

---

## 11. Installation

```bash
# Python engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

PostgreSQL: create a database `agecm` (see [16](#16-database-structure)). Backend and frontend deps install on first run below.

## 12. Running the Python simulation

```bash
cd python-engine
python main.py --scenario gradual_subsidence --nodes 6
```

Add `--backend http://localhost:8080` to POST telemetry to Spring Boot. Add `--mode packet_tracer` for hybrid mode. Runs fully offline without either.

## 13. Starting Spring Boot

```bash
cd backend
./mvnw spring-boot:run
```

Reads DB config from `src/main/resources/application.properties` (override with env vars `DB_URL`, `DB_USER`, `DB_PASS`).

## 14. Starting React

```bash
cd frontend
npm install
npm run dev
```

Opens on `http://localhost:5173`, proxies `/api` and `/ws` to `localhost:8080`.

## 15. Running Packet Tracer hybrid mode

```bash
cd python-engine
python main.py --scenario gradual_subsidence --nodes 6 --mode packet_tracer
```

Drops per-node JSON in `bridge/incoming/`, reads control replies from `bridge/outgoing/`. See [docs/packet-tracer-setup.md](docs/packet-tracer-setup.md). The rest of the system works whether or not Packet Tracer runs.

## 16. Available scenarios

`normal` · `gradual_subsidence` · `sudden_subsidence` · `vibration_noise` · `single_node_fault` · `multi_node_correlated_event` · `recovery`.

```bash
python main.py --scenario <name> --nodes <n> --duration <sec> --seed <int>
```

## 17. API endpoints

```
POST /api/telemetry            ingest one telemetry packet
GET  /api/nodes                all nodes + latest state
GET  /api/nodes/{id}           one node + recent telemetry
GET  /api/alerts               alerts (active first)
GET  /api/consensus            recent consensus events
GET  /api/network              recent network events / links
GET  /api/front-estimation     latest front estimate
GET  /api/health              liveness
POST /api/simulation/start     record a simulation run start
POST /api/simulation/stop      mark run stopped
POST /api/simulation/reset     clear live tables
WS   /ws  topic /topic/telemetry /topic/alerts   live updates
```

## 18. Database structure

See [16](#16-database-structure) tables above and `docs/architecture.md`. Columns cover node id, timestamp, sensor values, state, consensus confidence, sampling interval, spreading factor, Tx power, next hop, sequence, scenario.

## 19. Testing

Python: `cd python-engine && pytest`. Backend: `cd backend && ./mvnw test`.

Implemented tests: **T1** gradual ramp (filter/features/WARNING), **T3** vibration noise (no false CRITICAL), **T4** single-node fault (FAULT, not CRITICAL).

Deferred (need hardware / real network): **T2** latency, **T5** neighbour removal, **T6** 24-h energy. Not fabricated.

## 20. Known limitations

- Simulated sensors and radio only — no physical validation.
- Dynamic multi-hop routing is **partial**: routes are static/deterministic. Code is shaped for later dynamic selection.
- Packet Tracer cannot emulate ESP32/MPU6050/SX1276 faithfully; it is a network-topology layer only.
- The 40% energy-saving and 50% false-alarm-reduction figures are **design targets, not measured results**.

## 21. Review 3 future work

Hardware procurement / assembly / bench testing · tilt-rig · dynamic multi-hop route selection · cluster-head election · graph-based front prediction · 20–50 node scale evaluation · threshold calibration on real strata · field trial.

---

**No paid or cloud service is required.** Everything runs locally.
