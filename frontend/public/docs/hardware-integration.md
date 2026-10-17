# AGECM hardware and ThingSpeak integration

This is the **proposed schema 1.0**, not evidence of an already deployed channel or verified physical system. Exactly two ESP32 boards sense, and a third independently reads cloud measurements and drives a display. No physical gateway or active LoRa transport is part of the current build.

## Configure the two private channels

1. Create two private ThingSpeak channels with all eight fields enabled. Associate Channel 1 exclusively with `node_01` and Channel 2 with `node_02`.
2. Copy `.env.example` to `.env`. Configure each channel ID and its Read API key. Keep keys out of Git and browser code. The sensing firmware alone needs the node-specific Write API key.
3. Set `AGECM_MODE=LIVE` for both backend and adapter and restart both. Live mode never starts the demo generator. Do not run two adapter instances against the same channels.
4. Use `FEATURE_OWNER=python` by default. Firmware may leave fields 4/5 empty. If the firmware owns both rates, set `FEATURE_OWNER=firmware`; the adapter consumes the supplied rates without filtering/differentiating again. Numerical agreement needs bench testing.
5. Configure acquisition/report timing and quality semantics in firmware. Default reporting is 30 s, cloud polling 15 s, staleness 95 s and UI polling 5 s. These are independently configurable and do not establish physical measurement latency.

| Field | Meaning | Unit / convention |
|---|---|---|
| field1 | Calibrated tilt angle | degrees, signed axis documented by hardware team |
| field2 | Relative displacement | mm, fixed-target baseline |
| field3 | Vibration proxy | g, defined acceleration summary; not a spectrum |
| field4 | Tilt rate | degrees/s, optional when Python owns features |
| field5 | Displacement velocity | mm/s, optional when Python owns features |
| field6 | Quality flags | integer; 0 valid, bit 0 IMU failure, bit 1 ToF failure, bit 2 not calibrated, bit 3 window not ready; any nonzero flag invalidates this prototype's feature window |
| field7 | Sequence | nonnegative integer, monotonic during a boot |
| field8 | Boot ID | unique string per boot, at most 100 characters |

The `status` field is compact JSON:

```json
{"schema":"1.0","acquiredAt":"2026-10-15T12:00:00Z","uptimeMs":120000,"calibrated":true,"sampleIntervalMs":100,"reportIntervalSeconds":30}
```

Use synchronized UTC acquisition timestamps. The adapter intentionally rejects uptime-only entries because no trusted UTC anchor is available; `uptimeMs` is preserved as supplemental metadata. Never substitute the cloud timestamp for acquisition time. This conservative policy is an implementation decision.

## Write contract: sensing ESP32 to ThingSpeak

```http
POST https://api.thingspeak.com/update.json
Content-Type: application/json

{
  "api_key": "<this node's Write API key>",
  "field1": 1.2, "field2": 0.4, "field3": 0.03,
  "field6": 0, "field7": 100, "field8": "unique-boot-id",
  "status": "{\"schema\":\"1.0\",\"acquiredAt\":\"2026-10-15T12:00:00Z\",\"calibrated\":true,\"sampleIntervalMs\":100,\"reportIntervalSeconds\":30}"
}
```

Validate HTTPS certificates and HTTP status. Require a positive `entry_id` and the expected `channel_id` in the JSON response before recording success. HTTP 200 or a TCP connection alone is insufficient. Retry with bounded backoff and respect the actual account quota. Do not replay ambiguous writes blindly: a lost success response may already have created a cloud entry. Preserve boot/sequence identity so downstream ingestion can deduplicate it. ThingSpeak requires unique timestamps.

The development utility is disabled by default. It must target a **separate test channel**, with explicit `ENABLE_THINGSPEAK_WRITE_TEST=true`, `THINGSPEAK_TEST_CHANNEL_ID`, and `THINGSPEAK_TEST_WRITE_KEY`. Run `python3 processing/write_test.py` once. The website and normal adapter never write synthetic data into sensing channels.

## Read contract and durable ingestion

```http
GET https://api.thingspeak.com/channels/<channel_id>/feeds.json?api_key=<read_key>&results=100&status=true
```

