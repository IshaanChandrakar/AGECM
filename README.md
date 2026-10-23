# AGECM Revised — actual eight-field ESP32 contract

React/TypeScript/Vite/Tailwind/Recharts frontend, Java 17-target Spring Boot backend, PostgreSQL/Flyway persistence and Python ThingSpeak reader. Two sensing nodes use separate channels; the central display remains a separate, unverified reader. The charcoal/orange visual style and local project images are preserved.

## Confirmed and unresolved hardware details

Read-only inspection on 20 October 2026 independently confirmed both channels map field1–field8 to **Temperature, Humidity, CO max, CH4 max, Distance now, Dev max, Status worst, Fault any**. Both feeds were empty and metadata blank; no local firmware was found. The user then confirmed the ESP32 firmware convention: °C, %RH, ppm, ppm, mm, mm; status 0 OK < 1 WARN < 2 DANGER; fault 0 none / 1 any failure in the window. Samples are every 2 seconds, scheduled uploads every 20 seconds; aggregates reset only after successful upload and failed uploads extend the window. Deviation is maximum absolute change from a fixed 30-reading boot baseline. This is user-provided firmware evidence, not a physical source-code or sensor audit.

The shared contract contains the confirmed semantics. Unknown future codes remain unverified. Latest temperature/humidity/distance snapshots and window maxima/worst/fault fields are explicitly distinguished. Raw distance -1 is retained for traceability while its plotted measurement is unavailable; ambiguous zero distance/deviation during a fault window is annotated. All eight charts use sample time; status/fault use step traces. Maximum values come directly from firmware. Old tilt, vibration, displacement-rate and laboratory-rule features were removed from current processing/UI. Existing legacy database records remain intact and separate from the schema 2.0 API.

## Run the real project with Docker

Requires a running Docker engine. Your private local `.env` already contains the configured channel IDs and Read API keys. Keep it private. Set `AGECM_MODE=LIVE` there for real-channel reads; `DEMO` creates only explicitly labeled simulation records in the local database. Neither mode writes to sensing channels.

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
docker compose up --build -d
```

Open http://127.0.0.1:5173 . To avoid a busy frontend port:

```bash
FRONTEND_PORT=5183 docker compose up --build -d
```

Use `docker compose ps` and `docker compose logs --tail 50 backend processing`. Do not print `docker compose config` with resolved credentials; `docker compose config -q` validates quietly. `docker compose down` stops services while preserving the database volume. Do not use `down -v` or reset the database.

## Native run

Prerequisites: Java 17 or 21, Maven, Node 22.12+, Python 3.10+, PostgreSQL. The existing `agecm_revised` database is retained; Flyway applies migration V2 automatically. Python has no third-party dependencies.

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
./scripts/dev.sh
```

Or in three separate terminals, export local `.env` before each relevant command:

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
set -a; source .env; set +a
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
cd backend
mvn spring-boot:run
```

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
set -a; source .env; set +a
python3 processing/adapter.py
```

```bash
cd /Users/ishaanchandrakar/AGECM_Revised/frontend
npm ci
npm run dev
```

Frontend http://127.0.0.1:5173; native backend http://127.0.0.1:8080. Use `mvn spring-boot:run` without a space after the colon. Choose either native or Docker startup; avoid duplicate services on the same ports. No background preview servers should be needed.

## Configuration and architecture

```text
ESP32 Node 01 -> ThingSpeak channel 1 --+-> Python reader -> Spring Boot -> PostgreSQL
ESP32 Node 02 -> ThingSpeak channel 2 --+                       |
                                      |                REST + STOMP -> React
                                      +-> independent central ESP32 -> display
```

- `.env`: channel IDs/Read API keys, database settings, matching ingestion token and `AGECM_MODE` for both backend/processor. Do not commit it. The example has no real credentials.
- `config/sensor-contract.json`: separate node field maps, unit/aggregation/code conventions, evidence and confirmation flag. No secrets.
- `REPORT_INTERVAL_SECONDS=20`, `CLOUD_POLL_SECONDS=5`, `STALE_SECONDS=65` are configurable timing defaults, not measured hardware cadence. UI polls every 5 seconds.
- `THINGSPEAK_BASE_URL` normally requires HTTPS. HTTP is limited to an explicitly enabled local mock transport.
- Firmware Write API keys are not needed by the website or reader. The developer write utility remains disabled.

