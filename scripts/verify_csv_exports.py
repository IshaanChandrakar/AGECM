"""Read-only comparison of downloaded LIVE CSV files, PostgreSQL and ThingSpeak."""
import argparse,csv,json,subprocess,sys
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'processing'))
from processor import METRICS,Processor,utc

def verify(files,project):
 sql="SELECT row_to_json(t) FROM telemetry t WHERE source='cloud_hardware' AND schema_version='2.0'"
 records=[json.loads(line) for line in subprocess.check_output(['docker','exec',project+'-postgres-1','psql','-U','agecm_revised','-d','agecm_revised','-At','-c',sql]).splitlines()]
 byid={str(r['id']):r for r in records};columns=dict(zip(METRICS,['temperature','humidity','co_max','ch4_max','distance_now','dev_max','status_worst','fault_any']));columns['rawDistanceNow']='raw_distance_now';parsed=[]
 for file in files:
  with Path(file).open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
  previous=None;identities=set()
  for row in rows:
   stored=byid[row['id']];assert row['source']==stored['source']=='cloud_hardware';assert row['schemaVersion']==stored['schema_version']=='2.0'
   for key,column in columns.items():assert (None if row[key]=='' else float(row[key]))==stored[column],f'Measurement mismatch: {key}, record {row["id"]}'
   for key,column in [('sampleAt','sample_at'),('cloudCreatedAt','cloud_created_at'),('receivedAt','received_at')]:assert utc(row[key])==utc(stored[column])
   assert row['channelId']==stored['channel_id'] and int(row['entryId'])==stored['entry_id'];assert row['fieldIssues']==(stored['field_issues'] or '')
   order=(utc(row['sampleAt']),int(row['id']));assert previous is None or previous<order;previous=order
   identity=(row['channelId'],row['entryId'],utc(row['cloudCreatedAt']));assert identity not in identities;identities.add(identity)
  parsed.append((rows,identities));print(json.dumps({'file':str(file),'rows':len(rows),'allValuesMatchPostgres':True}))
 if len(parsed)>1:
  added=parsed[-1][1]-parsed[0][1];assert added,'No new observation between the downloads'
  c=json.loads(subprocess.check_output(['docker','inspect',project+'-processing-1']))[0];env=dict(item.split('=',1) for item in c['Config']['Env'] if '=' in item)
  latest=max(added,key=lambda identity:identity[2]);channel,entry,created=latest;index=next(i for i in [1,2] if env[f'THINGSPEAK_NODE{i}_CHANNEL_ID']==channel)
  try:feed=json.load(urlopen('https://api.thingspeak.com/channels/'+channel+'/feeds/'+entry+'.json?'+urlencode({'api_key':env[f'THINGSPEAK_NODE{index}_READ_KEY']}),timeout=25))
  except Exception:raise RuntimeError('Read-only cloud comparison unavailable; no authentication URL logged') from None
  assert utc(feed['created_at'])==created,'Channel entry was reused again after the export'
  normalized=Processor().process({key:feed.get('field'+str(i)) for i,key in enumerate(METRICS,1)});row=next(r for r in parsed[-1][0] if (r['channelId'],r['entryId'],utc(r['cloudCreatedAt']))==latest)
  for key in METRICS:assert (None if row[key]=='' else float(row[key]))==normalized[key],key
  print(json.dumps({'newIdentities':len(added),'verifiedCloudEntry':{'channelId':channel,'entryId':int(entry),'cloudCreatedAt':created.isoformat()},'allEightFieldsMatch':True}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('files',nargs='+');parser.add_argument('--project',default='agecm_revised');args=parser.parse_args();verify(args.files,args.project)
