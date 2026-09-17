package com.agecm.gateway.model;

import jakarta.persistence.*;
import java.time.Instant;

/** An alert raised when a node reports CRITICAL. */
@Entity
@Table(name = "alerts")
public class Alert {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    public String nodeId;
    public String state;
    public Long sequence;
    public Double timestampSim;
    public boolean active = true;
    public Instant createdAt = Instant.now();

    public Alert() {}
}
