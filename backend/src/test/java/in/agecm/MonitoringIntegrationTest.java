package in.agecm;
import org.junit.jupiter.api.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.web.servlet.MockMvc;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest @AutoConfigureMockMvc @ActiveProfiles("test")
class MonitoringIntegrationTest {
 @Autowired MockMvc mvc; @Autowired ObjectMapper mapper; @Autowired MonitoringService service;
 @Autowired TelemetryRepository records; @Autowired AlertRepository alertRecords;
 @BeforeEach void reset(){alertRecords.deleteAll();records.deleteAll();}
 TelemetryInput reading(String boot,long seq,String state){TelemetryInput t=new TelemetryInput();t.nodeId="node_01";t.source="demo";t.schemaVersion="1.0";t.bootId=boot;t.sequence=seq;t.acquiredAt=Instant.now();t.tilt=1.0;t.displacement=2.0;t.vibration=.03;t.tiltRate=.05;t.displacementVelocity=.001;t.qualityFlags=0;t.calibrated=true;t.featureReady=true;t.sampleIntervalMs=2000;t.reportIntervalSeconds=2;t.ruleVersion="lab-rule-v1";t.state=state;t.health="HEALTHY";return t;}
 void send(TelemetryInput t)throws Exception{mvc.perform(post("/api/telemetry").header("X-Ingestion-Token","test-token").contentType("application/json").content(mapper.writeValueAsBytes(t))).andExpect(status().isOk());}
 @Test void exactlyTwoSensingNodesAndUnverifiedCentral()throws Exception{mvc.perform(get("/api/system/status")).andExpect(status().isOk()).andExpect(jsonPath("$.nodes.length()").value(2)).andExpect(jsonPath("$.central.status").value("UNVERIFIED"));}
 @Test void ingestionRequiresToken()throws Exception{mvc.perform(post("/api/telemetry").contentType("application/json").content(mapper.writeValueAsBytes(reading("auth",1,"NORMAL")))).andExpect(status().isUnauthorized());assertEquals(0,records.count());}
 @Test void duplicatePacketsAndRepeatedWarningProduceOneEpisode()throws Exception{TelemetryInput t=reading("dedup",1,"WARNING");send(t);send(t);send(reading("dedup",2,"WARNING"));assertEquals(2,records.count());assertEquals(1,alertRecords.count());send(reading("dedup",3,"NORMAL"));assertNotNull(alertRecords.findAll().get(0).resolvedAt);}
 @Test void backfillCannotReplaceNewerSnapshot()throws Exception{send(reading("order",2,"NORMAL"));TelemetryInput old=reading("order",1,"CRITICAL");old.acquiredAt=Instant.now().minusSeconds(40);send(old);assertEquals("NORMAL",service.node("node_01").get("state"));assertEquals(0,alertRecords.count());}
 @Test void invalidMissingAndStaleMeasurementsAreUnavailable()throws Exception{TelemetryInput t=reading("invalid",1,"NORMAL");t.tilt=null;send(t);assertEquals("INVALID_SENSOR",service.node("node_01").get("health"));assertEquals("UNAVAILABLE",service.node("node_01").get("state"));TelemetryInput stale=reading("stale",2,"NORMAL");stale.nodeId="node_02";stale.acquiredAt=Instant.now().minusSeconds(100);send(stale);assertEquals("STALE",service.node("node_02").get("health"));assertEquals("UNAVAILABLE",service.node("node_02").get("state"));}
 @Test void demoRejectsCloudSourceAndThirdSensingNode()throws Exception{TelemetryInput t=reading("wrong",1,"NORMAL");t.source="cloud_hardware";mvc.perform(post("/api/telemetry").header("X-Ingestion-Token","test-token").contentType("application/json").content(mapper.writeValueAsBytes(t))).andExpect(status().isBadRequest());t.source="demo";t.nodeId="node_03";mvc.perform(post("/api/telemetry").header("X-Ingestion-Token","test-token").contentType("application/json").content(mapper.writeValueAsBytes(t))).andExpect(status().isBadRequest());}
 @Test void historyIsPaginatedAndSourceScoped()throws Exception{send(reading("history",1,"NORMAL"));send(reading("history",2,"NORMAL"));mvc.perform(get("/api/telemetry/history?size=1")).andExpect(status().isOk()).andExpect(jsonPath("$.content.length()").value(1)).andExpect(jsonPath("$.totalElements").value(2));}
}
