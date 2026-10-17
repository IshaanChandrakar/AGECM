"""ThingSpeak reader and explicitly separate deterministic demonstration source."""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import json
import logging
import math
import os
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from uuid import uuid4
from processor import Processor, number, utc

LOG = logging.getLogger("agecm.adapter")


class Http:
    def __init__(self, timeout=10, retries=2):
        self.timeout, self.retries = timeout, retries

    def request(self, method, url, data=None, headers=None):
        for attempt in range(self.retries+1):
            try:
                req = Request(url, data=json.dumps(data).encode() if data is not None else None,
                              method=method, headers={"Content-Type": "application/json", **(headers or {})})
                with urlopen(req, timeout=self.timeout) as res:
                    return json.load(res)
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                if attempt == self.retries:
                    # Do not put URLs containing private API keys into logs/exceptions.
                    raise RuntimeError(f"HTTPS/HTTP {method} failed ({type(exc).__name__})") from None
                time.sleep(min(2**attempt, 4))


class Adapter:
    def __init__(self, http=None):
        self.http = http or Http(float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")), int(os.getenv("REQUEST_RETRIES", "2")))
        self.base = os.getenv("BACKEND_URL", "http://127.0.0.1:8080").rstrip("/")
        self.headers = {"X-Ingestion-Token": os.getenv("INGESTION_TOKEN", "local-development-token")}
        self.mode = os.getenv("AGECM_MODE", "DEMO").upper()
        if self.mode not in ("DEMO", "LIVE"):
            raise ValueError("AGECM_MODE must be DEMO or LIVE")
        self.report_interval = int(os.getenv("REPORT_INTERVAL_SECONDS", "30"))
        self.processors = {n: Processor(os.getenv("FEATURE_OWNER", "python")) for n in ("node_01", "node_02")}
        self.cursors = {}

    def backend(self, method, path, body=None):
        return self.http.request(method, self.base+path, body, self.headers)

    def report(self, node, status, error=None, gaps=0):
        self.backend("POST", "/api/integration/status", dict(nodeId=node, status=status, error=error, gaps=gaps))

    def deliver(self, raw):
        processor = self.processors[raw["nodeId"]]
        checkpoint = copy.deepcopy(processor.sessions)
        try:
            data = processor.process(raw)
            response = self.backend("POST", "/api/telemetry", data)
            if not response.get("accepted"):
                raise RuntimeError("Backend rejected telemetry")
            return response
        except Exception:
            processor.sessions = checkpoint
            raise

    def normalize(self, node, channel, feed):
        entry = feed.get("entry_id")
        if not isinstance(entry, int) or entry < 1:
            raise ValueError("Missing valid ThingSpeak entry ID")
        created = utc(feed.get("created_at"))
        status = json.loads(feed.get("status") or "{}")
        if not isinstance(status, dict) or status.get("schema") != "1.0":
            raise ValueError("Status metadata requires schema 1.0")
        acquired = utc(status.get("acquiredAt"))
        if acquired > created+timedelta(seconds=10) or acquired > datetime.now(timezone.utc)+timedelta(seconds=10):
            raise ValueError("Invalid future acquisition timestamp")
        seq = number(feed.get("field7"), 0, 2**53-1)
        flags = number(feed.get("field6"), 0, 65535)
        boot = feed.get("field8")
        if seq is None or not seq.is_integer() or flags is None or not flags.is_integer() or not isinstance(boot,str) or not boot or len(boot)>100:
            raise ValueError("Invalid source identity or quality flags")
        report = status.get("reportIntervalSeconds", self.report_interval)
        sample = status.get("sampleIntervalMs")
        if not isinstance(report,int) or report <= 0 or not isinstance(sample,int) or sample <= 0:
            raise ValueError("Invalid sampling/reporting metadata")
        return dict(nodeId=node, source="cloud_hardware", schemaVersion="1.0", bootId=boot,
                    sequence=int(seq), channelId=str(channel), entryId=entry,
                    acquiredAt=acquired.isoformat(), cloudCreatedAt=created.isoformat(), uptimeMs=status.get("uptimeMs"),
                    tilt=number(feed.get("field1"), -180, 180), displacement=number(feed.get("field2"), -2000, 2000),
                    vibration=number(feed.get("field3"), 0, 16), tiltRate=number(feed.get("field4"), -360, 360),
                    displacementVelocity=number(feed.get("field5"), -4000, 4000), qualityFlags=int(flags),
                    calibrated=status.get("calibrated") is True, sampleIntervalMs=sample, reportIntervalSeconds=report)

    def poll_node(self, node):
        index = "1" if node == "node_01" else "2"
        channel = os.getenv(f"THINGSPEAK_NODE{index}_CHANNEL_ID", "")
        key = os.getenv(f"THINGSPEAK_NODE{index}_READ_KEY", "")
        if not channel or not key:
            self.report(node, "NOT_CONFIGURED", "Channel ID or Read API key is not configured")
            return
        try:
            if not channel.isdigit():
                raise ValueError("Channel ID must be numeric")
            if node not in self.cursors:
                saved = self.backend("GET", f"/api/ingestion/{node}")
                if saved["mode"].upper() != "LIVE":
                    raise ValueError("Backend and adapter modes differ")
                self.cursors[node] = int(saved["lastEntryId"])
            cursor = self.cursors[node]
            # Fetch a small current window; expand to the API maximum after an interruption.
            payload = self.http.request("GET", "https://api.thingspeak.com/channels/"+channel+"/feeds.json?"+urlencode(dict(api_key=key, results=100, status="true")))
            feeds = payload.get("feeds")
            if not isinstance(feeds, list):
                raise ValueError("Malformed ThingSpeak feed")
            if cursor and feeds and feeds[0].get("entry_id", 0) > cursor+1:
                payload = self.http.request("GET", "https://api.thingspeak.com/channels/"+channel+"/feeds.json?"+urlencode(dict(api_key=key, results=8000, status="true")))
                feeds = payload.get("feeds", [])
                if feeds and feeds[0].get("entry_id", 0) > cursor+1:
                    self.report(node, "GAP", "Catch-up exceeds readable cloud history; manual reconciliation required", 1)
                    return
            for feed in sorted(feeds, key=lambda f: f.get("entry_id", 0)):
                if feed.get("entry_id", 0) <= cursor:
                    continue
                raw = self.normalize(node, channel, feed)
                self.deliver(raw)
                cursor = raw["entryId"]
                self.cursors[node] = cursor
            self.report(node, "HEALTHY")
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            LOG.warning("%s ingestion failed: %s", node, str(exc))
            self.report(node, "ERROR", str(exc))

    def demo(self, scenario="cycle", interval=2.0, seed_count=80, once=False):
        boot = "demo-"+str(uuid4())[:12]
        seq = 0
        start = datetime.now(timezone.utc)-timedelta(seconds=seed_count*interval)
        while True:
            for index, node in enumerate(("node_01", "node_02")):
                # Each scenario is deterministic for a given sequence; time is actual UTC.
                phase = seq % 180
                selected = scenario
                if selected == "cycle":
                    selected = "stationary" if phase < 30 or phase >= 145 else "increasing_tilt" if phase < 70 else "critical" if phase < 110 else "recovery"
                if selected == "stale" and node == "node_02" and seq >= seed_count:
                    continue
                if selected == "cloud_failure" and seq >= seed_count:
                    self.report(node, "ERROR", "Simulated connectivity interruption; no physical ThingSpeak request")
                    continue
                rate = .065 if selected in ("increasing_tilt", "warning") else .18 if selected == "critical" else .001
                if scenario == "cycle":
                    # Smooth bounded rig motion; recovery is motion until the rig settles.
                    change = .001*min(phase,30) + .065*max(0,min(phase-30,40)) + .18*max(0,min(phase-70,40)) - .28*max(0,min(phase-110,35))
                    tilt = 1.2+index*.2+change*interval+.003*math.sin(seq/4+index)
                else:
                    triangular = 150-abs((seq % 300)-150)
                    tilt = 1.2+index*.2+rate*triangular*interval+.003*math.sin(seq/4+index)
                displacement = 2+index+.3*math.sin(seq/8) if selected != "displacement" else 2+(seq%50)*.3
                vibration = .025+.003*math.sin(seq) if selected != "vibration" else .8+.1*math.sin(seq)
                failure = selected == "sensor_failure" and node == "node_02"
                raw = dict(nodeId=node, source="demo", schemaVersion="1.0", bootId=boot, sequence=seq,
                           channelId=None, entryId=None, cloudCreatedAt=None,
                           acquiredAt=(start+timedelta(seconds=seq*interval)).isoformat() if seq < seed_count else datetime.now(timezone.utc).isoformat(),
                           uptimeMs=int(seq*interval*1000), tilt=None if failure else tilt,
                           displacement=displacement, vibration=vibration, qualityFlags=1 if failure else 0,
                           calibrated=True, sampleIntervalMs=int(interval*1000), reportIntervalSeconds=max(1,int(interval)))
                while True:
                    try:
                        self.deliver(raw)
                        self.report(node, "DEMO")
                        break
                    except RuntimeError as exc:
                        LOG.warning("Demo delivery paused until backend recovery: %s", exc)
                        time.sleep(5)
            seq += 1
            if once and seq >= seed_count:
                return
            if seq >= seed_count:
                time.sleep(interval)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["cycle", "stationary", "increasing_tilt", "displacement", "vibration", "warning", "critical", "recovery", "sensor_failure", "stale", "cloud_failure"], default="cycle")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--seed-count", type=int, default=80)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    adapter = Adapter()
    if adapter.mode == "DEMO":
        adapter.demo(args.scenario, float(os.getenv("DEMO_INTERVAL_SECONDS", "2")), args.seed_count, args.once)
    else:
        with ThreadPoolExecutor(max_workers=2) as pool:
            while True:
                futures = [pool.submit(adapter.poll_node, node) for node in ("node_01", "node_02")]
                for task in futures:
                    try:
                        task.result()
                    except RuntimeError as exc:
                        LOG.error("Backend unavailable: %s", exc)
                if args.once:
                    return
                time.sleep(max(5, float(os.getenv("CLOUD_POLL_SECONDS", "15"))))


if __name__ == "__main__":
    main()
