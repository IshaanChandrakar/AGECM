# CSV export and AWS preparation validation

22 October 2026. Local website: http://localhost:5173. AWS infrastructure was not provisioned or deployed.

## Diagnosis and implementation

The original CSV function serialized React's **cached, displayed chart rows** directly into a Blob. It made no request when clicked, silently inherited the chart's 1,000-row-per-node limit, omitted raw-distance/quality metadata, and always used `agecm-telemetry.csv` as the suggested filename. It had no fresh-query error/loading state. No hardcoded telemetry source was found.

The initial actual browser download contained three real cloud rows: Node 01 entries 18/19 and Node 02 entry 105, around `2026-10-22T13:57Z`. Those matched stored API history at capture time; identical downloads between uploads are not evidence of fabricated data. The hardware subsequently produced newer entries. An already open browser also retained the old frontend bundle until reloaded. The rebuilt frontend now serves its entry HTML with revalidation headers. Reload an existing tab once to load the new code; subsequent exports do not require page reloads.

The new implementation:

- POST `/api/telemetry/exports?hours=1&nodeId=node_01` prepares a fresh database snapshot. Omit `nodeId` for Comparison. Supported ranges are 1, 6, 24 and 168 hours. Source and schema are server-scoped.
- One forward-only JDBC query runs in a read-only REPEATABLE READ transaction, with a 500-row fetch size. It filters sample time and receipt time against the server cutoff and orders by sample time, then database ID. It never paginates a moving result with offsets and never materializes the whole CSV in browser memory.
- The prepared file is immutable; later ingestion cannot change a previous download. A new click prepares another snapshot. The successful response includes count, scope, start/end and download URL. Empty results have no download URL.
- GET of that URL streams the complete file with UTF-8 CSV content type, attachment filename, length, row count and cutoff headers, plus `Cache-Control: no-store`. Files expire after five minutes. Backend restart invalidates outstanding links; prepare a new export.
- Exports contain id, node/source/schema, complete cloud identity, sample/time basis/acquisition/cloud/receipt timestamps, all eight measurements, raw distance, field issues, firmware status text and health. The health column is the stored per-record ingestion quality; current freshness is assessed separately from its timestamps. UTC timestamps are explicit ISO-8601. Null is empty, zero is numeric, and invalid distance remains empty in the valid-distance column while raw -1 is retained separately.
- CSV uses CRLF records, correct quote/comma/newline escaping and a UTF-8 BOM for common spreadsheet applications. Potential spreadsheet formulas in untrusted free text get an apostrophe prefix; numeric measurements are unchanged.
- The browser reports preparing, empty, success and error states. It prevents duplicate clicks and never falls back to cached chart rows on export errors. Snapshot scope/time/count remain visible.
- Capacity is bounded by two concurrent preparations, short-lived artifacts, a 90-second query/transaction timeout and a 128 MiB per-file limit. Capacity/errors are explicit; records are never silently truncated. HTTP proxy timeout accommodates preparation.

## Real physical before/after evidence

Two browser downloads were captured from the same open analytics page without reload:

| Download | Rows | Evidence |
|---|---:|---|
| Before physical arrival | 51 | Actual browser CSV, parsed and compared to PostgreSQL |
| After physical arrival | 52 | Contains new Node 01 observation: channel 3542382, entry 54, cloud time `2026-10-22T14:35:33Z` (20:05:33 IST) |

The added observation matched PostgreSQL, REST and the CSV for all eight fields, timestamps, identity, quality information and raw distance. A separate read-only ThingSpeak single-entry request matched the eight fields. Its actual values were temperature null, humidity null, CO 3.8 ppm, CH4 11 ppm, distance null/raw -1, Dev max 0 mm, status 0 and fault-any 1. Those are genuine firmware values/faults; they were not replaced with plausible measurements. A CSV can be fresh even when a sensor value is unchanged or unavailable.

Repeat the local file comparison:

```bash
python3 scripts/verify_csv_exports.py \
  .runtime/csv-evidence/physical-before.csv \
  .runtime/csv-evidence/physical-after.csv
```

The comparison reads PostgreSQL and ThingSpeak only. The private local CSVs/logs are ignored by Git. Later channel clearing can make a historic cloud single-entry check unavailable; retained local full identities remain distinguishable.

## Completed checks

