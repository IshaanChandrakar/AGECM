import sys,os,json,unittest
from pathlib import Path
from unittest.mock import MagicMock,patch
from datetime import timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adapter import Adapter,Http
from processor import Processor,METRICS,utc
from write_test import validate_write

def feed(entry=1):
 return dict(entry_id=entry,created_at='2026-10-20T01:02:03Z',**{f'field{i}':str(i) for i in range(1,9)})
def channel(id=100):
 return dict(id=id,**dict(zip([f'field{i}' for i in range(1,9)],['Temp','Humidity','CO max','CH4 max','Dist Now','Dev max','Status worst','Fault any'])))
class PipelineTests(unittest.TestCase):
 def setUp(self):self.a=Adapter(http=MagicMock())
 def test_production_rejects_demo_or_development_secrets(self):
  with patch.dict(os.environ,{'AGECM_ENV':'production','AGECM_MODE':'DEMO'}):
   with self.assertRaisesRegex(ValueError,'LIVE'):Adapter(http=MagicMock())
  with patch.dict(os.environ,{'AGECM_ENV':'production','AGECM_MODE':'LIVE','INGESTION_TOKEN':'local-development-token'}):
   with self.assertRaisesRegex(ValueError,'private ingestion token'):Adapter(http=MagicMock())
 def test_production_accepts_configured_reader_and_rejects_mock(self):
  values={'AGECM_ENV':'production','AGECM_MODE':'LIVE','INGESTION_TOKEN':'private-fixture-token-with-32-characters','THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE2_CHANNEL_ID':'200','THINGSPEAK_NODE1_READ_KEY':'test-reader-1','THINGSPEAK_NODE2_READ_KEY':'test-reader-2','ALLOW_LOCAL_THINGSPEAK_MOCK':'false','THINGSPEAK_BASE_URL':'https://api.thingspeak.com'}
  with patch.dict(os.environ,values):self.assertEqual('LIVE',Adapter(http=MagicMock()).mode)
  with patch.dict(os.environ,{**values,'ALLOW_LOCAL_THINGSPEAK_MOCK':'true'}):
   with self.assertRaises(ValueError):Adapter(http=MagicMock())
 def test_exact_eight_field_mapping_independent_nodes(self):
  for node,id in [('node_01','100'),('node_02','200')]:
   r=self.a.normalize(node,id,feed());self.assertEqual(list(range(1,9)),[float(r[k]) for k in METRICS]);self.assertIsNone(r['acquiredAt']);self.assertEqual('cloud_hardware',r['source'])
  mapping=self.a.contract['nodes']['node_02'];mapping['temperature'],mapping['humidity']=mapping['humidity'],mapping['temperature'];self.assertEqual('2',self.a.normalize('node_02','200',feed())['temperature'])
 def test_distance_sentinel_preserves_raw_and_keeps_other_metrics(self):
  r=Processor().process(dict(distanceNow=-1,coMax=0,faultAny=1,statusWorst=2));self.assertIsNone(r['distanceNow']);self.assertEqual(-1,r['rawDistanceNow']);self.assertEqual(0,r['coMax']);self.assertEqual(2,r['statusWorst'])
 def test_zero_deviation_with_window_fault_is_retained_and_annotated(self):
  r=Processor().process(dict(distanceNow=0,devMax=0,faultAny=1,statusWorst=0));self.assertEqual(0,r['devMax']);self.assertEqual(0,r['distanceNow']);self.assertIn('failed distance read',json.loads(r['fieldIssues'])['devMax'])
 def test_mixed_window_status_is_not_reclassified_from_latest_temperature(self):
  r=Processor().process(dict(temperature=22,humidity=45,coMax=0,ch4Max=0,distanceNow=100,devMax=0,statusWorst=2,faultAny=0));self.assertEqual(2,r['statusWorst']);self.assertEqual(22,r['temperature'])
 def test_unmapped_status_is_invalid(self):
  self.assertIsNone(Processor().process(dict(statusWorst=3))['statusWorst'])
 def test_zero_null_invalid_partial_values(self):
  raw={k:0 for k in METRICS};raw['humidity']=None;raw['coMax']='nan';raw['ch4Max']='inf';r=Processor().process(raw);self.assertEqual(0,r['temperature']);self.assertEqual(0,r['faultAny']);self.assertIsNone(r['humidity']);self.assertIsNone(r['coMax']);self.assertIsNone(r['ch4Max']);self.assertIn('coMax',json.loads(r['fieldIssues']))
 def test_binary_semantics_are_not_invented(self):
  r=Processor().process({k:0 for k in METRICS});self.assertNotIn('state',r);self.assertNotIn('health',r);self.assertNotIn('faultLabel',r)
 def test_discrete_fractional_and_nonbinary_codes_invalid(self):
  r=Processor().process(dict(statusWorst=1.5,faultAny=2));self.assertIsNone(r['statusWorst']);self.assertIsNone(r['faultAny'])
 def test_no_old_status_json_boot_or_sequence_requirement(self):
  f=feed();f['status']='firmware running';r=self.a.normalize('node_01','100',f);self.assertIsNone(r['bootId']);self.assertIsNone(r['sequence']);self.assertEqual('7',r['statusWorst']);self.assertEqual('8',r['faultAny'])
 def test_timezone_and_true_acquisition_metadata(self):
  f=feed();f['status']=json.dumps({'acquiredAt':'2026-10-20T06:32:01+05:30'});r=self.a.normalize('node_01','100',f);self.assertEqual('2026-10-20T01:02:01+00:00',r['acquiredAt']);self.assertEqual(timezone.utc,utc(r['acquiredAt']).tzinfo)
  with self.assertRaises(ValueError):utc('2026-10-20T01:02:01')
 def test_mapping_label_and_channel_identity_checks(self):
  self.a.verify_channel('node_01',{'channel':channel()},'100')
  with self.assertRaises(ValueError):self.a.verify_channel('node_02',{'channel':channel()},'200')
  c=channel();c['field1']='Tilt';
  with self.assertRaises(ValueError):self.a.verify_channel('node_01',{'channel':c},'100')
 def test_maximum_values_pass_through_without_computation(self):
  raw=dict(coMax=22.2,ch4Max=18.4,devMax=7.3);r=Processor().process(raw)
  for k,v in raw.items():self.assertEqual(v,r[k])
 def poll_setup(self,feeds,cursor=0):
  self.a.cursors['node_01']=cursor;self.a.http.request.return_value={'channel':channel(),'feeds':feeds};self.a.report=MagicMock()
 def test_committed_cursor_duplicates_and_out_of_order_feeds(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.poll_setup([feed(3),feed(1),feed(2)],1);self.a.deliver=MagicMock(return_value={'accepted':True});self.a.poll_node('node_01');self.assertEqual([2,3],[c.args[0]['entryId'] for c in self.a.deliver.call_args_list]);self.assertEqual(3,self.a.cursors['node_01'])
 def test_failed_backend_does_not_advance_cursor(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.poll_setup([feed()]);self.a.deliver=MagicMock(side_effect=RuntimeError('Backend unavailable'));self.a.poll_node('node_01');self.assertEqual(0,self.a.cursors['node_01'])
 def test_reused_entry_ids_with_newer_cloud_time_are_recovered_once(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   rows=[feed(1),feed(2)];rows[1]['created_at']='2026-10-20T01:02:23Z'
   self.poll_setup(rows,36);self.a.watermarks['node_01']=utc('2026-10-20T01:00:00Z');self.a.deliver=MagicMock(return_value={'accepted':True})
   self.a.poll_node('node_01');self.assertEqual([1,2],[c.args[0]['entryId'] for c in self.a.deliver.call_args_list]);self.assertEqual(2,self.a.cursors['node_01']);self.assertEqual(utc(rows[1]['created_at']),self.a.watermarks['node_01'])
   self.a.deliver.reset_mock();self.a.poll_node('node_01');self.a.deliver.assert_not_called()
 def test_fresh_database_bootstraps_readable_history_without_inventing_entry_one(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.poll_setup([feed(9000),feed(9001)],0);self.a.deliver=MagicMock();self.a.poll_node('node_01');self.assertEqual([9000,9001],[c.args[0]['entryId'] for c in self.a.deliver.call_args_list]);self.assertEqual(9001,self.a.cursors['node_01']);self.assertEqual(1,self.a.report.call_args.args[3]);self.assertIn('results=8000',self.a.http.request.call_args.args[1])
 def test_old_cloud_snapshot_does_not_reset_cursor(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.poll_setup([feed(1)],36);self.a.watermarks['node_01']=utc('2026-10-20T02:00:00Z');self.a.deliver=MagicMock();self.a.poll_node('node_01');self.a.deliver.assert_not_called();self.assertEqual(36,self.a.cursors['node_01'])
 def test_reset_history_beyond_readable_window_reports_gap_without_skipping(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.poll_setup([feed(9000)],10000);self.a.watermarks['node_01']=utc('2026-10-20T01:00:00Z');self.a.deliver=MagicMock();self.a.poll_node('node_01');self.a.deliver.assert_not_called();self.assertEqual(10000,self.a.cursors['node_01']);self.assertEqual('GAP',self.a.report.call_args.args[1]);self.assertIn('results=8000',self.a.http.request.call_args.args[1])
 def test_failed_recovery_keeps_durable_watermark_and_retries(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.poll_setup([feed(1)],36);self.a.watermarks['node_01']=utc('2026-10-20T01:00:00Z');self.a.deliver=MagicMock(side_effect=RuntimeError('Backend unavailable'));self.a.poll_node('node_01');self.assertEqual(36,self.a.cursors['node_01']);self.assertEqual(utc('2026-10-20T01:00:00Z'),self.a.watermarks['node_01'])
 def test_failure_of_one_node_does_not_prevent_other_node_poll(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private','THINGSPEAK_NODE2_CHANNEL_ID':'200','THINGSPEAK_NODE2_READ_KEY':'private2'}):
   self.a.cursors={'node_01':0,'node_02':0};self.a.report=MagicMock();self.a.deliver=MagicMock()
   self.a.http.request.side_effect=[RuntimeError('Cloud unavailable'),{'channel':channel(200),'feeds':[feed(1)]},{'channel':channel(200),'feeds':[feed(1)]}]
   self.a.poll_node('node_01');self.a.poll_node('node_02');self.assertEqual('node_02',self.a.deliver.call_args.args[0]['nodeId']);self.assertEqual(1,self.a.cursors['node_02'])
 def test_restart_reads_persistent_cursor(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.a.backend=MagicMock(return_value={'lastEntryId':4,'mode':'LIVE'});self.a.http.request.return_value={'channel':channel(),'feeds':[feed(4),feed(5)]};self.a.report=MagicMock();self.a.deliver=MagicMock();self.a.poll_node('node_01');self.assertEqual(5,self.a.cursors['node_01']);self.assertEqual(1,self.a.deliver.call_count)
 def test_empty_cloud_does_not_fabricate_data(self):
  with patch.dict(os.environ,{'THINGSPEAK_NODE1_CHANNEL_ID':'100','THINGSPEAK_NODE1_READ_KEY':'private'}):
   self.poll_setup([]);self.a.deliver=MagicMock();self.a.poll_node('node_01');self.a.deliver.assert_not_called();self.a.report.assert_called_with('node_01','HEALTHY')
 def test_timeout_redacts_authentication_url(self):
  with patch('adapter.urlopen',side_effect=TimeoutError),patch('adapter.time.sleep'):
   with self.assertRaises(RuntimeError) as ctx:Http(retries=1).request('GET','https://api.thingspeak.com/?api_key=private')
   self.assertNotIn('private',str(ctx.exception))
 def test_wrong_read_key_returns_authentication_failure(self):
  from urllib.error import HTTPError
  with patch('adapter.urlopen',side_effect=HTTPError('secret-url',401,'Unauthorized',{},None)),patch('adapter.time.sleep'):
   with self.assertRaisesRegex(RuntimeError,'401'):Http(retries=0).request('GET','https://example.invalid/?api_key=private')
 def test_write_acknowledgment_is_positive_and_channel_specific(self):
  self.assertEqual(2,validate_write({'entry_id':2,'channel_id':55},55))
  for result in [0,{},dict(entry_id=0,channel_id=55),dict(entry_id=3,channel_id=56)]:
   with self.assertRaises(ValueError):validate_write(result,55)
if __name__=='__main__':unittest.main()