The adapter polls channels independently with bounded timeouts/retries, checks string/null numeric fields, identity, finite ranges, schema and timestamps. It requests a larger catch-up window (maximum 8,000) only if necessary. Larger feeds may be cached by ThingSpeak, so current monitoring stays on small windows.

Cloud identity `(channel_id, entry_id)` and source identity `(node_id, source, boot_id, sequence)` have database uniqueness constraints. A cursor advances in the **same PostgreSQL transaction** as telemetry persistence and is read back after adapter restart. In-memory processing state is rolled back on failed delivery. A detected unrecoverable cloud-history gap stops that channel and records `GAP`; it requires manual review, not silent cursor advancement. Invalid identity/schema similarly stops the channel at the offending entry. Missing sensor values are persisted as invalid measurements rather than converted to zero.

After adapter restart, feature buffers warm up again on subsequent new entries. Historical records remain available; rates and conditions remain unavailable until a new valid window is complete. An older backfilled record cannot replace a newer node snapshot or create a current movement episode. Run one ingestion adapter instance; multi-writer operation is outside this prototype.

## Processing policy

Python applies a five-sample moving average to tilt/displacement, then an eight-point filtered feature window, deriving rates from actual elapsed seconds. Raw calibrated values remain in history. The first derived rate therefore requires 12 valid raw inputs. Missing/invalid data, reboot or a long sampling gap resets readiness. At 30-second reporting cadence, 12 inputs span 330 seconds; firmware-side summaries can reduce that delay but need validation.

`lab-rule-v1` uses **magnitude** tilt rate. Defaults: Warning 0.02 degrees/s and Critical 0.10 degrees/s; 3 consecutive evaluations escalate; 5 recover; recovery thresholds have 30% hysteresis. The state machine begins evaluating after feature readiness; until a qualifying elevated dwell is reached it remains Normal, meaning no confirmed escalation under this rule. Displacement/vibration are observed but do not independently gate this reference rule. No legacy consensus gate or confidence percentage is reused. Thresholds are laboratory settings, not mine safety limits. Invalid/stale/cloud-error data has separate health and yields unavailable current movement status.

## Wiring and hardware verification

Reference classic ESP32 devkit wiring: SDA GPIO21, SCL GPIO22, common ground, appropriate 3.3 V supply. MPU6050 typically 0x68/0x69, VL53L0X typically 0x29. Verify the purchased breakout voltages, pull-ups, addresses and driver compatibility. Secure the IMU to the moving rig and mount the ToF target independently; moving target and sensor together cannot demonstrate displacement. Record mounting axis, signed baseline, stationary noise, calibration and local sampling rate.

Node 03 needs independent Wi-Fi, both Read API credentials, bounded polling and a compatible display driver. The display model is unselected. Its firmware should show node identity, values, units, acquisition age, source and sensor/cloud faults. It receives no laptop-generated classification unless a separate result path is implemented. The website keeps its status **Unverified** because no central heartbeat protocol is integrated.

## Physical acceptance sequence

- Scan I2C addresses and validate both raw sensors separately.
- Calibrate each node; record baseline/noise, movement signs, units and timestamps.
- Confirm distinct channel entries and positive write acknowledgments.
- Trace an entry from ESP32 through cloud, adapter, PostgreSQL and React.
- Compare Python rates with known timed rig movement.
- Test duplicate delivery, rebooted sequence, missing/null values, out-of-order backfill, stalled node, failed cloud read and backend outage.
- Disconnect the laptop and verify Node 03 continues its own cloud reads.
- Verify that failed internet/cloud access ages values and never falsely reports Normal.

## Current and future boundaries

The software demo and mocked cloud tests do not validate physical sensing, mine deployment, LoRa propagation, battery life, certified safety or prediction accuracy. Future LoRa fallback requires three compatible radios, a packet and failover protocol, central local algorithms, buffering/deduplication and representative radio tests. A two-producer/one-receiver radio arrangement is a star; it is not automatically a mesh.

Official API references: [Read Data](https://www.mathworks.com/help/thingspeak/readdata.html), [Write Data](https://www.mathworks.com/help/thingspeak/writedata.html), [Channel Data Control](https://www.mathworks.com/help/thingspeak/channel-control.html). API request/response formats were checked against MathWorks documentation on 15 October 2026; verify subscription-specific limits before physical operation.
