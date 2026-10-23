package in.agecm;
import java.time.Instant;
import java.util.*;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.JpaRepository;
interface TelemetryRepository extends JpaRepository<Telemetry,Long> {
 boolean existsByUniqueKeyOrSourceKey(String key,String sourceKey);
 boolean existsByChannelIdAndEntryIdAndCloudCreatedAt(String channel,Long entry,Instant created);
 Optional<Telemetry> findFirstByNodeIdAndSourceAndSchemaVersionOrderBySampleAtDescIdDesc(String node,String source,String schema);
 Page<Telemetry> findBySourceAndSchemaVersionAndSampleAtBetween(String source,String schema,Instant start,Instant end,Pageable page);
 Page<Telemetry> findBySourceAndSchemaVersionAndNodeIdAndSampleAtBetween(String source,String schema,String node,Instant start,Instant end,Pageable page);
}
interface AlertRepository extends JpaRepository<Alert,Long> {
 List<Alert> findBySourceAndNodeIdAndRuleVersionAndResolvedAtIsNull(String source,String node,String version);
 Page<Alert> findBySourceAndRuleVersion(String source,String version,Pageable page);
}
interface IngestionRepository extends JpaRepository<IngestionState,String> {}
