# packet-tracer/

Place your Cisco Packet Tracer topology file (`.pkt`) here.

Packet Tracer is an **optional** network-simulation layer for AGECM. It shows
network topology, nodes, links, and a gateway/server at the network level. It
does **not** emulate the proposed ESP32 / MPU6050 / VL53L0X / SX1276 hardware and
does **not** perform real LoRa transmission.

See [../docs/packet-tracer-setup.md](../docs/packet-tracer-setup.md) for the
suggested topology and the local JSON/file bridge integration
(`PACKET_TRACER_HYBRID` mode). The project runs fully without Packet Tracer
(`PURE_PYTHON_SIMULATION`).

Suggested topology to build:

- 6 end devices → 1 switch → 1 router → 1 server (gateway).
- Label devices `node_01 … node_06` and `gateway` to match the engine.
