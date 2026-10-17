"""Versioned laboratory signal processing. No prediction or safety validation claims."""
from collections import deque
from datetime import datetime, timezone
import math
import os


def utc(value):
    if not isinstance(value, str):
        raise ValueError("ISO-8601 timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def number(value, low, high):
    if value is None or value == "":
        return None
    try:
        x = float(value)
    except (ValueError, TypeError):
        return None
    return x if math.isfinite(x) and low <= x <= high else None


class Processor:
    def __init__(self, feature_owner="python", warning=None, critical=None):
        if feature_owner not in ("python", "firmware"):
            raise ValueError("FEATURE_OWNER must be python or firmware")
        self.owner = feature_owner
        self.warning = float(warning or os.getenv("WARNING_TILT_RATE", ".02"))
        self.critical = float(critical or os.getenv("CRITICAL_TILT_RATE", ".10"))
        if not 0 < self.warning < self.critical:
            raise ValueError("Invalid laboratory thresholds")
        self.sessions = {}

    def process(self, raw):
        t = utc(raw["acquiredAt"])
        node = raw["nodeId"]
        session = self.sessions.get(node)
        if session is None or session["boot"] != raw["bootId"]:
            session = dict(boot=raw["bootId"], samples=deque(maxlen=5), filtered=deque(maxlen=8),
                           state="NORMAL", candidate=None, dwell=0, last=None)
            self.sessions[node] = session
        # History/backfill can be stored, but must not contaminate the live feature window.
        ordered = session["last"] is None or t > session["last"]
        values = [number(raw.get("tilt"), -180, 180), number(raw.get("displacement"), -2000, 2000),
                  number(raw.get("vibration"), 0, 16)]
        out = dict(raw, tilt=values[0], displacement=values[1], vibration=values[2],
                   tiltRate=None, displacementVelocity=None, featureReady=False,
                   ruleVersion="lab-rule-v1", state="UNAVAILABLE", health="NOT_READY")
        valid = all(v is not None for v in values) and raw.get("qualityFlags") == 0 and raw.get("calibrated") is True
        if not valid:
            out["health"] = "INVALID_SENSOR" if raw.get("qualityFlags") != 0 or None in values else "NOT_READY"
            if ordered:
                session["samples"].clear(); session["filtered"].clear()
                session.update(candidate=None, dwell=0, state="NORMAL", last=t)
            return out
        if not ordered:
            return out
        if session["last"] is not None and (t-session["last"]).total_seconds() > max(95, 3*raw.get("reportIntervalSeconds", 30)):
            session["samples"].clear(); session["filtered"].clear()
            session.update(candidate=None, dwell=0, state="NORMAL")
        session["last"] = t
        if self.owner == "firmware":
            out["tiltRate"] = number(raw.get("tiltRate"), -360, 360)
            out["displacementVelocity"] = number(raw.get("displacementVelocity"), -4000, 4000)
        else:
            session["samples"].append(values)
            if len(session["samples"]) == 5:
                avg = [sum(v[i] for v in session["samples"])/5 for i in (0, 1)]
                session["filtered"].append((t, avg))
                if len(session["filtered"]) == 8:
                    first, last = session["filtered"][0], session["filtered"][-1]
                    elapsed = (last[0]-first[0]).total_seconds()
                    if elapsed > 0:
                        out["tiltRate"] = (last[1][0]-first[1][0])/elapsed
                        out["displacementVelocity"] = (last[1][1]-first[1][1])/elapsed
        if out["tiltRate"] is None or out["displacementVelocity"] is None:
            return out
        out["featureReady"] = True
        out["health"] = "HEALTHY"
        rate = abs(out["tiltRate"])
        state = session["state"]
        # Magnitude rule, 3 observations to escalate, 5 to recover, 30% hysteresis.
        if rate >= self.critical:
            candidate = "CRITICAL"
        elif state == "CRITICAL" and rate >= self.critical*.7:
            candidate = "CRITICAL"
        elif rate >= self.warning:
            candidate = "WARNING"
        elif state == "WARNING" and rate >= self.warning*.7:
            candidate = "WARNING"
        else:
            candidate = "NORMAL"
        if candidate == session["candidate"]:
            session["dwell"] += 1
        else:
            session.update(candidate=candidate, dwell=1)
        ranks = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2}
        required = 3 if ranks[candidate] > ranks[state] else 5
        if session["dwell"] >= required:
            session["state"] = candidate
        out["state"] = session["state"]
        return out