| Area | Result |
|---|---|
| Python reader/normalizer | 27 tests passed |
| Java integration/configuration/migrations/export | 23 tests passed |
| CSV browser checks | 7 passed, including the real physical before/after arrival and a separately seeded 2,105-row fixture |
| Existing app browser suite | 8 passed against the isolated mock-cloud stack |
| Real-channel recovery/UI suite | 4 passed. A separate physical WebSocket-arrival retry timed out with no new telemetry in its 45-second window; the live browser connection showed WebSocket connected. Actual STOMP update delivery passed against the isolated mock-cloud stack. |
| Total unique automated tests above | **69 passed** |
| Frontend production build | TypeScript and Vite passed |
| Docker | Backend, frontend and reader built and started; Java 17 container runtime; existing LIVE project/port/volume preserved |
| Production config | Standalone Compose interpolation/validation passed with placeholders; production guard tests reject development secrets, DEMO/mock mode, bad origins and unverified DB TLS |
| Production proxy | Nginx syntax passed; isolated internal-only proxy served health and a complete real CSV, and blocked external ingestion/cursor routes with 404 |
| HTTPS gateway | Official Caddy image validated the Caddyfile locally; no public ports/domain/certificates were provisioned |
| Data preservation | All 18,532 pre-change telemetry rows compared as parsed JSON and remained unchanged; full cloud identities have no duplicates |
| Backup/restore | Pre-change custom-format backup restored into a newly created isolated test DB: 18,532 telemetry rows and Flyway version 4 |
| Credentials | Private Read API keys scanned against tracked/new text source with no matches; `.env` remains ignored; no real keys entered frontend code or images |

The first CSV arrival attempt saw no new physical observation within 75 seconds and was reported as unavailable. Later real uploads resumed and the dedicated retry passed (51 → 52). A later separate physical STOMP arrival check had no new telemetry rows during its approximately `15:02:21Z–15:03:11Z` observation interval (confirmed by a receipt-time SQL query), so it is reported as an external-data availability limitation, not a passed arrival test. No synthetic observations were injected into the live database or real channels. The large-row browser fixture uses a separate Compose project, port and PostgreSQL volume; it is not evidence of physical hardware validation.

Fresh-database testing also exposed a bootstrap issue: when the oldest readable entry ID was already greater than one, the reader could stall as if a previously tracked history gap existed. A genuinely fresh cursor now fetches the bounded readable window (up to the cloud API's 8,000-entry maximum), ingests it and records the older-history limitation. Existing cursor/reset gap protections remain intact; no saved live cursor was reset. This matters for a new AWS database and was covered by an added Python regression test.

## Reproduction commands

Use the already-running LIVE application for real CSV/UI checks. Run the fixture suite only against a separately created mock stack, never by overriding the live project's channel configuration.

```bash
python3 -m unittest discover -s processing/tests -v
JAVA_HOME=$(/usr/libexec/java_home -v 21) mvn -q -f backend/pom.xml test
cd frontend
npm run build
E2E_BASE_URL=http://localhost:5173 CSV_FIXTURE_URL=http://localhost:5185 \
  npx playwright test tests/csv-export.spec.ts --grep-invert 'two real downloads'
RUN_PHYSICAL_ARRIVAL=1 E2E_BASE_URL=http://localhost:5173 \
  npx playwright test tests/csv-export.spec.ts --grep 'two real downloads'
E2E_BASE_URL=http://localhost:5185 npx playwright test tests/app.spec.ts
E2E_BASE_URL=http://localhost:5173 \
  npx playwright test tests/cloud-recovery.spec.ts --grep-invert 'new physical telemetry'
```

The large CSV fixture requires the dedicated test stack and its explicit seed. The physical test must observe a later cloud timestamp; it cannot pass solely by changing a filename or replaying an old entry.

## AWS readiness and remaining verification

Production files: `compose.production.yaml`, `.env.production.example`, `deploy/Caddyfile`, `deploy/nginx.production.conf`, `deploy/cloudwatch-agent.json`, the production Spring profile/guards, and `scripts/production_db.py`. The [manual AWS guide](aws-deployment.md) includes service selection, network/SG/IAM/secrets setup, DNS/TLS, private RDS verified TLS, deployment, logging, backups, restore and rollback.

These files prepare the application for the recommended EC2 + private RDS deployment. Actual AWS connectivity, account permissions, CA/hostname validation against your real RDS instance, public DNS/certificate issuance, CloudWatch ingestion/alarms, instance sizing and AWS restore/cutover must still be verified during your manual deployment. The optional production DB helper's RDS execution is not claimed as tested; local backup restore used an isolated test database.

No AWS resources were created, no images published, no firmware changed, no ThingSpeak writes performed, no database reset/volume deletion, and no Git commit/push occurred. The unrelated Nominatim container was left untouched.
