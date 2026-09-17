"""
Thin REST client to the Spring Boot backend.

Every call is best-effort and swallows connection errors, so the engine runs
fully offline (PURE_PYTHON_SIMULATION) when no backend is up.
"""

import requests


class BackendClient:
    def __init__(self, base_url, timeout=1.5, logger=None):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self._log = logger
        self._warned = False

    def _post(self, path, payload):
        try:
            requests.post(self.base + path, json=payload, timeout=self.timeout)
        except requests.RequestException:
            if not self._warned:
                print(f"[backend] unreachable at {self.base} — continuing offline")
                self._warned = True

    def post_telemetry(self, packet, run_id=None):
        payload = packet.to_backend_payload()
        if run_id is not None:
            payload["runId"] = run_id
        self._post("/api/telemetry", payload)

    def post_consensus(self, event, run_id=None):
        self._post("/api/consensus", {**event, "runId": run_id})

    def post_network(self, event, run_id=None):
        self._post("/api/network", {**event, "runId": run_id})

    def post_front(self, estimate, run_id=None):
        self._post("/api/front-estimation", {**estimate, "runId": run_id})

    def start_run(self, scenario, node_count):
        try:
            r = requests.post(self.base + "/api/simulation/start",
                              json={"scenario": scenario, "nodeCount": node_count},
                              timeout=self.timeout)
            return r.json().get("runId") if r.ok else None
        except (requests.RequestException, ValueError):
            return None

    def stop_run(self, run_id):
        self._post("/api/simulation/stop", {"runId": run_id})
