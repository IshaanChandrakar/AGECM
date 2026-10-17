#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s processing/tests -v
mvn -q -f backend/pom.xml test
(cd frontend && npm run build)
# With dev services and Google Chrome running: cd frontend && npm run test:e2e
