package com.agecm.gateway.dto;

import jakarta.validation.constraints.NotBlank;

/** Incoming telemetry payload from the Python engine (POST /api/telemetry). */
public class TelemetryRequest {
    @NotBlank
    public String nodeId;
    public String timestamp;            // ISO-8601; parsed to Instant
    public Double tiltRate;
    public Double displacementVelocity;
    public Double vibration;
    public String state;
    public Double consensusConfidence;  // nullable = undefined
    public Double samplingInterval;
    public Integer spreadingFactor;
    public Integer txPowerDbm;
    public String nextHop;
    public Long sequence;
    public Integer hopCount;
    public Long runId;
}
