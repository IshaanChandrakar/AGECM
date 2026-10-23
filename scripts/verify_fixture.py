#!/usr/bin/env python3
"""Compare identical local cloud entries across mock -> processor -> PostgreSQL -> API."""
import argparse,json,subprocess
from pathlib import Path
from urllib.request import urlopen
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:5183');p.add_argument('--project',default='agecm_contract_v2_checks');args=p.parse_args()
compose=['docker','compose','-p',args.project,'-f','compose.yaml','-f','compose.mock.yaml']
def command(service,argv):
 return subprocess.check_output(compose+['exec','-T',service]+argv,cwd=ROOT,text=True)
def get(path):
 with urlopen(args.url+path,timeout=10) as r:return json.load(r)
status=get('/api/system/status');assert status['fixture'] is True and status['mode']=='LIVE'
keys=['temperature','humidity','coMax','ch4Max','distanceNow','devMax','statusWorst','faultAny']
for index,node in enumerate(status['nodes'],1):
 sample=node['latest'];assert sample is not None and sample['channelId'] in ('100','200')
 channel=int(sample['channelId']);entry=int(sample['entryId'])
 code="import json;from urllib.request import urlopen;print(json.dumps(json.load(urlopen('http://thingspeak-mock:8090/channels/%d/feeds.json?api_key=fixture-read-%d&results=100'))))"%(channel,index)
 cloud=json.loads(command('processing',['python','-c',code]));feed=next(f for f in cloud['feeds'] if f['entry_id']==entry)
 sql="SELECT json_build_object('temperature',temperature,'humidity',humidity,'coMax',co_max,'ch4Max',ch4_max,'distanceNow',distance_now,'devMax',dev_max,'statusWorst',status_worst,'faultAny',fault_any,'sampleAt',sample_at,'cloudCreatedAt',cloud_created_at) FROM telemetry WHERE source='cloud_hardware' AND channel_id='%d' AND entry_id=%d"%(channel,entry)
 stored=json.loads(command('postgres',['psql','-U','agecm_revised','-d','agecm_revised','-Atc',sql]))
 for field,key in enumerate(keys,1):assert sample[key]==stored[key]==float(feed['field'+str(field)]),(node['id'],key)
 assert datetime.fromisoformat(sample['sampleAt'].replace('Z','+00:00'))==datetime.fromisoformat(feed['created_at'])==datetime.fromisoformat(stored['sampleAt'])
 assert sample['timestampBasis']=='CLOUD_CREATED_AT' and sample['acquiredAt'] is None
 print(json.dumps({'node':node['id'],'channelId':channel,'entryId':entry,'sampleAt':sample['sampleAt'],'eight_values_equal_in_cloud_database_api':True}))
