package in.agecm;
import org.junit.jupiter.api.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ActiveProfiles;
import java.time.Instant;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(properties={"agecm.mode=LIVE","agecm.channel1=100","agecm.channel2=200","spring.datasource.url=jdbc:h2:mem:live;MODE=PostgreSQL;DB_CLOSE_DELAY=-1"}) @ActiveProfiles("test")
class LiveModeIntegrationTest {
 @Autowired MonitoringService service;
 @Autowired TelemetryRepository records; @Autowired AlertRepository alertRecords; @Autowired IngestionRepository cursors;
 @BeforeEach void reset(){alertRecords.deleteAll();records.deleteAll();}
 @Test void cloudDeduplicationCursorAndPartialFailure(){TelemetryInput t=new TelemetryInput();t.nodeId="node_01";t.source="cloud_hardware";t.schemaVersion="1.0";t.bootId="physical-boot";t.sequence=1L;t.channelId="100";t.entryId=9L;t.acquiredAt=Instant.now();t.cloudCreatedAt=Instant.now();t.tilt=1.0;t.displacement=.1;t.vibration=.02;t.tiltRate=.001;t.displacementVelocity=.001;t.qualityFlags=0;t.calibrated=true;t.featureReady=true;t.ruleVersion="lab-rule-v1";t.state="NORMAL";t.health="HEALTHY";service.report("node_01","HEALTHY",null,0);service.ingest(t);service.ingest(t);assertEquals(1,records.count());assertEquals(9,cursors.findById("node_01").orElseThrow().lastEntryId);t.entryId=10L;service.ingest(t);assertEquals(1,records.count());assertEquals(10,cursors.findById("node_01").orElseThrow().lastEntryId);service.report("node_01","ERROR","Cloud timeout",0);assertEquals("CLOUD_ERROR",service.node("node_01").get("health"));assertEquals("UNAVAILABLE",service.node("node_01").get("state"));assertNotEquals("NORMAL",service.node("node_02").get("state"));}
}
