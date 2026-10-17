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
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;

@Service
public class MonitoringService {
 final TelemetryRepository records; final AlertRepository alerts; final IngestionRepository ingestion;
 final ObjectMapper mapper; final SimpMessagingTemplate socket;
 @Value("${agecm.mode}") String mode;
 @Value("${agecm.stale-seconds}") long staleSeconds;
 @Value("${agecm.reporting-seconds}") int reportSeconds;
 @Value("${agecm.channel1}") String channel1;
 @Value("${agecm.channel2}") String channel2;
 public MonitoringService(TelemetryRepository r,AlertRepository a,IngestionRepository i,ObjectMapper m,SimpMessagingTemplate s){records=r;alerts=a;ingestion=i;mapper=m;socket=s;}
 @PostConstruct void validateMode(){if(!Set.of("DEMO","LIVE").contains(mode.toUpperCase()))throw new IllegalArgumentException("AGECM_MODE must be DEMO or LIVE");}
 public String source(){return "LIVE".equalsIgnoreCase(mode)?"cloud_hardware":"demo";}
 public String getMode(){return mode;}
 public long telemetryCount(){return records.count();}
 public List<IngestionState> integrations(){return ingestion.findAll();}
 public Map<String,Object> cursor(String node){validNode(node);IngestionState c=ingestion.findById(node).orElseThrow();return Map.of("lastEntryId",Objects.equals(c.channelId,channel(node))?c.lastEntryId:0,"mode",mode);}
 public Page<Alert> alertPage(int page,int size){return alerts.findBySource(source(),PageRequest.of(Math.max(0,page),Math.min(500,Math.max(1,size)),Sort.by(Sort.Direction.DESC,"firstOccurredAt")));}
 public Alert alert(Long id){Alert a=alerts.findById(id).orElseThrow(()->new ResponseStatusException(HttpStatus.NOT_FOUND));if(!source().equals(a.source))throw new ResponseStatusException(HttpStatus.NOT_FOUND);return a;}
 public String channel(String node){return "node_01".equals(node)?channel1:channel2;}
 void validNode(String id){if(!Set.of("node_01","node_02").contains(id)) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Unknown sensing node");}
 void require(boolean condition,String reason){if(!condition)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,reason);}
 @Transactional
 public synchronized Map<String,Object> ingest(TelemetryInput input){
   validNode(input.nodeId);
   require(source().equals(input.source),"Record source does not match server data mode");
   require(!input.acquiredAt.isAfter(Instant.now().plusSeconds(10)),"Acquisition time is in the future");
   for(Double value:Arrays.asList(input.tilt,input.displacement,input.vibration,input.tiltRate,input.displacementVelocity)) require(value==null||Double.isFinite(value),"Measurements must be finite or null");
   require(input.tilt==null||Math.abs(input.tilt)<=180,"Tilt exceeds physical range");
   require(input.displacement==null||Math.abs(input.displacement)<=2000,"Displacement exceeds configured rig range");
   require(input.vibration==null||(input.vibration>=0&&input.vibration<=16),"Vibration proxy exceeds configured IMU range");
   if("cloud_hardware".equals(input.source)){
     require(!channel(input.nodeId).isBlank()&&channel(input.nodeId).equals(input.channelId),"Channel does not match configured node");
     require(input.entryId!=null&&input.cloudCreatedAt!=null,"Cloud records need an entry ID and cloud timestamp");
   }else require(input.channelId==null&&input.entryId==null&&input.cloudCreatedAt==null,"Demo records cannot use cloud identity");
   boolean valid=input.qualityFlags==0&&input.calibrated&&input.tilt!=null&&input.displacement!=null&&input.vibration!=null;
   if(!valid){input.health=input.qualityFlags!=0||input.tilt==null||input.displacement==null||input.vibration==null?"INVALID_SENSOR":"NOT_READY";input.state="UNAVAILABLE";input.featureReady=false;input.tiltRate=null;input.displacementVelocity=null;}
   if(!input.featureReady||input.tiltRate==null||input.displacementVelocity==null){input.state="UNAVAILABLE";if("HEALTHY".equals(input.health))input.health="NOT_READY";}
   String sourceKey=input.source+":"+input.nodeId+":"+input.bootId+":"+input.sequence;
   String key="cloud_hardware".equals(input.source)?"cloud:"+input.channelId+":"+input.entryId:sourceKey;
   if(records.existsByUniqueKeyOrSourceKey(key,sourceKey)){commitCursor(input);return Map.of("accepted",true,"duplicate",true);}
   Telemetry record=mapper.convertValue(input,Telemetry.class);record.uniqueKey=key;record.sourceKey=sourceKey;record.receivedAt=Instant.now();records.saveAndFlush(record);
   commitCursor(input);
   Telemetry latest=records.findFirstByNodeIdAndSourceOrderByAcquiredAtDescIdDesc(record.nodeId,source()).orElseThrow();
   if(latest.id.equals(record.id))evaluateNode(record.nodeId);
   publish("telemetry",record);
   return Map.of("accepted",true,"duplicate",false,"id",record.id);
 }
 void commitCursor(TelemetryInput input){if(input.entryId!=null){IngestionState c=ingestion.findById(input.nodeId).orElseThrow();if(!Objects.equals(c.channelId,input.channelId)){c.lastEntryId=0;c.channelId=input.channelId;}c.lastEntryId=Math.max(c.lastEntryId,input.entryId);c.lastSuccessAt=Instant.now();ingestion.save(c);}}
 void publish(String topic,Object event){
   if(TransactionSynchronizationManager.isSynchronizationActive())TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization(){@Override public void afterCommit(){socket.convertAndSend("/topic/"+topic,event);}});
   else socket.convertAndSend("/topic/"+topic,event);
 }
 public Map<String,Object> node(String id){
   validNode(id);Map<String,Object> result=new LinkedHashMap<>();Telemetry t=records.findFirstByNodeIdAndSourceOrderByAcquiredAtDescIdDesc(id,source()).orElse(null);
   IngestionState cloud=ingestion.findById(id).orElseThrow();String health=t==null?"NO_DATA":t.health;
   if(t!=null&&Duration.between(t.acquiredAt,Instant.now()).getSeconds()>staleSeconds)health="STALE";
   if("demo".equals(source())&&"ERROR".equals(cloud.status))health="CLOUD_ERROR";
   if("cloud_hardware".equals(source())){
     if(channel(id).isBlank())health="NOT_CONFIGURED";
     else if("ERROR".equals(cloud.status)||"GAP".equals(cloud.status))health="CLOUD_ERROR";
     else if(cloud.lastPollAt==null||Duration.between(cloud.lastPollAt,Instant.now()).getSeconds()>staleSeconds)health="ADAPTER_UNAVAILABLE";
   }
   result.put("id",id);result.put("role","SENSING");result.put("position",id.endsWith("1")?"Monitoring position 1":"Monitoring position 2");
   result.put("latest",t);result.put("health",health);result.put("state","HEALTHY".equals(health)&&t!=null?t.state:"UNAVAILABLE");
   result.put("ageSeconds",t==null?null:Math.max(0,Duration.between(t.acquiredAt,Instant.now()).getSeconds()));result.put("channelConfigured",!channel(id).isBlank());result.put("expectedReportSeconds",reportSeconds);result.put("cloud",cloud);return result;
 }
 public List<Map<String,Object>> nodes(){return List.of(node("node_01"),node("node_02"));}
 public Map<String,Object> status(){Map<String,Object> result=new LinkedHashMap<>();result.put("mode",mode.toUpperCase());result.put("source",source());result.put("serverTime",Instant.now());result.put("database","HEALTHY");result.put("expectedReportSeconds",reportSeconds);result.put("staleSeconds",staleSeconds);result.put("nodes",nodes());result.put("central",Map.of("id","node_03","role","CENTRAL_MONITOR","status","UNVERIFIED","description","Independent ThingSpeak reader and local display. No central-device heartbeat is integrated."));return result;}
 @Transactional
 public synchronized void report(String node,String status,String error,int gaps){
   validNode(node);require(Set.of("HEALTHY","ERROR","NOT_CONFIGURED","GAP","DEMO").contains(status),"Invalid integration status");
   IngestionState c=ingestion.findById(node).orElseThrow();if(!"GAP".equals(c.status))c.knownGaps+=Math.max(0,gaps);c.status=status;c.lastError=error==null?null:error.substring(0,Math.min(error.length(),500));c.lastPollAt=Instant.now();c.channelId=channel(node).isBlank()?null:channel(node);ingestion.save(c);evaluateNode(node);publish("health",Map.of("nodeId",node,"status",status));
 }
 void evaluateNode(String node){
   Map<String,Object> view=node(node);String health=(String)view.get("health");String state=(String)view.get("state");Telemetry t=(Telemetry)view.get("latest");
   String condition="HEALTHY".equals(health)?state:health;
   List<Alert> active=alerts.findBySourceAndNodeIdAndResolvedAtIsNull(source(),node);Instant now=Instant.now();boolean same=false;
   for(Alert a:active){if(a.condition.equals(condition)){a.lastOccurredAt=now;same=true;}else{a.resolvedAt=now;publish("alerts",a);}alerts.save(a);}
   if(!same&&!Set.of("NORMAL","NOT_READY","NO_DATA","NOT_CONFIGURED","UNAVAILABLE").contains(condition)){
     Alert a=new Alert();a.nodeId=node;a.source=source();a.condition=condition;a.severity="CRITICAL".equals(condition)?"HIGH":"WARNING".equals(condition)?"MEDIUM":"HEALTH";
     a.triggerText=Set.of("WARNING","CRITICAL").contains(condition)?"Magnitude tilt-rate laboratory rule; consecutive evidence and hysteresis applied.":"Data health: "+condition+". Movement classification unavailable.";
     a.firstOccurredAt=now;a.lastOccurredAt=now;a.recordId=t==null?null:t.id;a.ruleVersion=t==null?"lab-rule-v1":t.ruleVersion;a.qualityFlags=t==null?0:t.qualityFlags;alerts.save(a);publish("alerts",a);
   }
 }
 @Scheduled(fixedDelay=10000) @Transactional
 public synchronized void checkFreshness(){evaluateNode("node_01");evaluateNode("node_02");}
 public Page<Telemetry> history(String node,Instant start,Instant end,int page,int size){
   require(!end.isBefore(start),"End must follow start");Pageable p=PageRequest.of(Math.max(0,page),Math.min(2000,Math.max(1,size)),Sort.by(Sort.Direction.DESC,"acquiredAt","id"));
   if(node==null)return records.findBySourceAndAcquiredAtBetween(source(),start,end,p);validNode(node);return records.findBySourceAndNodeIdAndAcquiredAtBetween(source(),node,start,end,p);
 }
}
