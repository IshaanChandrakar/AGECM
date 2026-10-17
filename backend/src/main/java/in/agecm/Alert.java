package in.agecm;
import jakarta.persistence.*;
import java.time.Instant;
@Entity @Table(name="alerts")
public class Alert {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) public Long id;
 public String nodeId, source, condition, severity, triggerText;
 public Instant firstOccurredAt, lastOccurredAt, resolvedAt;
 public Long recordId;
 public String ruleVersion;
 public int qualityFlags;
}
