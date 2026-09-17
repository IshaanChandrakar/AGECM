# AGECM Packet Format

Simple JSON. One structure (`networking/packet.py`) covers all packet types.

## Packet types

`TELEMETRY` · `CONSENSUS_REQUEST` · `CONSENSUS_REPLY` · `CONTROL` · `ALERT` ·
`FORWARD` · `HEARTBEAT`

## Telemetry packet (engine internal / bridge form, snake_case)

```json
{
  "packet_type": "TELEMETRY",
  "node_id": "node_03",
  "sequence": 102,
  "timestamp": "2026-09-17T10:00:00+00:00",
  "state": "WARNING",
  "tilt_rate": 0.031,
  "displacement_velocity": 0.012,
  "vibration": 0.18,
  "consensus_confidence": 0.75,
  "sampling_interval": 5,
  "spreading_factor": 12,
  "tx_power_dbm": 14,
  "next_hop": "node_02",
  "hop_count": 0,
  "ttl": 3
}
```

`consensus_confidence` may be `null` (undefined — fewer than 2 neighbour replies).

## Backend telemetry payload (REST, camelCase)

`POST /api/telemetry` — the engine converts the packet to the backend contract:

```json
{
  "nodeId": "node_03",
  "timestamp": "2026-09-17T10:00:00+00:00",
  "tiltRate": 0.031,
  "displacementVelocity": 0.012,
  "vibration": 0.18,
  "state": "WARNING",
  "consensusConfidence": 0.75,
  "samplingInterval": 5,
  "spreadingFactor": 12,
  "txPowerDbm": 14,
  "nextHop": "node_02",
  "sequence": 102,
  "hopCount": 0
}
```

## Consensus request / reply (fields)

Request: `node_id`, `sequence`, `timestamp`, `tilt_rate`,
`displacement_velocity`, `vibration`, `state`.
Reply: `node_id` (responder), `request_node_id`, `sequence`, `timestamp`,
`corroborated` (bool), `tilt_rate`.

Confidence: `C = corroborating_replies / replies_received`. Response window 2 s;
fewer than 2 replies ⇒ `C` undefined.

## Networking fields

`hop_count`, `ttl`, `sequence` support two-hop forwarding and duplicate
detection. Radio fields (`spreading_factor`, `tx_power_dbm`) are **simulated**
LoRa configuration values — no SX1276 hardware transmits at these settings.
