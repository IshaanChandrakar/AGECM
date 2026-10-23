package in.agecm;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.ObjectMapper;
import static org.junit.jupiter.api.Assertions.*;
class FirmwareContractTest {
 @Test void confirmedFirmwareCodesAndUnitsAreExplicit()throws Exception{
  SensorContract c=new SensorContract(new ObjectMapper(),"");assertTrue(c.confirmed());assertEquals("DANGER",c.statusLabel(2));assertEquals(0,c.status(0).path("severity").asInt());assertNull(c.status(3));assertFalse(c.fault(0).path("isFault").asBoolean());assertTrue(c.fault(1).path("isFault").asBoolean());assertEquals("°C",c.document().path("metrics").get(0).path("unit").asText());assertEquals("field8",c.document().path("nodes").path("node_02").path("faultAny").asText());
 }
}
