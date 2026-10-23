package in.agecm;
import org.junit.jupiter.api.Test;
import org.flywaydb.core.Flyway;
import java.sql.*;
import static org.junit.jupiter.api.Assertions.*;
class MigrationPreservationTest {
 @Test void upgradesExistingCloudHistoryAndSeedsWatermarkWithoutDeletingRows() throws Exception {
  String url="jdbc:h2:mem:reuseMigration;MODE=PostgreSQL;DB_CLOSE_DELAY=-1";
  Flyway.configure().dataSource(url,"sa","").target("3").load().migrate();
  try(Connection c=DriverManager.getConnection(url,"sa","");Statement s=c.createStatement()){
   s.executeUpdate("INSERT INTO telemetry(unique_key,source_key,node_id,source,schema_version,channel_id,entry_id,cloud_created_at,received_at) VALUES ('cloud:100:1','cloud:100:1','node_01','cloud_hardware','2.0','100',1,TIMESTAMP WITH TIME ZONE '2026-10-20 01:00:00+00',CURRENT_TIMESTAMP)");
   s.executeUpdate("UPDATE ingestion_state SET channel_id='100',schema_version='2.0',last_entry_id=1 WHERE node_id='node_01'");
  }
  Flyway.configure().dataSource(url,"sa","").load().migrate();
  try(Connection c=DriverManager.getConnection(url,"sa","");Statement s=c.createStatement()){
   ResultSet watermark=s.executeQuery("SELECT last_entry_id,last_cloud_created_at FROM ingestion_state WHERE node_id='node_01'");assertTrue(watermark.next());assertEquals(1,watermark.getLong(1));assertNotNull(watermark.getObject(2));
   s.executeUpdate("INSERT INTO telemetry(unique_key,source_key,node_id,source,schema_version,channel_id,entry_id,cloud_created_at,received_at) VALUES ('new-observation','new-observation','node_01','cloud_hardware','2.0','100',1,TIMESTAMP WITH TIME ZONE '2026-10-20 02:00:00+00',CURRENT_TIMESTAMP)");
   ResultSet rows=s.executeQuery("SELECT count(*) FROM telemetry");assertTrue(rows.next());assertEquals(2,rows.getInt(1));
   assertThrows(SQLException.class,()->s.executeUpdate("INSERT INTO telemetry(unique_key,source_key,node_id,source,schema_version,channel_id,entry_id,cloud_created_at,received_at) VALUES ('duplicate','duplicate','node_01','cloud_hardware','2.0','100',1,TIMESTAMP WITH TIME ZONE '2026-10-20 02:00:00+00',CURRENT_TIMESTAMP)"));
  }
 }
 @Test void preservesLegacyDataAndAllowsCloudOnlyV2Identity() throws Exception {
  String url="jdbc:h2:mem:preserve;MODE=PostgreSQL;DB_CLOSE_DELAY=-1";
  Flyway.configure().dataSource(url,"sa","").target("1").load().migrate();
  try(Connection c=DriverManager.getConnection(url,"sa","");Statement s=c.createStatement()){
   s.executeUpdate("INSERT INTO telemetry(unique_key,source_key,node_id,source,schema_version,boot_id,sequence,acquired_at,received_at,tilt,quality_flags,calibrated,feature_ready,rule_version,state,health) VALUES ('legacy','legacy','node_01','demo','1.0','old',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,3.14,0,true,true,'lab-rule-v1','NORMAL','HEALTHY')");
  }
  Flyway.configure().dataSource(url,"sa","").load().migrate();
  try(Connection c=DriverManager.getConnection(url,"sa","");Statement s=c.createStatement()){
   ResultSet old=s.executeQuery("SELECT tilt FROM telemetry WHERE unique_key='legacy'");assertTrue(old.next());assertEquals(3.14,old.getDouble(1));
   s.executeUpdate("INSERT INTO telemetry(unique_key,source_key,node_id,source,schema_version,channel_id,entry_id,cloud_created_at,received_at,sample_at,timestamp_basis,co_max,fault_any) VALUES ('cloud:100:1','cloud:100:1','node_01','cloud_hardware','2.0','100',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,'CLOUD_CREATED_AT',0,0)");
   ResultSet count=s.executeQuery("SELECT count(*) FROM telemetry");assertTrue(count.next());assertEquals(2,count.getInt(1));
  }
 }
}
