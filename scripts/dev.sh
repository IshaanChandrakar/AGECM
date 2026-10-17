#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi
# Spring Boot 3.3.x supports the requested Java 17 target; use installed Java 21 on this Mac.
if [[ -z "${JAVA_HOME:-}" ]] && [[ -x /usr/libexec/java_home ]]; then
  AGECM_JDK_PATH=$(/usr/libexec/java_home -v 21 2>/dev/null || /usr/libexec/java_home -v 17 2>/dev/null || true)
  if [[ -n "$AGECM_JDK_PATH" ]]; then export JAVA_HOME="$AGECM_JDK_PATH"; export PATH="$JAVA_HOME/bin:$PATH"; fi
fi
mkdir -p .runtime
if [[ ! -d frontend/node_modules ]]; then (cd frontend && npm ci); fi
mvn -q -f backend/pom.xml package -DskipTests
cp backend/target/monitoring-1.0.0.jar .runtime/monitoring-dev.jar
java -jar .runtime/monitoring-dev.jar > .runtime/backend.log 2>&1 &
AGECM_BACKEND_PID=$!
AGECM_ADAPTER_PID=""
AGECM_FRONTEND_PID=""
cleanup(){ kill "$AGECM_BACKEND_PID" ${AGECM_ADAPTER_PID:+$AGECM_ADAPTER_PID} ${AGECM_FRONTEND_PID:+$AGECM_FRONTEND_PID} 2>/dev/null || true; }
trap cleanup EXIT INT TERM
for AGECM_ATTEMPT in $(seq 1 60); do
 if curl -fsS "${BACKEND_URL:-http://127.0.0.1:8080}/api/health" >/dev/null 2>&1; then break; fi
 if ! kill -0 "$AGECM_BACKEND_PID" 2>/dev/null; then cat .runtime/backend.log; exit 1; fi
 sleep 1
done
curl -fsS "${BACKEND_URL:-http://127.0.0.1:8080}/api/health" >/dev/null
python3 processing/adapter.py --scenario "${DEMO_SCENARIO:-cycle}" > .runtime/adapter.log 2>&1 &
AGECM_ADAPTER_PID=$!
(cd frontend && exec npm run dev) &
AGECM_FRONTEND_PID=$!
printf '\nAGECM: http://127.0.0.1:5173  |  Ctrl+C stops the application.\n'
wait
