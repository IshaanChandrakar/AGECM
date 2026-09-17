package com.agecm.gateway.model;

import jakarta.persistence.*;
import java.time.Instant;

/** A stored AGECM consensus round result. */
@Entity
@Table(name = "consensus_events")
public class ConsensusEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    public String requestingNode;
    @Column(length = 512)
    public String responders;          // comma-separated node ids
    public Integer repliesReceived;
    public Integer corroborating;
    public Double confidence;          // nullable = undefined
    public Long sequence;
    public Double timestampSim;        // simulated seconds
    public Long runId;
    public Instant createdAt = Instant.now();

    public ConsensusEvent() {}
}
