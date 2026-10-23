"""ThingSpeak reader and explicitly separate deterministic demonstration source."""
import argparse
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
from processor import Processor, METRICS, load_contract, utc

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
                    raise RuntimeError(f"HTTPS/HTTP {method} failed ({type(exc).__name__}, status={getattr(exc, 'code', 'unavailable')})") from None
                time.sleep(min(2**attempt, 4))


class Adapter:
    def __init__(self, http=None):
        self.http = http or Http(float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")), int(os.getenv("REQUEST_RETRIES", "2")))
        self.base = os.getenv("BACKEND_URL", "http://127.0.0.1:8080").rstrip("/")
        self.headers = {"X-Ingestion-Token": os.getenv("INGESTION_TOKEN", "local-development-token")}
        self.mode = os.getenv("AGECM_MODE", "DEMO").upper()
        if self.mode not in ("DEMO", "LIVE"):
            raise ValueError("AGECM_MODE must be DEMO or LIVE")
        self.report_interval = int(os.getenv("REPORT_INTERVAL_SECONDS", "20"))
        self.contract = load_contract()
        self.processor = Processor()
        self.cloud_base = os.getenv("THINGSPEAK_BASE_URL", "https://api.thingspeak.com").rstrip("/")
        if not self.cloud_base.startswith("https://") and not (os.getenv("ALLOW_LOCAL_THINGSPEAK_MOCK") == "true" and self.cloud_base.startswith(("http://127.0.0.1:", "http://localhost:", "http://thingspeak-mock:"))):
            raise ValueError("ThingSpeak requires HTTPS; local mock transport requires explicit opt-in")
        if os.getenv('AGECM_ENV') == 'production':
            if self.mode != 'LIVE' or self.cloud_base != 'https://api.thingspeak.com' or os.getenv('ALLOW_LOCAL_THINGSPEAK_MOCK', 'false') != 'false':
                raise ValueError('Production requires real read-only ThingSpeak HTTPS in LIVE mode')
            token = self.headers['X-Ingestion-Token']
            if len(token) < 32 or 'REPLACE' in token or token == 'local-development-token':
                raise ValueError('Production requires a private ingestion token of at least 32 characters')
            for index in (1, 2):
                channel = os.getenv(f'THINGSPEAK_NODE{index}_CHANNEL_ID', '')
                key = os.getenv(f'THINGSPEAK_NODE{index}_READ_KEY', '')
                if not channel.isdigit() or not key or 'REPLACE' in key:
                    raise ValueError('Production requires both numeric channel IDs and Read API keys')
        self.cursors = {}
        self.watermarks = {}

    def backend(self, method, path, body=None):
        return self.http.request(method, self.base+path, body, self.headers)

    def report(self, node, status, error=None, gaps=0):
        self.backend("POST", "/api/integration/status", dict(nodeId=node, status=status, error=error, gaps=gaps))

    def deliver(self, raw):
        response = self.backend("POST", "/api/telemetry", self.processor.process(raw))
        if not response.get("accepted"):
            raise RuntimeError("Backend rejected telemetry")
        return response

    def normalize(self, node, channel, feed):
        entry = feed.get('entry_id')
        if not isinstance(entry, int) or isinstance(entry, bool) or entry < 1:
            raise ValueError('Missing valid ThingSpeak entry ID')
        created = utc(feed.get('created_at'))
        if created > datetime.now(timezone.utc)+timedelta(seconds=10):
            raise ValueError('Future cloud timestamp')
        metadata = {}
        status = feed.get('status')
        if isinstance(status, str):
            try:
                parsed = json.loads(status)
                if isinstance(parsed, dict):
                    metadata = parsed
            except (ValueError, TypeError):
                pass  # Plain-text firmware status does not invalidate measurements.
        acquired = utc(metadata['acquiredAt']) if metadata.get('acquiredAt') else None
        if acquired and (acquired > created+timedelta(seconds=10) or acquired > datetime.now(timezone.utc)+timedelta(seconds=10)):
            raise ValueError('Future acquisition timestamp')
        raw = dict(nodeId=node, source='cloud_hardware', schemaVersion='2.0',
                   channelId=str(channel), entryId=entry, acquiredAt=acquired.isoformat() if acquired else None,
                   cloudCreatedAt=created.isoformat(), bootId=metadata.get('bootId'), sequence=metadata.get('sequence'),
                   statusText=status if isinstance(status,str) else None)
        for metric, field in self.contract['nodes'][node].items():
            raw[metric] = feed.get(field)
        return raw

    def verify_channel(self, node, payload, channel):
        metadata = payload.get('channel')
        if not isinstance(metadata, dict) or str(metadata.get('id')) != channel:
            raise ValueError('Channel identity mismatch')
        names = {m['key']: m['fieldLabel'] for m in self.contract['metrics']}
        for metric, field in self.contract['nodes'][node].items():
            if str(metadata.get(field, '')).strip().casefold() != names[metric].strip().casefold():
                raise ValueError(f'Channel field label mismatch for {metric}; review the contract')

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
                self.watermarks[node] = utc(saved["lastCloudCreatedAt"]) if saved.get("lastCloudCreatedAt") else None
            cursor = self.cursors[node]
            watermark = self.watermarks.get(node)
            # Fetch a small current window; expand to the API maximum after an interruption.
            payload = self.http.request("GET", self.cloud_base+"/channels/"+channel+"/feeds.json?"+urlencode(dict(api_key=key, results=100, status="true")))
            self.verify_channel(node, payload, channel)
            feeds = payload.get("feeds")
            if not isinstance(feeds, list):
                raise ValueError("Malformed ThingSpeak feed")
            feeds = sorted(feeds, key=lambda f: f.get("entry_id", 0))
            # Entry IDs alone are not durable across a ThingSpeak channel clear.
            # Only newer cloud timestamps constitute evidence of ID reuse.
            reused = watermark is not None and any(f.get('entry_id', 0) <= cursor and utc(f.get('created_at')) > watermark for f in feeds)
            if feeds and (cursor == 0 or reused or feeds[0].get("entry_id", 0) > cursor+1):
                payload = self.http.request("GET", self.cloud_base+"/channels/"+channel+"/feeds.json?"+urlencode(dict(api_key=key, results=8000, status="true")))
                self.verify_channel(node, payload, channel)
                feeds = sorted(payload.get("feeds", []), key=lambda f: f.get("entry_id", 0))
                reset_start_missing = reused and feeds and feeds[0].get('entry_id', 0) > 1 and utc(feeds[0].get('created_at')) > watermark
                if feeds and (reset_start_missing or (cursor > 0 and not reused and feeds[0].get("entry_id", 0) > cursor+1)):
                    self.report(node, "GAP", "Catch-up exceeds readable cloud history; manual reconciliation required", 1)
                    return
            bootstrap_start = feeds[0].get('entry_id', 0) if cursor == 0 and feeds and feeds[0].get('entry_id', 0) > 1 else None
            for feed in sorted(feeds, key=lambda f: (utc(f.get("created_at")), f.get("entry_id", 0))):
                created = utc(feed.get("created_at"))
                if feed.get("entry_id", 0) <= cursor and not (watermark is not None and created > watermark):
                    continue
                raw = self.normalize(node, channel, feed)
                self.deliver(raw)
                if watermark is None or created > watermark or (created == watermark and raw["entryId"] > cursor):
                    cursor = raw["entryId"]
                    watermark = created
                    self.cursors[node] = cursor
                    self.watermarks[node] = watermark
            if bootstrap_start is not None:
                self.report(node, 'HEALTHY', f'Initial bootstrap starts at readable entry {bootstrap_start}; earlier history is unavailable from this bounded cloud read', 1)
            else:
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
                    selected = "stationary"
                if selected == "stale" and node == "node_02" and seq >= seed_count:
                    continue
                if selected == "cloud_failure" and seq >= seed_count:
                    self.report(node, "ERROR", "Simulated connectivity interruption; no physical ThingSpeak request")
                    continue
                # Numerical demo values are illustrative, not hardware measurements or safety limits.
                failed = selected == 'sensor_failure' and node == 'node_02'
                raw = dict(nodeId=node, source='demo', schemaVersion='2.0', bootId=boot, sequence=seq,
                           channelId=None, entryId=None, cloudCreatedAt=None,
                           acquiredAt=(start+timedelta(seconds=seq*interval)).isoformat() if seq < seed_count else datetime.now(timezone.utc).isoformat(),
                           temperature=None if failed else 24+index+math.sin(seq/10),
                           humidity=50+index+2*math.sin(seq/13), coMax=0 if seq % 20 < 5 else 3+index,
                           ch4Max=0 if seq % 15 < 5 else 5+index,
                           distanceNow=100+index+math.sin(seq/8), devMax=.5+abs(math.sin(seq/7)),
                           statusWorst=seq//20 % 3, faultAny=None if failed else seq//40 % 2)
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
    parser.add_argument("--scenario", choices=["cycle", "stationary", "sensor_failure", "stale", "cloud_failure"], default="cycle")
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
                time.sleep(max(5, float(os.getenv("CLOUD_POLL_SECONDS", "5"))))


if __name__ == "__main__":
    main()
