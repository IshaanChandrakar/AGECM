package com.agecm.gateway.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.time.Instant;

/** Current state of one mesh node (latest telemetry snapshot). */
@Entity
public class Node {
    @Id
    public String nodeId;

    public String state = "NORMAL";
    public Double tiltRate;
    public Double displacementVelocity;
    public Double vibration;
    public Double consensusConfidence;
    public Double samplingInterval;
    public Integer spreadingFactor;
    public Integer txPowerDbm;
    public String nextHop;
    public Long lastSequence;
    public Instant lastSeen;

    public Node() {}
}
