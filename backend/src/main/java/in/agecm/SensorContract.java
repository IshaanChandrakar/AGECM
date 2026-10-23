package in.agecm;
import com.fasterxml.jackson.databind.*;
import java.nio.file.*;
import java.util.*;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Value;
@Component
public class SensorContract {
 final JsonNode data;
 public SensorContract(ObjectMapper mapper,@Value("${agecm.contract-path:}") String configured) throws Exception {
  Path path=configured.isBlank()?List.of(Path.of("config/sensor-contract.json"),Path.of("../config/sensor-contract.json")).stream().filter(Files::isRegularFile).findFirst().orElseThrow(()->new IllegalArgumentException("Sensor contract file not found")):Path.of(configured);
  data=mapper.readTree(path.toFile());
  if(!"2.0".equals(data.path("schemaVersion").asText()))throw new IllegalArgumentException("Expected sensor contract schema 2.0");
 }
 public JsonNode document(){return data;}
 public boolean confirmed(){return data.path("semanticsConfirmed").asBoolean(false);}
 public JsonNode status(Integer code){return code==null||!confirmed()?null:data.path("statusCodes").get(code.toString());}
 public JsonNode fault(Integer code){return code==null||!confirmed()?null:data.path("faultValues").get(code.toString());}
 public String statusLabel(Integer code){JsonNode value=status(code);return value==null?code==null?"Unavailable":"Code "+code+" · meaning unconfirmed":value.path("label").asText("Unmapped code "+code);}
 public String faultLabel(Integer code){JsonNode value=fault(code);return value==null?code==null?"Unavailable":"Code "+code+" · meaning unconfirmed":value.path("label").asText("Unmapped code "+code);}
}
