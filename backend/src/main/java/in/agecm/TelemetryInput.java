package in.agecm;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.time.Instant;

@MappedSuperclass
public class TelemetryInput {
 @NotBlank @Pattern(regexp="node_0[12]") public String nodeId;
 @NotNull @Pattern(regexp="demo|cloud_hardware") public String source;
 @NotNull @Pattern(regexp="1.0") public String schemaVersion;
 @NotBlank @Size(max=100) public String bootId;
 @NotNull @PositiveOrZero public Long sequence;
 @Size(max=40) public String channelId;
 @Positive public Long entryId;
 @NotNull public Instant acquiredAt;
 public Instant cloudCreatedAt;
 @PositiveOrZero public Long uptimeMs;
 public Double tilt, displacement, vibration, tiltRate, displacementVelocity;
 @NotNull @Min(0) public Integer qualityFlags;
 public boolean calibrated, featureReady;
 @Positive public Integer sampleIntervalMs;
 @Positive public Integer reportIntervalSeconds;
 @NotBlank @Size(max=60) public String ruleVersion;
 @NotNull @Pattern(regexp="NORMAL|WARNING|CRITICAL|UNAVAILABLE") public String state;
 @NotNull @Pattern(regexp="HEALTHY|INVALID_SENSOR|NOT_READY") public String health;
}
