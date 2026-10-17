# Validation evidence

Executed locally on 15 October 2026. This folder is a fresh implementation; the older app was not copied or modified.

| Check | Result |
|---|---|
| Python processing/ThingSpeak adapter tests | 16 passed using standard-library unittest and mocked HTTP responses |
| Spring Boot integration tests | 8 passed; isolated H2 PostgreSQL-compatibility databases for DEMO and LIVE modes |
| Frontend production build | Passed TypeScript and Vite build; Analytics loaded separately from the homepage |
| Playwright / installed Google Chrome | 6 passed; desktop 1440 px and mobile 390 px route checks |
| Frontend dependency audit | 0 known vulnerabilities reported by npm audit at validation time |
| Real PostgreSQL 17 runtime | Flyway migration applied; demo telemetry and alerts persisted; REST history retrieved |
| Actual STOMP WebSocket | Connected, subscribed, ingested an authenticated demo packet, received committed telemetry and read it back from PostgreSQL |
| Native live-mode smoke test | Separate backend on port 8081 plus Python adapter with no credentials: both nodes Not Configured / Unavailable; central Unverified; no cloud_hardware records created |
| Docker Compose configuration | Validated with docker compose config -q |
| Container build/start | Not executed: Docker daemon unavailable on the host |
| Genuine ThingSpeak/private-channel integration | Not executed: channel IDs/keys and verified hardware were not supplied |
| Physical sensors, Wi-Fi coverage, central display, LoRa, field reliability | Not verified |

## What the tests exercise

Python: actual elapsed-time rates, feature readiness, negative-rate magnitude escalation, consecutive-evidence behavior, missing/NaN readings, reboot and gap resets, firmware feature ownership, string/null feed parsing, identity/schema validation, backend-acceptance cursor ordering, restart cursor loading, cloud duplicate skipping, empty feeds, rollback after failed delivery, unrecoverable catch-up gaps, timeout retry redaction, positive write-entry validation and explicit unconfigured-channel reporting.

Backend: authenticated ingestion, exact two-sensing-node representation, separate unverified central role, source-mode enforcement, duplicate telemetry and single alert episodes, alert resolution, older-backfill protection, invalid/stale unavailability, history pagination, live cloud identity/cursor handling and cloud-error state suppression. Duplicate source packets received under new cloud entry IDs advance the committed cursor without creating duplicate telemetry.

Browser: relevant local image loading, homepage/dashboard navigation, mobile menu, API-backed readings, all five chart containers, node/time filters, CSV export, alert dialog, backend failure, empty live mode, all routes without runtime errors or horizontal overflow, and genuine STOMP/REST integration.

Desktop and mobile screenshots are retained in `output/preview/`. Their illustrative images were visually reviewed. Full-page capture scrolls images into view first so lazy loading is exercised. The website's JPGs are approximately 1.7 MB total; source PNGs are retained under `output/imagegen/`.

## Limits

Tests mock external ThingSpeak responses and validate its documented contracts. They do not prove real sensor acquisition, physical ESP32 firmware, display behavior or an actual mine installation. The runtime was tested on Java 21 with Java 17 compilation target; a Java 17 container runtime was configured but not executed. Spring Boot's pinned Flyway version reports that PostgreSQL 17 is newer than its tested support window; schema migration, validation and runtime persistence nevertheless passed locally. Compose uses PostgreSQL 16.

No prediction accuracy, LoRa communication, energy reduction or field deployment outcome is claimed. Current software uses a configurable laboratory tilt-rate rule; physical threshold calibration remains required. Larger histories are paginated through the API; the frontend deliberately shows up to 1,000 records per node and discloses that limit. Adapter processing buffers warm up again after restart. Unrecoverable gaps or malformed source identity require manual reconciliation rather than silently advancing the cursor.
