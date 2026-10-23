package in.agecm;
import org.junit.jupiter.api.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.web.servlet.MockMvc;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest @AutoConfigureMockMvc @ActiveProfiles("test")
class MonitoringIntegrationTest {
 @Autowired MockMvc mvc; @Autowired ObjectMapper mapper; @Autowired MonitoringService service;
 @Autowired TelemetryRepository records; @Autowired AlertRepository episodes;
 @BeforeEach void reset(){episodes.deleteAll();records.deleteAll();}
 TelemetryInput reading(long seq){TelemetryInput t=new TelemetryInput();t.nodeId="node_01";t.source="demo";t.schemaVersion="2.0";t.bootId="test-session";t.sequence=seq;t.acquiredAt=Instant.now();t.temperature=25.0;t.humidity=50.0;t.coMax=0.0;t.ch4Max=4.0;t.distanceNow=100.0;t.devMax=.5;t.statusWorst=0;t.faultAny=0;return t;}
 void send(TelemetryInput t)throws Exception{mvc.perform(post("/api/telemetry").header("X-Ingestion-Token","test-token").contentType("application/json").content(mapper.writeValueAsBytes(t))).andExpect(status().isOk());}
 @Test void exactNodesAndUnverifiedCentral()throws Exception{mvc.perform(get("/api/system/status")).andExpect(status().isOk()).andExpect(jsonPath("$.nodes.length()").value(2)).andExpect(jsonPath("$.central.status").value("UNVERIFIED")).andExpect(jsonPath("$.contract.metrics.length()").value(8));}
 @Test void negativeDistancePreservesSentinelWithoutHidingOtherValues()throws Exception{TelemetryInput t=reading(1);t.distanceNow=-1.0;send(t);Telemetry r=records.findAll().get(0);assertNull(r.distanceNow);assertEquals(-1.0,r.rawDistanceNow);assertEquals(0.0,r.coMax);assertTrue(r.fieldIssues.contains("sentinel"));}
 @Test void protectsIngestion()throws Exception{mvc.perform(post("/api/telemetry").contentType("application/json").content(mapper.writeValueAsBytes(reading(1)))).andExpect(status().isUnauthorized());}
 @Test void zeroAndPartialDataStayDistinct()throws Exception{TelemetryInput t=reading(1);t.humidity=null;send(t);Telemetry r=records.findAll().get(0);assertEquals(0,r.coMax);assertNull(r.humidity);assertEquals("PARTIAL_DATA",service.node(t.nodeId).get("health"));}
 @Test void unknownCodesNeverBecomeHealthy()throws Exception{send(reading(1));assertEquals("SEMANTICS_UNVERIFIED",service.node("node_01").get("health"));assertTrue(service.node("node_01").get("faultLabel").toString().contains("unconfirmed"));assertEquals(0,episodes.count());}
 @Test void deduplicatesAndChronologicalHistoryProtectsLatest()throws Exception{TelemetryInput t=reading(2);send(t);send(t);TelemetryInput old=reading(1);old.acquiredAt=Instant.now().minusSeconds(40);old.temperature=99.0;send(old);assertEquals(2,records.count());assertEquals(25.0,((Telemetry)service.node("node_01").get("latest")).temperature);mvc.perform(get("/api/telemetry/history?size=1")).andExpect(jsonPath("$.totalElements").value(2));}
 @Test void rejectsWrongModeSchemaAndFractionalCodes()throws Exception{TelemetryInput t=reading(1);t.source="cloud_hardware";mvc.perform(post("/api/telemetry").header("X-Ingestion-Token","test-token").contentType("application/json").content(mapper.writeValueAsBytes(t))).andExpect(status().isBadRequest());t.source="demo";t.schemaVersion="1.0";mvc.perform(post("/api/telemetry").header("X-Ingestion-Token","test-token").contentType("application/json").content(mapper.writeValueAsBytes(t))).andExpect(status().isBadRequest());t.schemaVersion="2.0";String body=mapper.writeValueAsString(t).replace("\"faultAny\":0","\"faultAny\":0.5");mvc.perform(post("/api/telemetry").header("X-Ingestion-Token","test-token").contentType("application/json").content(body)).andExpect(status().isBadRequest());}
 @Test void staleAndBackendCloudFailureAreHealthEpisodes()throws Exception{TelemetryInput t=reading(1);t.acquiredAt=Instant.now().minusSeconds(100);send(t);assertEquals("STALE",service.node("node_01").get("health"));service.report("node_01","ERROR","Mock cloud outage",0);assertEquals("CLOUD_ERROR",service.node("node_01").get("health"));service.report("node_01","DEMO",null,0);}
}
