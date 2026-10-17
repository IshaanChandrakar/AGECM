import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from processor import Processor
from adapter import Adapter, Http
from write_test import validate_write

BASE=datetime(2026,1,1,tzinfo=timezone.utc)
def raw(i,rate=.05,boot="b",node="node_01"):
    return dict(nodeId=node,source="demo",schemaVersion="1.0",bootId=boot,sequence=i,
                acquiredAt=(BASE+timedelta(seconds=i*2)).isoformat(),tilt=i*2*rate,
                displacement=i*.2,vibration=.02,qualityFlags=0,calibrated=True,reportIntervalSeconds=2)
def feed(i=1):
    return dict(entry_id=i,created_at="2026-01-01T00:00:00Z",field1="1.2",field2="2.3",field3=".02",
                field4=None,field5=None,field6="0",field7=str(i),field8="boot",
                status='{"schema":"1.0","acquiredAt":"2026-01-01T00:00:00Z","calibrated":true,"sampleIntervalMs":100,"reportIntervalSeconds":30}')

class ProcessingTests(unittest.TestCase):
    def test_actual_elapsed_time_and_consecutive_warning(self):
        p=Processor();values=[p.process(raw(i)) for i in range(15)]
        self.assertIsNone(values[10]["tiltRate"]);self.assertAlmostEqual(.05,values[11]["tiltRate"])
        self.assertEqual("WARNING",values[-1]["state"])
    def test_negative_movement_escalates_and_critical_is_not_instant(self):
        p=Processor();values=[p.process(raw(i,-.2)) for i in range(15)]
        self.assertNotEqual("CRITICAL",values[11]["state"]);self.assertEqual("CRITICAL",values[-1]["state"])
    def test_missing_nan_and_boot_change_reset_feature_window(self):
        p=Processor()
        for i in range(15):p.process(raw(i))
        r=raw(15);r["tilt"]=float("nan");self.assertEqual("INVALID_SENSOR",p.process(r)["health"])
        self.assertIsNone(p.process(raw(16))["tiltRate"])
        self.assertFalse(p.process(raw(17,boot="reboot"))["featureReady"])
    def test_firmware_feature_owner_does_not_rederive(self):
        p=Processor("firmware");r=raw(0);r.update(tiltRate=.003,displacementVelocity=.004)
        self.assertEqual(.003,p.process(r)["tiltRate"])
    def test_sparse_gap_restarts_readiness(self):
        p=Processor()
        for i in range(15):p.process(raw(i))
        self.assertFalse(p.process(raw(200))["featureReady"])

class CloudTests(unittest.TestCase):
    def setUp(self):self.a=Adapter(http=MagicMock())
    def test_parses_strings_nulls_and_metadata(self):
        f=feed();r=self.a.normalize("node_01","123",f);self.assertEqual(1.2,r["tilt"]);self.assertIsNone(r["tiltRate"]);self.assertEqual("cloud_hardware",r["source"])
        f["field1"]=None;self.assertIsNone(self.a.normalize("node_01","123",f)["tilt"])
    def test_bad_identity_and_schema_rejected(self):
        for key,value in [("entry_id",0),("field7","1.5"),("field8",None),("status","{}")]:
            f=feed();f[key]=value
            with self.assertRaises(ValueError):self.a.normalize("node_01","123",f)
    def test_cursor_only_advances_after_backend_acceptance(self):
        with patch.dict(os.environ,{"THINGSPEAK_NODE1_CHANNEL_ID":"123","THINGSPEAK_NODE1_READ_KEY":"secret"}):
            self.a.cursors["node_01"]=0;self.a.http.request.return_value={"feeds":[feed()]}
            self.a.deliver=MagicMock(side_effect=RuntimeError("downstream unavailable"));self.a.report=MagicMock()
            self.a.poll_node("node_01");self.assertEqual(0,self.a.cursors["node_01"]);self.a.report.assert_called_with("node_01","ERROR","downstream unavailable")
    def test_duplicate_cloud_entries_are_skipped(self):
        with patch.dict(os.environ,{"THINGSPEAK_NODE1_CHANNEL_ID":"123","THINGSPEAK_NODE1_READ_KEY":"secret"}):
            self.a.cursors["node_01"]=1;self.a.http.request.return_value={"feeds":[feed()]};self.a.deliver=MagicMock();self.a.report=MagicMock();self.a.poll_node("node_01");self.a.deliver.assert_not_called()
    def test_restart_loads_committed_backend_cursor(self):
        with patch.dict(os.environ,{"THINGSPEAK_NODE1_CHANNEL_ID":"123","THINGSPEAK_NODE1_READ_KEY":"secret"}):
            self.a.backend=MagicMock(return_value={"lastEntryId":7,"mode":"LIVE"});self.a.http.request.return_value={"feeds":[feed(7),feed(8)]};self.a.deliver=MagicMock(return_value={"accepted":True});self.a.report=MagicMock();self.a.poll_node("node_01");self.assertEqual(8,self.a.cursors["node_01"]);self.assertEqual(1,self.a.deliver.call_count)
    def test_irrecoverable_gap_does_not_silently_advance_cursor(self):
        with patch.dict(os.environ,{"THINGSPEAK_NODE1_CHANNEL_ID":"123","THINGSPEAK_NODE1_READ_KEY":"secret"}):
            self.a.cursors["node_01"]=1;self.a.http.request.return_value={"feeds":[feed(200)]};self.a.deliver=MagicMock();self.a.report=MagicMock();self.a.poll_node("node_01");self.assertEqual(1,self.a.cursors["node_01"]);self.a.deliver.assert_not_called();self.assertEqual("GAP",self.a.report.call_args.args[1])
    def test_empty_channel_is_successful_read_without_fabrication(self):
        with patch.dict(os.environ,{"THINGSPEAK_NODE1_CHANNEL_ID":"123","THINGSPEAK_NODE1_READ_KEY":"secret"}):
            self.a.cursors["node_01"]=0;self.a.http.request.return_value={"feeds":[]};self.a.deliver=MagicMock();self.a.report=MagicMock();self.a.poll_node("node_01");self.a.deliver.assert_not_called();self.a.report.assert_called_with("node_01","HEALTHY")
    def test_failed_delivery_rolls_back_processing_window(self):
        self.a.backend=MagicMock(side_effect=RuntimeError("not accepted"))
        with self.assertRaises(RuntimeError):self.a.deliver(raw(0))
        self.assertEqual({},self.a.processors["node_01"].sessions)
    def test_positive_entry_identity_required_for_writes(self):
        self.assertEqual(2,validate_write(dict(entry_id=2,channel_id=55),55))
        for response in [0,None,{},dict(entry_id=0,channel_id=55),dict(entry_id=2,channel_id=56)]:
            with self.assertRaises(ValueError):validate_write(response,55)
    def test_network_timeout_retries_without_exposing_key(self):
        with patch("adapter.urlopen",side_effect=TimeoutError),patch("adapter.time.sleep"):
            with self.assertRaisesRegex(RuntimeError,"TimeoutError") as ctx:Http(retries=1).request("GET","https://api.thingspeak.com/?api_key=secret")
            self.assertNotIn("secret",str(ctx.exception))
    def test_unconfigured_node_reports_explicitly(self):
        with patch.dict(os.environ,{"THINGSPEAK_NODE2_CHANNEL_ID":"","THINGSPEAK_NODE2_READ_KEY":""}):
            self.a.report=MagicMock();self.a.poll_node("node_02");self.assertEqual("NOT_CONFIGURED",self.a.report.call_args.args[1])

if __name__=="__main__":unittest.main()
