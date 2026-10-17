package in.agecm;
import java.time.Instant;
import java.util.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.data.domain.*;
import jakarta.validation.Valid;
import org.springframework.web.bind.MethodArgumentNotValidException;

@RestController @RequestMapping("/api")
public class ApiController {
 final MonitoringService service;
 @Value("${agecm.ingestion-token}") String token;
 public ApiController(MonitoringService s){service=s;}
 void authorize(String supplied){if(token.isBlank()||supplied==null||!MessageDigest.isEqual(token.getBytes(StandardCharsets.UTF_8),supplied.getBytes(StandardCharsets.UTF_8)))throw new ResponseStatusException(HttpStatus.UNAUTHORIZED,"Valid ingestion token required");}
 @GetMapping("/health") public Object health(){service.telemetryCount();return Map.of("status","UP","database","HEALTHY","mode",service.getMode());}
 @GetMapping("/system/status") public Object status(){return service.status();}
 @GetMapping("/nodes") public Object nodes(){return service.nodes();}
 @GetMapping({"/nodes/{id}","/nodes/{id}/latest"}) public Object node(@PathVariable String id){return service.node(id);}
 @GetMapping("/telemetry/latest") public Object latest(){return service.nodes().stream().map(n->n.get("latest")).filter(Objects::nonNull).toList();}
 @GetMapping({"/telemetry/history","/nodes/{id}/history"}) public Object history(@PathVariable(required=false)String id,@RequestParam(required=false)String nodeId,@RequestParam(required=false)Instant start,@RequestParam(required=false)Instant end,@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="500")int size){return service.history(id==null?nodeId:id,start==null?Instant.now().minusSeconds(3600):start,end==null?Instant.now():end,page,size);}
 @GetMapping("/alerts") public Object alerts(@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="200")int size){return service.alertPage(page,size);}
 @GetMapping("/alerts/{id}") public Object alert(@PathVariable Long id){return service.alert(id);}
 @GetMapping("/integration/thingspeak/status") public Object integration(){return service.integrations();}
 @GetMapping("/ingestion/{node}") public Object cursor(@PathVariable String node,@RequestHeader(value="X-Ingestion-Token",required=false)String key){authorize(key);return service.cursor(node);}
 @PostMapping("/telemetry") public Object ingest(@Valid @RequestBody TelemetryInput input,@RequestHeader(value="X-Ingestion-Token",required=false)String key){authorize(key);return service.ingest(input);}
 public record IntegrationReport(String nodeId,String status,String error,int gaps){}
 @PostMapping("/integration/status") public Object report(@RequestBody IntegrationReport report,@RequestHeader(value="X-Ingestion-Token",required=false)String key){authorize(key);service.report(report.nodeId(),report.status(),report.error(),report.gaps());return Map.of("accepted",true);}
}
@RestControllerAdvice
class ErrorHandler {
 @ExceptionHandler(ResponseStatusException.class) @ResponseStatus
 public org.springframework.http.ResponseEntity<?> status(ResponseStatusException e){return org.springframework.http.ResponseEntity.status(e.getStatusCode()).body(Map.of("error",e.getReason()==null?"Request failed":e.getReason(),"timestamp",Instant.now()));}
 @ExceptionHandler(MethodArgumentNotValidException.class)
 public org.springframework.http.ResponseEntity<?> validation(MethodArgumentNotValidException e){return org.springframework.http.ResponseEntity.badRequest().body(Map.of("error","Invalid telemetry contract","fields",e.getBindingResult().getFieldErrors().stream().map(f->f.getField()+": "+f.getDefaultMessage()).toList()));}
}
