package in.agecm;
import java.time.Instant;
import java.util.*;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.JpaRepository;
interface TelemetryRepository extends JpaRepository<Telemetry,Long> {
 boolean existsByUniqueKeyOrSourceKey(String key,String sourceKey);
 Optional<Telemetry> findFirstByNodeIdAndSourceOrderByAcquiredAtDescIdDesc(String node,String source);
 Page<Telemetry> findBySourceAndAcquiredAtBetween(String source,Instant start,Instant end,Pageable page);
 Page<Telemetry> findBySourceAndNodeIdAndAcquiredAtBetween(String source,String node,Instant start,Instant end,Pageable page);
}
interface AlertRepository extends JpaRepository<Alert,Long> {
 List<Alert> findBySourceAndNodeIdAndResolvedAtIsNull(String source,String node);
 Page<Alert> findBySource(String source,Pageable page);
}
interface IngestionRepository extends JpaRepository<IngestionState,String> {}
