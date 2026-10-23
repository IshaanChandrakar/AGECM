# ThingSpeak ingestion recovery — 21 October 2026

## Proven cause

The existing `agecm_revised` Compose project served `http://127.0.0.1:5173` in LIVE mode, using the real HTTPS ThingSpeak endpoint and volume `agecm_revised_agecm-data`. No mock override was active. The running images matched their local tags before this change. The problem was reproduced in the served browser.

The database retained Node 01 entry IDs 1–36, ending at `2026-10-20T19:46:34Z`, and Node 02 IDs 1–31, ending at `2026-10-20T19:40:15Z`. The current cloud feeds reused IDs starting at 1, with **later** timestamps: Node 01 from `19:47:52Z` and Node 02 from `19:47:53Z`. This proves entry-ID reuse consistent with channel clearing; the channel administration action itself was not observed.

The adapter filtered on `entry_id > saved cursor`. All current cloud IDs were below those saved cursors and were silently skipped while polling still reported HEALTHY. The original SQL uniqueness constraint also assumed `(channel_id, entry_id)` could never be reused, which would prevent a correct replay.

Node 02's earlier stored rows genuinely lacked temperature and humidity and reported fault-any 1. Its later cloud observations contain valid temperature/humidity and fault-any 0. Comparing the same numeric ID without its timestamp incorrectly conflates two different observations. Node 01's chart similarly showed its earlier observations.

## Changes

- Migration V4 retains every existing row and replaces cloud uniqueness with `(channel_id, entry_id, cloud_created_at)`. It seeds a durable cloud-time watermark from the stored observations without resetting cursors.
- New ingestion uses the complete cloud identity for duplicate detection. A newer cloud timestamp can advance the cursor to a lower reused ID. Older replays and backfills cannot rewind it.
- The reader detects newer timestamps behind its saved ID and expands the read-only catch-up window to at most 8,000 observations. If even that window omits the start of a detected reset, it reports GAP and does not silently skip the missing range. Only successfully persisted entries update its in-memory watermark. Restart obtains both ID and timestamp from the backend. Existing records are replayed idempotently; no values or timestamps are invented.
- Charts render sample dots, including isolated valid values between nulls or long gaps. A reused-ID boundary breaks the connecting line. The distance empty state explains invalid firmware readings; raw -1 remains available and never enters the valid-distance plot.
- All eight firmware mappings, null/zero handling, status meanings, and window semantics are unchanged.

## Repeatable verification

From the repository root, with the LIVE Compose project running:

```bash
python3 scripts/verify_real_cloud.py
```

This script uses the configured running reader's credentials privately for read-only cloud requests, then compares all eight normalized values, raw distance, and cloud timestamps against PostgreSQL and the served API. It requires paginated extension beyond 2,000 stored cloud observations per node and reports that explicitly.

Regression checks:

```bash
python3 -m unittest discover -s processing/tests -v
JAVA_HOME=$(/usr/libexec/java_home -v 21) mvn -q -f backend/pom.xml test
cd frontend
npm run build
E2E_BASE_URL=http://127.0.0.1:5173 npx playwright test tests/cloud-recovery.spec.ts
```

The Java tests include V3-to-V4 preservation, cursor seeding, reused cloud IDs, duplicate replay, and protection against an older replay rewinding the cursor. Reader tests cover reset recovery, failed delivery, old cloud snapshots and node independence. Browser regression tests keep synthetic partial/isolated samples separate from real-channel comparisons.

## Limitations

A raw distance of -1 is a sensor/out-of-range observation, not a website loss. Dev max 0 does not establish sensor health. Firmware fault codes are displayed as uploaded, even if distance is invalid on the same row; the website does not rewrite them.

Polling success does not imply recent hardware uploads. When neither real cloud channel produces a newer observation, the correct website state remains STALE. Live arrival testing must distinguish automatic website refresh from the arrival of a new physical measurement. No real channel writes or firmware changes were performed.

## Completed validation

- 24 Python tests passed.
- 16 Java tests passed, including preservation and reused-ID cases.
- 10 browser tests passed: five recovery checks (including a new real physical WebSocket event) and five existing outage, partial data, alert, responsive route and ingestion authorization checks. The four non-arrival recovery checks passed again after the final backend restart.
- Frontend TypeScript/Vite production build passed. All affected Docker images were rebuilt. Backend Java 17 runtime, healthy PostgreSQL/backend containers, LIVE mode and port 5173 were verified.
- All 18,265 original database rows were compared as parsed JSON after recovery and remained unchanged. Full cloud identities have no duplicates. Restarted processing loaded the persisted ID/time watermark and continued ingesting. The database volume remained `agecm_revised_agecm-data`; no unrelated container was stopped.
- A new physical Node 01 reading, entry 42 at `2026-10-20T20:21:33Z`, was observed in committed REST history, on the telemetry WebSocket, and in the already open monitoring card without reload.
- Private Read API keys were scanned against tracked/new source and found no matches. No firmware changes, channel writes, database reset, Git commit or push occurred.

The following frozen cloud observations matched all eight fields, raw invalid distance and timestamps in PostgreSQL and the API. Browser checks independently matched monitoring cards, plotted entry/time identities, tooltips, both nodes and their comparison. Times below are UTC (add 05:30 for IST). This is a verification snapshot; later uploads can advance the latest entries.

| Node | Channel / entry | Cloud timestamp UTC | Temp °C | Humidity %RH | CO ppm | CH4 ppm | Distance raw → plotted | Dev mm | Status | Fault |
|---|---|---|---|---|---|---|---|---|---|---|
| node_01 | 3542382 / 56 | 2026-10-20T20:26:32Z | 22.6 | 75.0 | 3.9 | 11 | -1 → null | 0 | 0 | 0 |
| node_02 | 3542383 / 14 | 2026-10-20T20:19:33Z | 23.0 | 73.0 | 3.7 | 11 | -1 → null | 0 | 0 | 0 |

Current cloud observations compared: node_01 56, node_02 14. Earlier retained observations with the same numeric IDs have different cloud timestamps and are deliberately preserved. Node 02 may still be STALE when its hardware stops uploading; this is separate from the repaired ingestion defect.
