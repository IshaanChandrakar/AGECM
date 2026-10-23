package in.agecm;
import java.time.*;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import com.fasterxml.jackson.databind.*;
import jakarta.annotation.PostConstruct;

@Service
public class MonitoringService {
 static final String SCHEMA="2.0", VERSION="sensor-v2";
 final TelemetryRepository records; final AlertRepository alerts; final IngestionRepository ingestion;
 final ObjectMapper mapper; final SimpMessagingTemplate socket; final SensorContract contract;
 @Value("${agecm.mode}") String mode;
 @Value("${agecm.stale-seconds}") long staleSeconds;
 @Value("${agecm.reporting-seconds}") int reportSeconds;
 @Value("${agecm.fixture:false}") boolean fixture;
 @Value("${agecm.channel1}") String channel1;
 @Value("${agecm.channel2}") String channel2;
 public MonitoringService(TelemetryRepository r,AlertRepository a,IngestionRepository i,ObjectMapper m,SimpMessagingTemplate s,SensorContract c){records=r;alerts=a;ingestion=i;mapper=m;socket=s;contract=c;}
 @PostConstruct void validateMode(){if(!Set.of("DEMO","LIVE").contains(mode.toUpperCase()))throw new IllegalArgumentException("AGECM_MODE must be DEMO or LIVE");}
 public String source(){return "LIVE".equalsIgnoreCase(mode)?"cloud_hardware":"demo";}
 public String getMode(){return mode;}
 public JsonNode contractDocument(){return contract.document();}
 public long telemetryCount(){return records.count();}
 public List<IngestionState> integrations(){return ingestion.findAll();}
 public Map<String,Object> cursor(String node){validNode(node);IngestionState c=ingestion.findById(node).orElseThrow();boolean matches=Objects.equals(c.channelId,channel(node))&&SCHEMA.equals(c.schemaVersion);Map<String,Object> result=new LinkedHashMap<>();result.put("lastEntryId",matches?c.lastEntryId:0);result.put("lastCloudCreatedAt",matches?c.lastCloudCreatedAt:null);result.put("mode",mode);result.put("schemaVersion",SCHEMA);return result;}
 public Page<Alert> alertPage(int page,int size){return alerts.findBySourceAndRuleVersion(source(),VERSION,PageRequest.of(Math.max(0,page),Math.min(500,Math.max(1,size)),Sort.by(Sort.Direction.DESC,"firstOccurredAt")));}
 public Alert alert(Long id){Alert a=alerts.findById(id).orElseThrow(()->new ResponseStatusException(HttpStatus.NOT_FOUND));if(!source().equals(a.source)||!VERSION.equals(a.ruleVersion))throw new ResponseStatusException(HttpStatus.NOT_FOUND);return a;}
 public String channel(String node){return "node_01".equals(node)?channel1:channel2;}
 void validNode(String id){if(!Set.of("node_01","node_02").contains(id))throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Unknown sensing node");}
 void require(boolean condition,String reason){if(!condition)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,reason);}
 Map<String,Double> measurements(TelemetryInput t){Map<String,Double> values=new LinkedHashMap<>();values.put("temperature",t.temperature);values.put("humidity",t.humidity);values.put("coMax",t.coMax);values.put("ch4Max",t.ch4Max);values.put("distanceNow",t.distanceNow);values.put("devMax",t.devMax);values.put("statusWorst",t.statusWorst==null?null:t.statusWorst.doubleValue());values.put("faultAny",t.faultAny==null?null:t.faultAny.doubleValue());return values;}
 String readingHealth(TelemetryInput t){
  JsonNode reportedFault=contract.fault(t.faultAny);
  if(reportedFault!=null&&reportedFault.path("isFault").asBoolean(false))return "WINDOW_FAULT";
  if(measurements(t).values().stream().allMatch(Objects::isNull))return "NO_VALID_VALUES";
  if(measurements(t).values().stream().anyMatch(Objects::isNull))return "PARTIAL_DATA";
  JsonNode fault=contract.fault(t.faultAny);
  if(fault==null||contract.status(t.statusWorst)==null)return "SEMANTICS_UNVERIFIED";
  return fault.path("isFault").asBoolean(true)?"WINDOW_FAULT":"AVAILABLE";
 }
 @Transactional public synchronized Map<String,Object> ingest(TelemetryInput input){
  validNode(input.nodeId);require(SCHEMA.equals(input.schemaVersion),"Expected sensor schema 2.0");require(source().equals(input.source),"Record source does not match server mode");
  require(input.acquiredAt==null||!input.acquiredAt.isAfter(Instant.now().plusSeconds(10)),"Future acquisition timestamp");
  if(input.rawDistanceNow==null)input.rawDistanceNow=input.distanceNow;
  if(input.distanceNow!=null&&input.distanceNow<0)input.distanceNow=null;
  require(input.rawDistanceNow==null||Double.isFinite(input.rawDistanceNow),"Raw distance must be finite or null");
  require(input.humidity==null||(input.humidity>=0&&input.humidity<=100),"Humidity outside 0–100 %RH");
  for(Double value:Arrays.asList(input.coMax,input.ch4Max,input.devMax))require(value==null||value>=0,"Gas and deviation values cannot be negative");
  require(input.statusWorst==null||!contract.confirmed()||contract.status(input.statusWorst)!=null,"Unmapped firmware status code");
  for(Double value:measurements(input).values())require(value==null||Double.isFinite(value),"Measurements must be finite or null");
  require(input.faultAny==null||input.faultAny==0||input.faultAny==1,"Fault any must be binary or null; meaning is configured separately");
  if("cloud_hardware".equals(input.source)){
   require(!channel(input.nodeId).isBlank()&&channel(input.nodeId).equals(input.channelId),"Channel does not match node");
   require(input.entryId!=null&&input.entryId>0&&input.cloudCreatedAt!=null,"Cloud records require positive entry ID and cloud timestamp");
   require(!input.cloudCreatedAt.isAfter(Instant.now().plusSeconds(10)),"Future cloud timestamp");
   require(input.acquiredAt==null||!input.acquiredAt.isAfter(input.cloudCreatedAt.plusSeconds(10)),"Acquisition follows cloud timestamp");
  }else{require(input.channelId==null&&input.entryId==null&&input.cloudCreatedAt==null,"Demo cannot use cloud identity");require(input.acquiredAt!=null&&input.bootId!=null&&!input.bootId.isBlank()&&input.sequence!=null,"Demo requires acquisition time and session identity");}
  String key="cloud_hardware".equals(input.source)?"cloud:"+input.channelId+":"+input.entryId+":"+input.cloudCreatedAt:"demo:"+input.nodeId+":"+input.bootId+":"+input.sequence;
  String sourceKey="cloud_hardware".equals(input.source)&&(input.bootId==null||input.sequence==null)?key:input.source+":"+input.nodeId+":"+input.bootId+":"+input.sequence;
  if(("cloud_hardware".equals(input.source)&&records.existsByChannelIdAndEntryIdAndCloudCreatedAt(input.channelId,input.entryId,input.cloudCreatedAt))||records.existsByUniqueKeyOrSourceKey(key,sourceKey)){commitCursor(input);return Map.of("accepted",true,"duplicate",true);}
  Telemetry t=mapper.convertValue(input,Telemetry.class);t.uniqueKey=key;t.sourceKey=sourceKey;t.receivedAt=Instant.now();t.sampleAt=input.acquiredAt==null?input.cloudCreatedAt:input.acquiredAt;t.timestampBasis=input.acquiredAt==null?"CLOUD_CREATED_AT":"demo".equals(input.source)?"DEMO_UTC":"ACQUISITION_UTC";
  t.health=readingHealth(t);Map<String,String> issues=new LinkedHashMap<>();try{if(t.fieldIssues!=null)mapper.readTree(t.fieldIssues).fields().forEachRemaining(e->{if(measurements(t).containsKey(e.getKey()))issues.put(e.getKey(),e.getValue().asText());});}catch(Exception ignored){}
  if(t.rawDistanceNow!=null&&t.rawDistanceNow<0)issues.put("distanceNow","firmware distance sentinel");
  if(t.faultAny!=null&&t.faultAny==1){if(t.distanceNow!=null&&t.distanceNow==0)issues.put("distanceNow","zero is ambiguous during a window fault");if(t.devMax!=null&&t.devMax==0)issues.put("devMax","zero is ambiguous during a window fault");}
  measurements(t).forEach((k,v)->{if(v==null)issues.putIfAbsent(k,"missing");});try{t.fieldIssues=mapper.writeValueAsString(issues);}catch(Exception e){throw new IllegalArgumentException(e);}
  records.saveAndFlush(t);commitCursor(t);Telemetry latest=latest(input.nodeId);
  if(latest.id.equals(t.id))evaluateNode(t.nodeId);
  publish("telemetry",t);return Map.of("accepted",true,"duplicate",false,"id",t.id);
 }
 Telemetry latest(String node){return records.findFirstByNodeIdAndSourceAndSchemaVersionOrderBySampleAtDescIdDesc(node,source(),SCHEMA).orElse(null);}
 void commitCursor(TelemetryInput input){if(input.entryId!=null){IngestionState c=ingestion.findById(input.nodeId).orElseThrow();if(!Objects.equals(c.channelId,input.channelId)||!SCHEMA.equals(c.schemaVersion)){c.lastEntryId=0;c.lastCloudCreatedAt=null;}c.channelId=input.channelId;c.schemaVersion=SCHEMA;
  // A newer cloud timestamp can legitimately carry a reused/lower ID after channel clearing.
  // Replays and older backfills must never rewind this durable watermark.
  if(c.lastCloudCreatedAt==null||input.cloudCreatedAt.isAfter(c.lastCloudCreatedAt)||(input.cloudCreatedAt.equals(c.lastCloudCreatedAt)&&input.entryId>c.lastEntryId)){c.lastEntryId=input.entryId;c.lastCloudCreatedAt=input.cloudCreatedAt;}
  c.lastSuccessAt=Instant.now();ingestion.save(c);}}

