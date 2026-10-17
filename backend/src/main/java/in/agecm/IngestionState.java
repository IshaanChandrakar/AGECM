package in.agecm;
import jakarta.persistence.*;
import java.time.Instant;
@Entity @Table(name="ingestion_state")
public class IngestionState {
 @Id public String nodeId;
 public String channelId;
 public long lastEntryId;
 public Instant lastSuccessAt, lastPollAt;
 public String status, lastError;
 public int knownGaps;
}
