# Actual ESP32 / ThingSpeak sensor contract (schema 2.0)

Read-only inspection on 20 October 2026 independently confirmed these labels on both configured channels. Both feeds were empty and channel metadata was blank at inspection; no firmware was found locally. This confirms field assignment, not units or firmware semantics.

| Field | Node 01 | Node 02 | Unit / semantics |
|---|---|---|---|
| field1 | Temperature | Temperature | °C · latest sample |
| field2 | Humidity | Humidity | %RH · latest sample |
| field3 | CO max | CO max | ppm · maximum in upload window |
| field4 | CH4 max | CH4 max | ppm · maximum in upload window |
| field5 | Distance now | Distance now | mm · latest VL53L0X reading; -1 invalid |
| field6 | Dev max | Dev max | mm · maximum absolute change from boot baseline |
| field7 | Status worst | Status worst | 0 OK < 1 WARN < 2 DANGER · worst in window |
| field8 | Fault any | Fault any | 0 no fault; 1 any failed sample in window |

The user confirmed the firmware semantics on 20 October 2026. The firmware file itself was not present locally, so these details are attributed to that confirmation rather than a source-file audit.

**Window semantics:** samples every 2 seconds, scheduled uploads every 20 seconds, normally about 10 samples. Window aggregates reset only after a valid ThingSpeak entry acknowledgment. Failed uploads extend the window until the next successful upload. Latest temperature/humidity/distance snapshots and window maxima/codes share a row: DANGER can coexist with a normal latest temperature after an earlier spike.

**Deviation:** `abs(distNow - baselineMM)` in mm, maximum across the upload window. Baseline is the average of 30 readings captured once at boot and never adapts. A zero distance/deviation during a fault window can be ambiguous; the app retains zero and annotates it rather than treating it as a missing value or proof of no movement. Raw distance -1 is preserved in `rawDistanceNow`; `distanceNow=null` creates a chart gap and unavailable distance card.

**Status:** 0 OK (all parameters within normal limits), 1 WARN (at least one warning threshold crossed), 2 DANGER (at least one danger threshold crossed). Firmware combines parameter and window levels with maximum. Snapshot values must not be used to recompute or downgrade the uploaded worst status.

| Firmware parameter | WARN ≥ | DANGER ≥ |
|---|---|---|
| Temperature | 35 °C | 40 °C |
| Humidity | 80 %RH | 90 %RH |
| CO | 25 ppm | 50 ppm |
| CH4 | 5000 ppm | 10000 ppm |
| Absolute displacement | 20 mm | 50 mm |

These are confirmed firmware thresholds, not independently validated mine-safety limits. They are documented and exposed as metadata; the website does not reclassify snapshots. CH4 5000 ppm = 0.5% and 10000 ppm = 1% by volume under the firmware's stated convention.

**Fault:** a logical OR since the last successful upload. 0 means no sensor fault in that window; 1 means at least one failed sample. Causes reported by firmware: DHT11 NaN temperature/humidity; MQ-9 `readRs() <= 0` (heater off/disconnected); VL53L0X -1/out-of-range/status 4 or unavailable baseline. A fault flag does not identify which of the valid displayed fields failed historically. Other valid measurements remain visible.

## Shared configuration

`config/sensor-contract.json` is the shared non-secret contract, mounted read-only into backend and processor containers. It has separate per-node field maps. The reader verifies each returned channel ID and its field labels on every poll. A metadata change stops interpretation of that channel until reviewed.

The confirmed metric units, deviation definition, mixed upload window, numeric severity order and fault convention are configured here with `semanticsConfirmed=true`. Firmware thresholds are metadata, not platform classifiers. A future change requires explicit contract review and restarting backend/processor. Unknown codes remain unavailable rather than being treated as healthy. No API keys belong in this JSON.

No platform thresholds, smoothing, tilt rates, derived displacement velocities, consensus confidence or mine-failure prediction rules are applied. Firmware-provided maxima/worst/any values are stored and displayed directly. Numeric zero remains distinct from missing or invalid values. Missing values remain gaps; partial data and window faults are marked without hiding other valid measurements.

## Identity and time

Cloud records require the configured node/channel identity, a positive ThingSpeak `entry_id`, and timezone-aware `created_at`. Deduplication is enforced by `(channel_id,entry_id)`; boot/sequence metadata is optional and is never read from fields 7/8. Those fields are status and fault measurements.

No schema 1.0 JSON `status`, boot ID, sequence, calibration flag, IMU data or feature window is required to read actual feeds. If `status` contains JSON `acquiredAt`, the true acquisition UTC is preserved. Plain-text `status` is also supported. Otherwise `acquiredAt=null`, `sampleAt=cloudCreatedAt`, and `timestampBasis=CLOUD_CREATED_AT`. The UI explicitly labels cloud time. A cloud timestamp is not sensor acquisition time.

Cursor updates occur in the telemetry transaction. Restart recovery reads only the cursor for the active channel and schema. Old schema cursors do not skip new-contract records. Records are sorted chronologically for processing, and older backfilled entries cannot replace newer samples or trigger current alerts. If catch-up exceeds readable history, a visible Gap requires reconciliation. A failed backend delivery does not advance the cursor.

## Credentials and read-only operation

Local values were found in `.env.example` during this update and preserved in ignored, mode-0600 `.env`. The shareable example was sanitized. Do not commit `.env` or paste keys in screenshots. Read API keys are passed only to the server-side reader; write API keys belong only to each ESP32 firmware. The browser receives neither.

Normal reads use `GET https://api.thingspeak.com/channels/<channel>/feeds.json`, the channel Read API key, `results=100`, and `status=true`. A bounded 8,000-entry catch-up is requested only when needed. Requests use HTTPS with timeouts/retries. Keys/credential-bearing URLs are not logged.

No real sensing channel was written to. The developer write utility remains disabled and requires separate explicit authorization and a dedicated test channel. The website does not need Write API keys. Local mocked ThingSpeak tests use a different Docker service, fixture channel IDs and non-secret fixture read keys.

## Firmware work still needed

Confirm the actual firmware build, sensor pin assignments, gas calibration, captured baseline and aggregation behavior on physical hardware. Then publish distinct identifiable entries from each node and compare by channel, entry ID and timestamp through cloud, database, API and UI. Validate sensor-disconnection behavior, partial faults, clock synchronization, stalled publishing, network failures and recovery.

Node 03 remains an independent cloud reader/display with no sensing role. It stays Unverified in the website until an actual heartbeat/status integration exists. No LoRa, offline mesh, battery-life, field-safety or prediction claim follows from this software test.
