package com.agecm.gateway.model;

import jakarta.persistence.*;
import java.time.Instant;

/** One stored telemetry packet from a node. */
@Entity
@Table(name = "telemetry", indexes = {
        @Index(name = "idx_tel_node", columnList = "nodeId"),
        @Index(name = "idx_tel_time", columnList = "timestamp")
})
public class Telemetry {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    public String nodeId;
    public Instant timestamp;
    public Double tiltRate;
    public Double displacementVelocity;
    public Double vibration;
    public String state;
    public Double consensusConfidence;   // nullable = undefined
    public Double samplingInterval;
    public Integer spreadingFactor;
    public Integer txPowerDbm;
    public String nextHop;
    public Long sequence;
    public Integer hopCount;
    public Long runId;

    public Telemetry() {}
}
