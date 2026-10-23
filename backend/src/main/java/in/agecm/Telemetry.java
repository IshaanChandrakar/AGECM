package in.agecm;
import jakarta.persistence.*;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.Instant;
@Entity @Table(name="telemetry")
public class Telemetry extends TelemetryInput {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) public Long id;
 @JsonIgnore public String uniqueKey;
 @JsonIgnore public String sourceKey;
 public Instant receivedAt, sampleAt;
 public String timestampBasis, health;
}
