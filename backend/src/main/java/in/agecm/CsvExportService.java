package in.agecm;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.*;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.*;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.server.ResponseStatusException;

@Service
public class CsvExportService {
 static final String[] COLUMNS={"id","nodeId","source","schemaVersion","channelId","entryId","sampleAt","timestampBasis","acquiredAt","cloudCreatedAt","receivedAt","temperature","humidity","coMax","ch4Max","distanceNow","devMax","statusWorst","faultAny","rawDistanceNow","fieldIssues","statusText","health"};
 static final String SELECT="id,node_id,source,schema_version,channel_id,entry_id,sample_at,timestamp_basis,acquired_at,cloud_created_at,received_at,temperature,humidity,co_max,ch4_max,distance_now,dev_max,status_worst,fault_any,raw_distance_now,field_issues,status_text,health";
 record Snapshot(String id,Path file,String filename,long count,Instant exportedAt,Instant start,Instant end,String nodeId) {}
 final Map<String,Snapshot> snapshots=new ConcurrentHashMap<>();
 final Semaphore workers=new Semaphore(2);
 final JdbcTemplate jdbc; final TransactionTemplate transaction; final MonitoringService monitoring;
 public CsvExportService(JdbcTemplate jdbc,PlatformTransactionManager manager,MonitoringService monitoring){
  this.jdbc=jdbc;this.monitoring=monitoring;transaction=new TransactionTemplate(manager);transaction.setReadOnly(true);transaction.setIsolationLevel(TransactionDefinition.ISOLATION_REPEATABLE_READ);transaction.setTimeout(90);
 }
 public Map<String,Object> prepare(String nodeId,int hours){
  if(nodeId!=null)monitoring.validNode(nodeId);
  if(!Set.of(1,6,24,168).contains(hours))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Choose 1, 6, 24 or 168 hours");
  cleanup();if(snapshots.size()>=32||!workers.tryAcquire())throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS,"Export is busy; try again shortly");
  Path file=null;
  try{
   Instant end=Instant.now(),start=end.minusSeconds(hours*3600L);String id=UUID.randomUUID().toString();
   file=Files.createTempFile("agecm-export-",".csv");final Path target=file;
   long count=Objects.requireNonNull(transaction.execute(tx->{
    try(BufferedWriter out=Files.newBufferedWriter(target,StandardCharsets.UTF_8)){
     out.write('\ufeff');out.write(String.join(",",COLUMNS));out.write("\r\n");
     return jdbc.query(connection->{
      PreparedStatement statement=connection.prepareStatement("SELECT "+SELECT+" FROM telemetry WHERE source=? AND schema_version=? AND sample_at>=? AND sample_at<=? AND received_at<=?"+(nodeId==null?"":" AND node_id=?")+" ORDER BY sample_at ASC,id ASC",ResultSet.TYPE_FORWARD_ONLY,ResultSet.CONCUR_READ_ONLY);
      statement.setFetchSize(500);statement.setQueryTimeout(90);statement.setString(1,monitoring.source());statement.setString(2,MonitoringService.SCHEMA);statement.setTimestamp(3,Timestamp.from(start));statement.setTimestamp(4,Timestamp.from(end));statement.setTimestamp(5,Timestamp.from(end));if(nodeId!=null)statement.setString(6,nodeId);return statement;
     },(org.springframework.jdbc.core.ResultSetExtractor<Long>)rs->{
      long rows=0;try{while(rs.next()){
       for(int i=1;i<=COLUMNS.length;i++){if(i>1)out.write(',');Object value=rs.getObject(i);String text=value==null?"":(i==7||i==9||i==10||i==11)?rs.getTimestamp(i).toInstant().toString():value.toString();
        // Numeric values retain their signs. Prevent spreadsheet execution of untrusted text.
        if(value instanceof String&&!text.stripLeading().isEmpty()&&"=+@-".indexOf(text.stripLeading().charAt(0))>=0)text="'"+text;
        out.write(escape(text));}
       out.write("\r\n");rows++;if(rows%500==0){out.flush();if(Files.size(target)>128L*1024*1024)throw new IOException("Export exceeds 128 MiB; select a shorter range");}
      }}catch(IOException e){throw new UncheckedIOException(e);}return rows;
     });
    }catch(IOException e){throw new UncheckedIOException(e);}
   }));
   if(Files.size(file)>128L*1024*1024)throw new IOException("Export exceeds 128 MiB");
   Map<String,Object> result=new LinkedHashMap<>();result.put("count",count);result.put("exportedAt",end);result.put("start",start);result.put("end",end);result.put("scope",nodeId==null?"comparison":nodeId);
   if(count==0){Files.deleteIfExists(file);result.put("downloadUrl",null);return result;}
   String filename="agecm-"+(nodeId==null?"comparison":nodeId)+"-"+hours+"h-"+DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC).format(end)+"-"+id.substring(0,8)+".csv";
   snapshots.put(id,new Snapshot(id,file,filename,count,end,start,end,nodeId));result.put("downloadUrl","/api/telemetry/exports/"+id);return result;
  }catch(RuntimeException|IOException e){if(file!=null)try{Files.deleteIfExists(file);}catch(IOException ignored){}if(e instanceof ResponseStatusException status)throw status;throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Fresh CSV could not be prepared; retry or select a shorter range");}
  finally{workers.release();}
 }
 static String escape(String text){return text.indexOf(',')>=0||text.indexOf('"')>=0||text.indexOf('\r')>=0||text.indexOf('\n')>=0?'"'+text.replace("\"","\"\"")+'"':text;}
 public ResponseEntity<FileSystemResource> download(String id){
  Snapshot snapshot=snapshots.get(id);if(snapshot==null||snapshot.exportedAt().isBefore(Instant.now().minusSeconds(300))||!Files.exists(snapshot.file()))throw new ResponseStatusException(HttpStatus.GONE,"Export expired; prepare a fresh export");
  try{return ResponseEntity.ok().cacheControl(CacheControl.noStore()).header(HttpHeaders.CONTENT_DISPOSITION,ContentDisposition.attachment().filename(snapshot.filename()).build().toString()).header("X-Export-Cutoff",snapshot.end().toString()).header("X-Export-Row-Count",Long.toString(snapshot.count())).contentType(new MediaType("text","csv",StandardCharsets.UTF_8)).contentLength(Files.size(snapshot.file())).body(new FileSystemResource(snapshot.file()));}
  catch(IOException e){throw new ResponseStatusException(HttpStatus.GONE,"Export unavailable; prepare a fresh export");}
 }
 @Scheduled(fixedDelay=60000) public void cleanup(){snapshots.forEach((id,s)->{if(s.exportedAt().isBefore(Instant.now().minusSeconds(300))&&snapshots.remove(id,s))try{Files.deleteIfExists(s.file());}catch(IOException ignored){}});}
}
