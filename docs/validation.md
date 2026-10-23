# Sensor-contract validation — 20 October 2026

## Confirmed evidence

Read-only requests independently confirmed both configured channel label maps: field1 Temperature, field2 Humidity, field3 CO max, field4 CH4 max, field5 Distance now, field6 Dev max, field7 Status worst, field8 Fault any. Channel metadata was blank and both feeds empty. Units, aggregation/window behavior, thresholds, baseline and status/fault conventions were subsequently confirmed directly by the user from ESP32 firmware details. The actual firmware source file was not available locally.

The shared contract uses °C, %RH, ppm, ppm, mm, mm; status 0 OK < 1 WARN < 2 DANGER; fault 0 none / 1 any failed sample in the upload window. Firmware maxima/worst/fault-OR are passed through, not recomputed from latest snapshots. Samples occur every 2 seconds and scheduled uploads every 20 seconds; failed uploads extend the window. These conventions are not independent physical calibration or safety validation.

## Automated checks

| Check | Result |
|---|---|
| Python unittest | 19 passed |
| Java integration/contract/migration tests | 13 passed |
| Playwright with installed Google Chrome | 8 passed |
| TypeScript + Vite production build | Passed |
| Docker Compose builds | Backend, processor and frontend built successfully |
| Docker runtime | PostgreSQL healthy; backend healthy; processor, Nginx proxy, frontend and local ThingSpeak fixture operational |
| Actual Java 17 runtime | Temurin 17.0.20.1 used by the Docker backend |
| Local Java test runtime | Java 21, Java 17 compilation target |
| Credential hygiene | Ignored private .env preserved; no configured API key values found in tracked/new source files |
| Git diff whitespace / Compose validation | Passed |

Python tests cover independent field maps, metadata label/channel checks, zero/null/nonfinite handling, partial values, negative distance sentinel, ambiguous zero with a window fault, unrecognized/fractional codes, mixed-window worst status, direct maxima, timezone conversion, optional acquisition metadata, absent legacy schema/boot/sequence requirements, entry ordering, deduplication, restart cursor recovery, backend failure, empty feeds, authentication failure, timeout redaction and guarded write acknowledgments.

Java tests cover ingestion authentication, exact sensing/central roles, source/schema isolation, finite/discrete validation, zero versus missing, unknown and deliberately reversed test-only binary semantics, confirmed actual firmware codes/units, negative distance preservation, cloud-time fallback, true acquisition time, channel identity, deduplication, out-of-order history, stale/cloud-error health, firmware status/fault episodes and legacy migration retention. A previous concurrent mock-stubbing test failure was removed by using an immutable test-only contract fixture; final tests pass without shared runtime mock mutation.

Browser tests cover all eight time charts, per-node/comparison selection, units, code meanings, real fixture data in cards, exact entry identity in tooltips, CSV export, partial data, unknown semantics, unavailable backend, alert details, all routes, image loading, desktop/mobile layouts, STOMP events and ingestion authentication. Visual review caught auto-generated discrete-axis ticks outside the firmware's codes; axes now explicitly use only 0/1/2 and 0/1. Node 02 uses a dashed trace to remain distinguishable where measurements overlap.

## Identical-entry pipeline comparisons

The isolated `agecm_contract_v2_checks` stack uses a read-only local ThingSpeak service with fixture channels 100 and 200, separate non-secret fixture credentials, an explicitly marked LOCAL MOCK UI and a dedicated PostgreSQL volume. It never contacts actual sensing channels.

`python3 scripts/verify_fixture.py` fetched identifiable cloud entries, queried the same channel/entry IDs in PostgreSQL, and compared API values and timestamps. All eight values matched for both nodes. One recorded comparison used entry 597502451 in both separate channels, cloud timestamp `2026-10-20T14:42:33Z`. Browser tests independently froze actual API responses to compare the same stored record with its monitoring card and matched hovered tooltip entry IDs to API history. New fixture entries were observed reaching both nodes and STOMP subscribers.

## Restart and outage checks

Executed against the isolated fixture stack:

- Stopped mock cloud: both nodes became CLOUD_ERROR, without substituting demo data.
- Restarted mock cloud: new entries resumed from both nodes.
- Restarted the processor: persisted backend cursors recovered.
- Stopped backend: the Nginx API proxy exposed the outage.
- Restarted backend: processing and database-backed monitoring recovered.
- Queried PostgreSQL after recovery: zero duplicate `(channel_id,entry_id)` groups.

## Non-destructive migrations

Flyway migrations V2/V3 preserve old telemetry columns and rows, add the actual measurements and timestamp basis, relax obsolete required metadata, isolate the active schema and retain raw distance sentinels. Obsolete active laboratory-rule episodes are resolved, not deleted.

In addition to the automated H2 migration test, actual V1 SQL was applied to a separate PostgreSQL test database and a legacy row with tilt 3.14 inserted. V2/V3 SQL preserved that row unchanged and accepted a new schema-2.0 cloud row with nullable acquisition/boot/sequence fields and raw distance -1. Both schema versions remained present. No native user database reset, volume deletion or sensing-channel write was performed.

## Real-channel verification and remaining limits

A separate Docker stack, `agecm_live_v2_checks`, used the actual configured private Read API credentials. Both channels polled successfully with cloud status HEALTHY, but their feeds remained empty and latest readings stayed null/NO_DATA. Its PostgreSQL database contained no telemetry rows and no fabricated demo values. This verifies configuration, authenticated read access and honest empty-data behavior, not physical sensor acquisition.

Real entry-to-database/API/UI comparisons could not be completed because neither real channel contained historical or new entries during observation. Remaining acceptance checks: publish known identifiable physical readings from both ESP32s; compare exact channel ID/entry ID/timestamp throughout the system; verify DHT11/MQ-9/VL53L0X fault cases, gas calibration, 30-reading boot baseline, upload retry/window extension, actual clock metadata and independent central display behavior. No mine-safety, prediction, LoRa, range, battery-life or field-reliability claim is made.

Screenshots are retained under `output/preview-v2/`. Test containers are stopped after validation without deleting their database volumes, keeping normal startup ports available. Nothing was committed or pushed to GitHub.


## Real-channel recovery, 21 October 2026

See [ThingSpeak recovery evidence](thingspeak-recovery.md) for the reused-entry-ID diagnosis, preservation migration, exact real-channel comparisons, browser proof and final regression checks. This supersedes the earlier limitation that real channel feeds were empty.


## CSV and AWS preparation, 22 October 2026

See [CSV and AWS validation](csv-aws-validation.md) for the fresh server export, real before/after hardware downloads, current 69-test results, isolated large-export fixture, preserved data and local production-config validation. AWS deployment verification is explicitly separate.
