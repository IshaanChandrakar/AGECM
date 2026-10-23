"""Read-only comparison of real cloud observations, PostgreSQL and the served API.

Run from the repository root. No channel writes, cursor resets or data mutations.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlencode
from urllib.request import urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'processing'))
from processor import Processor, METRICS, utc


def run(*args):
    return subprocess.check_output(args, stderr=subprocess.PIPE).decode()


def verify(project, base):
    reader = json.loads(run('docker', 'inspect', project+'-processing-1'))[0]
    env = dict(item.split('=', 1) for item in reader['Config']['Env'] if '=' in item)
    assert env['AGECM_MODE'] == 'LIVE'
    assert env.get('THINGSPEAK_BASE_URL', 'https://api.thingspeak.com') == 'https://api.thingspeak.com'
    status = json.load(urlopen(base+'/api/system/status', timeout=15))
    assert status['mode'] == 'LIVE' and not status.get('fixture')
    sql = "SELECT row_to_json(t) FROM telemetry t WHERE source='cloud_hardware' AND schema_version='2.0'"
    def identity(row, database=False):
        return (row['channel_id' if database else 'channelId'], row['entry_id' if database else 'entryId'], utc(row['cloud_created_at' if database else 'cloudCreatedAt']))
    columns = dict(zip(METRICS, ['temperature','humidity','co_max','ch4_max','distance_now','dev_max','status_worst','fault_any']))
    report = []
    def cloud(index):
        channel = env[f'THINGSPEAK_NODE{index}_CHANNEL_ID']
        key = env[f'THINGSPEAK_NODE{index}_READ_KEY']
        # URL never leaves this function or appears in a diagnostic message.
        url = 'https://api.thingspeak.com/channels/'+channel+'/feeds.json?'+urlencode(dict(api_key=key, results=8000, status='true'))
        try:
            return index, channel, json.load(urlopen(url, timeout=25))
        except Exception:
            raise RuntimeError('Read-only cloud request failed for node '+str(index)) from None
    with ThreadPoolExecutor(max_workers=2) as pool:
        clouds = list(pool.map(cloud, [1, 2]))
    # Freeze the cloud snapshot first. Allow bounded normal polling/commit latency,
    # rather than comparing a newer cloud snapshot with an older SQL snapshot.
    targets = {(channel, f['entry_id'], utc(f['created_at'])) for _,channel,payload in clouds for f in payload['feeds']}
    for attempt in range(16):
        database = [json.loads(line) for line in run('docker', 'exec', project+'-postgres-1', 'psql', '-U', 'agecm_revised', '-d', 'agecm_revised', '-At', '-c', sql).splitlines()]
        stored = {identity(row, True):row for row in database}
        if targets.issubset(stored):
            break
        if attempt < 15:
            time.sleep(2)
    assert targets.issubset(stored), 'Cloud observations are still absent from PostgreSQL after 30 seconds'
    for index, channel, payload in clouds:
        node = 'node_0'+str(index)
        history = json.load(urlopen(base+'/api/nodes/'+node+'/history?size=2000&start=1970-01-01T00%3A00%3A00Z', timeout=15))
        assert history['totalElements'] <= 2000, 'Use paginated comparison for larger histories'
        api = {identity(row):row for row in history['content']}
        for feed in payload['feeds']:
            ident = (channel, feed['entry_id'], utc(feed['created_at']))
            expected = Processor().process({key:feed.get(f'field{i}') for i,key in enumerate(METRICS, 1)})
            assert ident in stored and ident in api, f'Missing {node} entry {feed["entry_id"]} at {feed["created_at"]}'
            for key in METRICS:
                assert expected[key] == stored[ident][columns[key]] == api[ident][key], f'{node} entry {feed["entry_id"]}: {key} mismatch'
            assert expected['rawDistanceNow'] == stored[ident]['raw_distance_now'] == api[ident]['rawDistanceNow']
            assert utc(api[ident]['sampleAt']) == ident[2] and api[ident]['timestampBasis'] == 'CLOUD_CREATED_AT'
        if payload['feeds']:
            latest = max(payload['feeds'], key=lambda f:(utc(f['created_at']),f['entry_id']))
            report.append(dict(node=node,channel=channel,entriesCompared=len(payload['feeds']),latestEntry=latest['entry_id'],cloudCreatedAt=latest['created_at'],fields={f'field{i}':latest.get(f'field{i}') for i in range(1,9)}))
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--project',default='agecm_revised');parser.add_argument('--base',default='http://127.0.0.1:5173');args=parser.parse_args()
    verify(args.project,args.base.rstrip('/'))
