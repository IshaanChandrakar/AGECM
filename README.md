# AGECM Revised

A fresh local implementation in this folder. React + TypeScript/Vite/Tailwind, Spring Boot 3.3.5 targeting Java 17, PostgreSQL/Flyway, and a standard-library Python ThingSpeak adapter. Five pages: overview, monitoring, analytics, alerts, architecture. Four original generated images are integrated and served locally.

Exactly **two sensing ESP32s** are represented. The third ESP32 is an **independent central reader/display** and remains Unverified. Demonstration data is always labeled and stored as `source=demo`; live ThingSpeak data uses `source=cloud_hardware`. No active LoRa, physical mesh, peer consensus or validated mine-failure prediction is claimed.

## Architecture

```text
ESP32 sensing Node 01 -> ThingSpeak channel 1 --+
ESP32 sensing Node 02 -> ThingSpeak channel 2 --+-> Python adapter -> Spring Boot -> PostgreSQL
                                               |                       |
                                               |                 REST + STOMP -> React
                                               +-> Central ESP32 Node 03 -> independent display
```

The demonstration source replaces only the physical/cloud input, feeding the same normalized backend API. It never writes to ThingSpeak. Spring Boot owns persistence, per-source history, freshness, alert episodes and broadcasts. Python owns validation, filtering, feature derivation and the versioned laboratory movement rule. Mode changes are environment-controlled, with no public UI control of hardware.

## Quick start with Docker