Read [hardware integration](docs/hardware-integration.md) for the exact timestamp, schema, cursor, partial-fault and firmware acceptance policies. This guide is also served by the frontend Architecture page.

## Repeatable Docker integration fixture

The isolated fixture uses local mock ThingSpeak channels 100/200 and its own named database volume. It does not read or modify actual sensing channels.

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
FRONTEND_PORT=5183 docker compose -p agecm_contract_v2_checks -f compose.yaml -f compose.mock.yaml up --build -d
python3 scripts/verify_fixture.py
cd frontend
E2E_BASE_URL=http://127.0.0.1:5183 npm run test:e2e
```

The fixture is explicitly labeled LOCAL MOCK in the UI and continuously generates deterministic entries with monotonic timestamp-based IDs, supporting exact comparisons by channel ID, entry ID and timestamp, as well as STOMP updates, restart recovery and browser proxy verification. Stop with the same Compose project/files and `down`, preserving its volume.

## Tests

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
python3 -m unittest discover -s processing/tests -v
JAVA_HOME=$(/usr/libexec/java_home -v 21) mvn -f backend/pom.xml test
cd frontend
npm run build
E2E_BASE_URL=http://127.0.0.1:5183 npm run test:e2e
```

Backend tests use H2 PostgreSQL compatibility databases; the integration fixture uses real PostgreSQL in Docker. Tests include unknown and deliberately reversed fault conventions without treating fixture meanings as actual hardware evidence. See [validation](docs/validation.md) for actual results and outstanding physical acceptance checks.

## API and storage

Read endpoints: `/api/health`, `/api/contract`, `/api/system/status`, `/api/nodes`, `/api/nodes/{id}`, `/api/nodes/{id}/history`, `/api/telemetry/latest`, `/api/telemetry/history`, `/api/alerts`, `/api/alerts/{id}`, `/api/integration/thingspeak/status`.

History accepts `start`, `end`, `nodeId`, `page`, `size` (up to 2,000); source and schema are server-scoped. UI shows up to 1,000 samples per node and discloses that limit. CSV exports fetch a fresh server snapshot of every matching record (independent of the chart limit), with UTC identity/timestamps, all eight measurements, raw distance and quality information. Prepared downloads expire after five minutes.

Protected endpoints require `X-Ingestion-Token`: `POST /api/telemetry`, `POST /api/integration/status`, `GET /api/ingestion/{node}`. Mode/channel mismatches, wrong schema, fractional discrete codes and nonfinite values are rejected. Missing values remain null. STOMP topics `/topic/telemetry`, `/topic/alerts`, `/topic/health` publish after commit; reconnect and REST fallback are supported.

Migration V2 adds new columns, permits absent acquisition/boot/sequence data, retains old columns/rows, ends obsolete active tilt episodes and introduces schema-aware cursors. No destructive reset is used. Alerts depend only on confirmed firmware codes or observable data-health faults. A fresh HTTP response is not proof of fresh sensor data; current readings are marked stale by their sample timestamps.

Physical sensor behavior, gas calibration, actual upload-window behavior, central display functionality and field safety remain separate acceptance work. Empty channels cannot validate the hardware-to-cloud path. No simulated data substitutes for missing LIVE readings.


For missing or outdated readings after a ThingSpeak channel clear, see [recovery and validation](docs/thingspeak-recovery.md). The reader now persists a cloud timestamp alongside its entry ID and preserves earlier observations when IDs are reused. Run `python3 scripts/verify_real_cloud.py` to compare the real cloud feeds with PostgreSQL and the served API without writing to ThingSpeak.


## CSV export and manual AWS deployment

Reload an already-open browser tab once after this frontend update. Each **Export CSV** click then prepares fresh data from PostgreSQL for the selected node/comparison and time range; it does not reuse the chart cache. The UI shows the server cutoff and record count. Nulls remain empty, zeros remain zero, and invalid distance retains its raw sentinel separately. See [CSV validation and real physical evidence](docs/csv-aws-validation.md).

The recommended initial cloud arrangement is EC2/Docker Compose + private RDS PostgreSQL + Caddy HTTPS. Use the separate [production Compose file](compose.production.yaml) and [production environment example](.env.production.example), following the [manual AWS deployment guide](docs/aws-deployment.md). The guide lists required versus optional AWS services, private secrets/networking, backup/restore and rollback steps. No AWS infrastructure is created by these files. Keep using `compose.yaml` for local development; do not merge the production stack into it.
