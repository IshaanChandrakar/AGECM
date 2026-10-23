package in.agecm;
import org.junit.jupiter.api.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ActiveProfiles;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(properties={"spring.datasource.url=jdbc:h2:mem:codes;MODE=PostgreSQL;DB_CLOSE_DELAY=-1","agecm.contract-path=src/test/resources/reversed-contract.json"}) @ActiveProfiles("test")
class ConfirmedSemanticsTest {
 @Autowired MonitoringService service; @Autowired TelemetryRepository records; @Autowired AlertRepository episodes; @Autowired ObjectMapper mapper;
 @Test void explicitTestConventionCanReverseBinaryMeaningWithoutAssumptions()throws Exception {
  // Deliberately artificial fixture semantics, not a statement about physical firmware.

  TelemetryInput t=new TelemetryInput();t.nodeId="node_01";t.source="demo";t.schemaVersion="2.0";t.bootId="fixture";t.sequence=1L;t.acquiredAt=Instant.now();t.temperature=1.;t.humidity=2.;t.coMax=0.;t.ch4Max=0.;t.distanceNow=3.;t.devMax=4.;t.statusWorst=9;t.faultAny=0;
  service.ingest(t);assertEquals("WINDOW_FAULT",service.node("node_01").get("health"));assertTrue(episodes.findAll().stream().anyMatch(a->a.condition.equals("FAULT_REPORTED")));assertTrue(episodes.findAll().stream().anyMatch(a->a.condition.equals("FIRMWARE_STATUS")&&a.severity.equals("Fixture elevated")));
  t.sequence=2L;t.acquiredAt=Instant.now();t.faultAny=1;service.ingest(t);assertEquals("AVAILABLE",service.node("node_01").get("health"));assertTrue(episodes.findAll().stream().filter(a->a.condition.equals("FAULT_REPORTED")).allMatch(a->a.resolvedAt!=null));
 }
}