Requires a running Docker engine:

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
cp .env.example .env
docker compose up --build
```

Open http://127.0.0.1:5173 . PostgreSQL and ingestion endpoints stay on the internal Compose network. Docker startup was not executed in this environment because its daemon was not running; the native PostgreSQL workflow below was executed.

## Native development

Prerequisites: Java 17 or 21, Maven 3.9+, Python 3.10+, Node 22.12+ or 24+, PostgreSQL 16/17. The current machine has Java 21 and PostgreSQL 17; compilation uses Java 17 language/bytecode target. There are no Python package dependencies.

Create an isolated local database once (using an administrator PostgreSQL account):

```bash
psql postgres -c "CREATE ROLE agecm_revised LOGIN PASSWORD 'agecm_local';"
createdb -O agecm_revised agecm_revised
```

This database and role were created during implementation. Do not repeat creation if they already exist.

```bash
cd /Users/ishaanchandrakar/AGECM_Revised
cp .env.example .env
chmod +x scripts/*.sh
./scripts/dev.sh
```

The script builds Spring Boot, starts backend/adapter/frontend and stops its processes on Ctrl+C. Logs are under `.runtime/`. Leave `AGECM_MODE=DEMO` to run without hardware. Alternatively, start each component in its own terminal after exporting the variables from `.env`:

```bash
set -a; source .env; set +a
# On this Mac, when default Java is 25:
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
mvn -f backend/pom.xml spring-boot:run
python3 processing/adapter.py --scenario cycle
cd frontend && npm ci && npm run dev
```

The three launch commands above are separate foreground processes, each in a separate terminal. Frontend: http://127.0.0.1:5173 . Backend: http://127.0.0.1:8080 . Vite proxies `/api` and `/ws`, keeping the browser free of private channel credentials. Native backend binds to loopback by default. Replace the local development ingestion token and database password before any shared deployment. No public read authentication is provided; this is a local course-project application.

## Configuration

All variables and safe local defaults are in `.env.example`. Required live settings are `AGECM_MODE=LIVE`, both `THINGSPEAK_NODE{1,2}_CHANNEL_ID` and `THINGSPEAK_NODE{1,2}_READ_KEY`, the database settings, and a matching `INGESTION_TOKEN` for backend and adapter. The native script loads `.env`; direct Maven/Python invocations require exporting it first. Never add private keys to `VITE_*` variables.

`REPORT_INTERVAL_SECONDS=30`, `CLOUD_POLL_SECONDS=15`, `STALE_SECONDS=95`, `REQUEST_TIMEOUT_SECONDS=10`, `REQUEST_RETRIES=2`, and `FEATURE_OWNER=python` are explicit implementation choices. `WARNING_TILT_RATE` and `CRITICAL_TILT_RATE` configure the laboratory rule. Restart adapter/backend after configuration changes. Frontend connection fallback polls every 5 seconds independently of cloud reporting.

Read [the hardware integration guide](docs/hardware-integration.md) for the complete field mapping, write examples, timing/provenance decisions, source identity, cursor recovery, wiring and physical acceptance sequence. It is also served from the Architecture page. Physical channel credentials, verified ESP32 firmware and purchased sensor/display specifications remain outstanding.

## Demo scenarios

```bash
python3 processing/adapter.py --scenario cycle
python3 processing/adapter.py --scenario stationary
python3 processing/adapter.py --scenario increasing_tilt
python3 processing/adapter.py --scenario displacement
python3 processing/adapter.py --scenario vibration
python3 processing/adapter.py --scenario warning
python3 processing/adapter.py --scenario critical
python3 processing/adapter.py --scenario sensor_failure
python3 processing/adapter.py --scenario stale
python3 processing/adapter.py --scenario cloud_failure
```

Run only one adapter. The default demo preloads 80 timestamped samples per node, then continues at an explicitly accelerated 2-second cadence. `--seed-count 0` disables preloading; `--once --seed-count 80` sends a finite fixture. Stale mode stops Node 02 after preloading; cloud_failure simulates an outage without sending physical cloud requests. Historical simulation sessions remain source-labeled in PostgreSQL.

## API and data contract

Read routes: `/api/health`, `/api/system/status`, `/api/nodes`, `/api/nodes/{id}`, `/api/nodes/{id}/latest`, `/api/nodes/{id}/history`, `/api/telemetry/latest`, `/api/telemetry/history`, `/api/alerts`, `/api/alerts/{id}`, `/api/integration/thingspeak/status`. History accepts `start`, `end`, `nodeId`, `page` and `size` (max 2,000). Alerts paginate with max 500. Queries are always scoped to the server's active source mode. The UI loads the latest 1,000 samples per node in its selected range and states this limit; all records remain accessible through pagination.

Protected routes use `X-Ingestion-Token`: `POST /api/telemetry`, `POST /api/integration/status`, `GET /api/ingestion/{node}`. Invalid node/source/schema/timestamps are rejected; Node 03 cannot ingest sensing data. The `TelemetryInput` class is the schema 1.0 DTO. Backend receipt time is server-assigned. Missing values stay null. Cloud/source uniqueness and cursor persistence are enforced transactionally. Alerts open once per active condition and resolve as conditions change; stale and cloud failures suppress current movement classification.

STOMP WebSocket endpoint: `/ws`. Topics: `/topic/telemetry`, `/topic/alerts`, `/topic/health`. Events publish after database commit. Frontend reconnects automatically and retains REST polling fallback.

## Tests and validation

```bash
python3 -m unittest discover -s processing/tests -v
JAVA_HOME=$(/usr/libexec/java_home -v 21) mvn -f backend/pom.xml test
cd frontend && npm run build
# With native demo services running and Google Chrome installed:
npm run test:e2e
```

Backend tests use an isolated H2 database in PostgreSQL compatibility mode; runtime uses genuine PostgreSQL. Browser tests use installed Google Chrome through Playwright, including STOMP telemetry publication. See [validation results](docs/validation.md) for executed checks and limitations.

## Repository

```text
frontend/      React pages, Recharts, API/STOMP provider, responsive CSS, images, browser tests
backend/       Spring Boot DTO/entities/repositories/service/API, Flyway migration, integration tests
processing/    ThingSpeak adapter, signal processing, deterministic demo, guarded write test, tests
docs/          Hardware integration, image provenance/prompts, validation evidence
output/        Full-resolution generated image masters
scripts/       Native launch and test helpers
compose.yaml   PostgreSQL, backend, processing and frontend services
.env.example   Configuration contract with no private credentials
```

## Boundaries

This is a laboratory educational prototype. No physical sensor connectivity, field reliability, LoRa fallback, battery-life saving or mine-failure prediction has been validated. Uptime-only firmware needs a documented UTC anchor before ingestion. Unrecoverable cloud gaps and malformed source identity require manual reconciliation; the adapter will not silently skip them. Rates warm up again after restart. New physical measurements require sensor/firmware calibration and tests; future sensor additions require a schema migration and metric configuration. There are no unused gas, temperature, pressure or humidity cards.