 void publish(String topic,Object event){if(TransactionSynchronizationManager.isSynchronizationActive())TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization(){@Override public void afterCommit(){socket.convertAndSend("/topic/"+topic,event);}});else socket.convertAndSend("/topic/"+topic,event);}
 public Map<String,Object> node(String id){
  validNode(id);Telemetry t=latest(id);IngestionState cloud=ingestion.findById(id).orElseThrow();String health=t==null?"NO_DATA":readingHealth(t);
  if(t!=null&&Duration.between(t.sampleAt,Instant.now()).getSeconds()>staleSeconds)health="STALE";
  if("ERROR".equals(cloud.status)||"GAP".equals(cloud.status))health="CLOUD_ERROR";
  if("cloud_hardware".equals(source())){if(channel(id).isBlank()||"NOT_CONFIGURED".equals(cloud.status))health="NOT_CONFIGURED";else if(cloud.lastPollAt==null||Duration.between(cloud.lastPollAt,Instant.now()).getSeconds()>staleSeconds)health="ADAPTER_UNAVAILABLE";}
  Map<String,Object> result=new LinkedHashMap<>();result.put("id",id);result.put("role","SENSING");result.put("position",id.endsWith("1")?"Monitoring position 1":"Monitoring position 2");result.put("latest",t);result.put("health",health);
  result.put("firmwareStatusLabel",contract.statusLabel(t==null?null:t.statusWorst));result.put("faultLabel",contract.faultLabel(t==null?null:t.faultAny));
  result.put("ageSeconds",t==null?null:Math.max(0,Duration.between(t.sampleAt,Instant.now()).getSeconds()));result.put("channelConfigured",!channel(id).isBlank());result.put("expectedReportSeconds",reportSeconds);result.put("cloud",cloud);return result;
 }
 public List<Map<String,Object>> nodes(){return List.of(node("node_01"),node("node_02"));}
 public Map<String,Object> status(){Map<String,Object> result=new LinkedHashMap<>();result.put("mode",mode.toUpperCase());result.put("source",source());result.put("fixture",fixture);result.put("serverTime",Instant.now());result.put("database","HEALTHY");result.put("expectedReportSeconds",reportSeconds);result.put("staleSeconds",staleSeconds);result.put("nodes",nodes());result.put("contract",contract.document());result.put("central",Map.of("id","node_03","role","CENTRAL_MONITOR","status","UNVERIFIED","description","Independent ThingSpeak reader and local display. No central heartbeat is integrated."));return result;}
 @Transactional public synchronized void report(String node,String status,String error,int gaps){validNode(node);require(Set.of("HEALTHY","ERROR","NOT_CONFIGURED","GAP","DEMO").contains(status),"Invalid integration status");IngestionState c=ingestion.findById(node).orElseThrow();if(!Objects.equals(c.channelId,channel(node))){c.lastEntryId=0;c.lastCloudCreatedAt=null;}if(!"GAP".equals(c.status))c.knownGaps+=Math.max(0,gaps);c.status=status;c.lastError=error==null?null:error.substring(0,Math.min(error.length(),500));c.lastPollAt=Instant.now();c.channelId=channel(node).isBlank()?null:channel(node);ingestion.save(c);evaluateNode(node);publish("health",Map.of("nodeId",node,"status",status));}
 void evaluateNode(String node){
  Map<String,Object> view=node(node);Telemetry t=(Telemetry)view.get("latest");String health=(String)view.get("health");Map<String,String> desired=new LinkedHashMap<>();
  if(!Set.of("AVAILABLE","NO_DATA","NOT_CONFIGURED","SEMANTICS_UNVERIFIED","WINDOW_FAULT").contains(health))desired.put(health,"Data health: "+health+". No platform safety classification is inferred.");
  if(t!=null&&Set.of("AVAILABLE","WINDOW_FAULT","PARTIAL_DATA","SEMANTICS_UNVERIFIED").contains(health)){
   JsonNode s=contract.status(t.statusWorst);if(s!=null&&s.path("severity").asInt(0)>0)desired.put("FIRMWARE_STATUS","Firmware status code "+t.statusWorst+": "+contract.statusLabel(t.statusWorst));
   JsonNode f=contract.fault(t.faultAny);if(f!=null&&f.path("isFault").asBoolean(false))desired.put("FAULT_REPORTED","Firmware fault code "+t.faultAny+": "+contract.faultLabel(t.faultAny));
  }
  Instant now=Instant.now();for(Alert a:alerts.findBySourceAndNodeIdAndRuleVersionAndResolvedAtIsNull(source(),node,VERSION)){if(desired.containsKey(a.condition)&&Objects.equals(desired.get(a.condition),a.triggerText)){a.lastOccurredAt=now;desired.remove(a.condition);}else{a.resolvedAt=now;publish("alerts",a);}alerts.save(a);}
  desired.forEach((condition,trigger)->{Alert a=new Alert();a.nodeId=node;a.source=source();a.condition=condition;a.severity=condition.equals("FIRMWARE_STATUS")?contract.statusLabel(t.statusWorst):condition.equals("FAULT_REPORTED")?"FAULT":"DATA";a.triggerText=trigger;a.firstOccurredAt=now;a.lastOccurredAt=now;a.recordId=t==null?null:t.id;a.ruleVersion=VERSION;a.qualityFlags=0;alerts.save(a);publish("alerts",a);});
 }
 @Scheduled(fixedDelay=10000) @Transactional public synchronized void checkFreshness(){evaluateNode("node_01");evaluateNode("node_02");}
 public Page<Telemetry> history(String node,Instant start,Instant end,int page,int size){require(!end.isBefore(start),"End must follow start");Pageable p=PageRequest.of(Math.max(0,page),Math.min(2000,Math.max(1,size)),Sort.by(Sort.Direction.DESC,"sampleAt","id"));if(node==null)return records.findBySourceAndSchemaVersionAndSampleAtBetween(source(),SCHEMA,start,end,p);validNode(node);return records.findBySourceAndSchemaVersionAndNodeIdAndSampleAtBetween(source(),SCHEMA,node,start,end,p);}
}
