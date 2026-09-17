package com.agecm.gateway.model;

import jakarta.persistence.*;
import java.time.Instant;

/** A stored linear front-estimation result (Review 2 prototype). */
@Entity
@Table(name = "front_estimations")
public class FrontEstimation {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    public boolean active;
    public Double directionX;
    public Double directionY;
    public Double bearingDeg;
    public Double progressionSpeed;
    @Column(length = 512)
    public String supportingNodes;     // comma-separated
    public Long runId;
    public Instant createdAt = Instant.now();

    public FrontEstimation() {}
}
