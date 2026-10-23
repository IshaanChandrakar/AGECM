package in.agecm;
import org.junit.jupiter.api.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.jdbc.core.JdbcTemplate;
import com.fasterxml.jackson.databind.*;
import java.time.*;
import java.sql.Timestamp;
import java.nio.charset.StandardCharsets;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(properties={"agecm.mode=LIVE","agecm.channel1=100","agecm.channel2=200","spring.datasource.url=jdbc:h2:mem:csv;MODE=PostgreSQL;DB_CLOSE_DELAY=-1"}) @AutoConfigureMockMvc @ActiveProfiles("test")
class CsvExportIntegrationTest {
 @Autowired MockMvc mvc; @Autowired ObjectMapper mapper; @Autowired JdbcTemplate jdbc; @Autowired CsvExportService exports;
 @BeforeEach void reset(){jdbc.update("DELETE FROM alerts");jdbc.update("DELETE FROM telemetry");}
 void row(String key,String node,String source,Instant sample,Double temperature,String text){jdbc.update("INSERT INTO telemetry(unique_key,source_key,node_id,source,schema_version,channel_id,entry_id,sample_at,cloud_created_at,received_at,timestamp_basis,temperature,humidity,co_max,ch4_max,distance_now,dev_max,status_worst,fault_any,raw_distance_now,field_issues,status_text,health) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",key,key,node,source,"2.0",source.equals("cloud_hardware")?(node.equals("node_01")?"100":"200"):null,source.equals("cloud_hardware")?1:null,Timestamp.from(sample),Timestamp.from(sample),Timestamp.from(Instant.now().minusMillis(10)),"CLOUD_CREATED_AT",temperature,null,0,11,null,0,0,0,-1,"{\"distanceNow\":\"sentinel\"}",text,"PARTIAL_DATA");}
 JsonNode prepare(String query)throws Exception{return mapper.readTree(mvc.perform(post("/api/telemetry/exports"+query)).andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store")).andReturn().getResponse().getContentAsString());}
 String download(JsonNode snapshot)throws Exception{return mvc.perform(get(snapshot.get("downloadUrl").asText())).andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store")).andExpect(header().string("X-Export-Row-Count",snapshot.get("count").asText())).andExpect(content().contentTypeCompatibleWith("text/csv")).andReturn().getResponse().getContentAsString(StandardCharsets.UTF_8);}
 @Test void sourceAndNodeAndTimeFiltersPreserveNullZeroSentinelAndUtc()throws Exception{
  Instant now=Instant.now().minusSeconds(10);row("a","node_01","cloud_hardware",now,23.4,"normal");row("b","node_02","cloud_hardware",now,24.0,"normal");row("old","node_01","cloud_hardware",now.minusSeconds(7200),99.0,"old");row("demo","node_01","demo",now,88.0,"demo");
  JsonNode one=prepare("?hours=1&nodeId=node_01");assertEquals(1,one.get("count").asInt());String csv=download(one);assertTrue(csv.contains("rawDistanceNow,fieldIssues,statusText,health"));assertTrue(csv.contains("23.4,,0.0,11.0,,0.0,0,0,-1.0"));assertTrue(csv.contains(now.toString()));assertFalse(csv.contains("99.0"));assertFalse(csv.contains("88.0"));assertFalse(csv.contains("node_02"));
  assertEquals(2,prepare("?hours=1").get("count").asInt());assertEquals(2,prepare("?hours=6&nodeId=node_01").get("count").asInt());
 }
 @Test void completedSnapshotIsImmutableAndSecondExportIsFresh()throws Exception{
  Instant now=Instant.now().minusSeconds(5);row("a","node_01","cloud_hardware",now,21.0,"first");JsonNode first=prepare("?hours=1");String original=download(first);row("b","node_02","cloud_hardware",now.plusSeconds(1),22.0,"new physical-shaped fixture");assertEquals(original,download(first));JsonNode second=prepare("?hours=1");assertEquals(2,second.get("count").asInt());assertNotEquals(first.get("downloadUrl"),second.get("downloadUrl"));assertTrue(download(second).contains("22.0"));
 }
 @Test void emptyAndInvalidRequestsNeverReturnOldFiles()throws Exception{
  JsonNode empty=prepare("?hours=1");assertEquals(0,empty.get("count").asInt());assertTrue(empty.get("downloadUrl").isNull());mvc.perform(post("/api/telemetry/exports?hours=0")).andExpect(status().isBadRequest());mvc.perform(post("/api/telemetry/exports?nodeId=unknown")).andExpect(status().isNotFound());mvc.perform(get("/api/telemetry/exports/unknown")).andExpect(status().isGone());
 }
 @Test void largerThanChartPageIncludesAllRowsInStableOrder()throws Exception{
  Instant sample=Instant.now().minusSeconds(20);jdbc.batchUpdate("INSERT INTO telemetry(unique_key,source_key,node_id,source,schema_version,sample_at,received_at,co_max) VALUES (?,?,?,'cloud_hardware','2.0',?,?,0)",new org.springframework.jdbc.core.BatchPreparedStatementSetter(){public int getBatchSize(){return 2105;}public void setValues(java.sql.PreparedStatement ps,int i)throws java.sql.SQLException{ps.setString(1,"batch"+i);ps.setString(2,"batch"+i);ps.setString(3,i%2==0?"node_01":"node_02");ps.setTimestamp(4,Timestamp.from(sample));ps.setTimestamp(5,Timestamp.from(sample));}});
  JsonNode snapshot=prepare("?hours=1");assertEquals(2105,snapshot.get("count").asInt());String[] lines=download(snapshot).strip().split("\r\n");assertEquals(2106,lines.length);long previous=0;for(int i=1;i<lines.length;i++){long id=Long.parseLong(lines[i].split(",")[0]);assertTrue(id>previous);previous=id;}
 }
 @Test void quotesCommasNewlinesAndSpreadsheetTextAreHandled()throws Exception{
  row("a","node_01","cloud_hardware",Instant.now().minusSeconds(5),0.0,"He said \"check, sensor\"\nsecond line");String csv=download(prepare("?hours=1"));assertTrue(csv.contains("\"He said \"\"check, sensor\"\"\nsecond line\""));assertEquals("\"a,b\"",CsvExportService.escape("a,b"));row("b","node_02","cloud_hardware",Instant.now().minusSeconds(4),-2.0,"=SUM(A1:A2)\nnext line");csv=download(prepare("?hours=1"));assertTrue(csv.contains("'=SUM(A1:A2)"));assertTrue(csv.contains("-2.0"));
 }
}
