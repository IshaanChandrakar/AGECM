package in.agecm;
import org.springframework.http.*;
import org.springframework.core.io.FileSystemResource;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
@RestController @RequestMapping("/api/telemetry/exports")
public class CsvExportController {
 final CsvExportService exports;
 public CsvExportController(CsvExportService exports){this.exports=exports;}
 @PostMapping public ResponseEntity<Map<String,Object>> prepare(@RequestParam(required=false)String nodeId,@RequestParam(defaultValue="1")int hours){return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(exports.prepare(nodeId,hours));}
 @GetMapping("/{id}") public ResponseEntity<FileSystemResource> download(@PathVariable String id){return exports.download(id);}
}
