package in.agecm;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.time.Instant;
@MappedSuperclass
public class TelemetryInput {
 @NotBlank @Pattern(regexp="node_0[12]") public String nodeId;
 @NotNull @Pattern(regexp="demo|cloud_hardware") public String source;
 @NotNull @Pattern(regexp="2\\.0") public String schemaVersion;
 @Size(max=100) public String bootId;
 @PositiveOrZero public Long sequence;
 @Size(max=40) public String channelId;
 @Positive public Long entryId;
 public Instant acquiredAt, cloudCreatedAt;
 public Double temperature, humidity, coMax, distanceNow, devMax, rawDistanceNow;
 @Column(name="ch4_max") public Double ch4Max;
 public Integer statusWorst;
 @Min(0) @Max(1) public Integer faultAny;
 @Size(max=2000) @Column(length=2000) public String fieldIssues;
 @Size(max=2000) @Column(length=2000) public String statusText;
}
