# Cisco Packet Tracer Setup (optional network-simulation layer)

Packet Tracer is used **only** as a network-topology / connectivity simulation.
It is **not** a faithful emulator of ESP32, MPU6050, VL53L0X, or the SX1276 LoRa
radio, and it does **not** perform real LoRa transmission. The AGECM algorithm
runs entirely in the Python engine; Packet Tracer is never a hard dependency.

## Suggested topology

- Multiple end devices (IoT / generic hosts) representing mesh nodes.
- One switch/router representing the local network infrastructure.
- One server representing the gateway / backend host.
- Links connecting nodes → infrastructure → gateway.

This visualises connectivity and the two-hop reporting concept at the network
level. Sensor behaviour and AGECM intelligence stay in Python.

## Integration: local JSON/file bridge (guaranteed path)

Packet Tracer cannot be assumed to reach localhost freely, so the reliable
integration is a file bridge:

```
bridge/
  incoming/    # telemetry JSON for / from the network layer
  outgoing/    # AGECM CONTROL responses
  processed/   # incoming files after handling (dedup)
```

Run the engine in hybrid mode:

```bash
cd python-engine
python main.py --scenario gradual_subsidence --nodes 6 --mode packet_tracer
```

The engine writes one JSON file per telemetry packet into `bridge/incoming/`
(e.g. `node_01_1.json`) and CONTROL responses into `bridge/outgoing/` on
escalation. `PacketTracerAdapter.read_incoming()` moves handled files into
`bridge/processed/` and skips any already seen (by `node_id`+`sequence`) so
nothing is processed twice.

If a verified direct Packet Tracer → localhost path exists in your environment,
it can be used instead; the file bridge remains the guaranteed fallback.

## Limitations

- No real hardware, no real LoRa radio, no physical sensor data.
- Radio parameters (SF, Tx power) are simulated software values only.
- Direct Packet Tracer ↔ localhost communication is environment-dependent and
  not assumed. The rest of the system runs fully without Packet Tracer.
