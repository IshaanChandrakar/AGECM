"""Normalize firmware observations without inventing thresholds or aggregations."""
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import os

METRICS = ('temperature', 'humidity', 'coMax', 'ch4Max', 'distanceNow', 'devMax', 'statusWorst', 'faultAny')


def utc(value):
    if not isinstance(value, str):
        raise ValueError('Timezone-aware ISO-8601 timestamp required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return parsed.astimezone(timezone.utc)


def load_contract():
    path = Path(os.getenv('SENSOR_CONTRACT_PATH') or Path(__file__).resolve().parents[1]/'config/sensor-contract.json')
    contract = json.loads(path.read_text())
    for node in ('node_01', 'node_02'):
        mapping = contract['nodes'][node]
        if set(mapping) != set(METRICS) or set(mapping.values()) != {f'field{i}' for i in range(1, 9)}:
            raise ValueError(f'Invalid independent field mapping for {node}')
    return contract


def number(value):
    if value is None or value == '' or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


class Processor:
    def __init__(self, contract=None):
        self.contract = contract or load_contract()

    def process(self, raw):
        result = dict(raw)
        issues = dict(raw.get('fieldIssues') or {})
        for name in METRICS:
            supplied = raw.get(name)
            value = number(supplied)
            if value is None:
                issues[name] = 'missing' if supplied in (None, '') else 'invalid number'
            if name in ('statusWorst', 'faultAny') and value is not None:
                if not value.is_integer() or abs(value) > 2147483647 or (name == 'faultAny' and value not in (0, 1)) or (name == 'statusWorst' and self.contract['semanticsConfirmed'] and str(int(value)) not in self.contract['statusCodes']):
                    issues[name] = 'invalid discrete code'
                    value = None
                else:
                    value = int(value)
            if name in ('coMax','ch4Max','devMax','distanceNow') and value is not None and value < 0:
                issues[name] = 'firmware distance sentinel' if name == 'distanceNow' else 'negative measurement'
                value = None
            if name == 'humidity' and value is not None and not 0 <= value <= 100:
                issues[name] = 'outside 0–100 %RH'
                value = None
            result[name] = value
        result['rawDistanceNow'] = number(raw.get('distanceNow'))
        if result.get('faultAny') == 1:
            for key in ('distanceNow','devMax'):
                if result.get(key) == 0:
                    issues[key] = 'zero may represent a failed distance read; fault occurred in this window'
        result['fieldIssues'] = json.dumps(issues, separators=(',', ':'))
        return result
