package in.agecm;
import org.junit.jupiter.api.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ActiveProfiles;
import java.time.Instant;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(properties={"agecm.mode=LIVE","agecm.channel1=100","agecm.channel2=200","spring.datasource.url=jdbc:h2:mem:live;MODE=PostgreSQL;DB_CLOSE_DELAY=-1"}) @ActiveProfiles("test")
class LiveModeIntegrationTest {
 @Autowired MonitoringService service; @Autowired TelemetryRepository records; @Autowired AlertRepository episodes; @Autowired IngestionRepository cursors;
 @BeforeEach void reset(){episodes.deleteAll();records.deleteAll();for(IngestionState c:cursors.findAll()){c.lastEntryId=0;c.lastCloudCreatedAt=null;cursors.save(c);}}
 TelemetryInput cloud(String node,String channel,long entry){TelemetryInput t=new TelemetryInput();t.nodeId=node;t.source="cloud_hardware";t.schemaVersion="2.0";t.channelId=channel;t.entryId=entry;t.cloudCreatedAt=Instant.now();t.temperature=0.0;t.humidity=0.0;t.coMax=0.0;t.ch4Max=0.0;t.distanceNow=0.0;t.devMax=0.0;t.statusWorst=0;t.faultAny=0;return t;}
 @Test void cloudTimestampFallbackDuplicatesRestartAndIsolation(){TelemetryInput t=cloud("node_01","100",9);service.report("node_01","HEALTHY",null,0);service.ingest(t);service.ingest(t);assertEquals(1,records.count());Telemetry stored=records.findAll().get(0);assertNull(stored.acquiredAt);assertNull(stored.bootId);assertNull(stored.sequence);assertEquals("CLOUD_CREATED_AT",stored.timestampBasis);assertEquals(t.cloudCreatedAt,stored.sampleAt);assertEquals(9L,service.cursor("node_01").get("lastEntryId"));assertThrows(Exception.class,()->service.ingest(cloud("node_02","100",10)));service.ingest(cloud("node_02","200",9));assertEquals(2,records.count());}
 @Test void acquisitionTimestampIsPreservedAndFailureUnavailable(){TelemetryInput t=cloud("node_01","100",10);t.acquiredAt=Instant.now().minusSeconds(5);service.ingest(t);Telemetry stored=records.findAll().get(0);assertEquals("ACQUISITION_UTC",stored.timestampBasis);assertEquals(t.acquiredAt,stored.sampleAt);service.report("node_01","ERROR","Authentication failure HTTP 401",0);assertEquals("CLOUD_ERROR",service.node("node_01").get("health"));}
 @Test void changingConfiguredChannelClearsBothCursorComponents(){IngestionState c=cursors.findById("node_01").orElseThrow();c.channelId="999";c.schemaVersion="2.0";c.lastEntryId=99;c.lastCloudCreatedAt=Instant.now();cursors.save(c);service.report("node_01","HEALTHY",null,0);assertEquals(0L,service.cursor("node_01").get("lastEntryId"));assertNull(service.cursor("node_01").get("lastCloudCreatedAt"));}
 @Test void channelClearingRetainsReusedIdsWithoutDuplicatesOrCursorRewind(){
  TelemetryInput old=cloud("node_01","100",1);old.cloudCreatedAt=Instant.now().minusSeconds(300);old.temperature=null;service.ingest(old);
  TelemetryInput last=cloud("node_01","100",36);last.cloudCreatedAt=Instant.now().minusSeconds(200);service.ingest(last);
  TelemetryInput fresh=cloud("node_01","100",1);fresh.cloudCreatedAt=Instant.now().minusSeconds(100);fresh.temperature=23.4;service.ingest(fresh);service.ingest(fresh);
  assertEquals(3,records.count());assertEquals(1L,service.cursor("node_01").get("lastEntryId"));assertEquals(fresh.cloudCreatedAt,service.cursor("node_01").get("lastCloudCreatedAt"));assertEquals(23.4,((Telemetry)service.node("node_01").get("latest")).temperature);
  service.ingest(last);assertEquals(1L,service.cursor("node_01").get("lastEntryId"));assertEquals(3,records.count());
 }
}
