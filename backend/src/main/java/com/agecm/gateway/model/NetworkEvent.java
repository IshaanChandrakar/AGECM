package com.agecm.gateway.model;

import jakarta.persistence.*;
import java.time.Instant;

/** A stored two-hop forwarding / network event. */
@Entity
@Table(name = "network_events")
public class NetworkEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    public String relayNode;
    public String originNode;
    public String nextHop;
    public Integer hopCount;
    public Integer ttl;
    public Long sequence;
    public Boolean delivered;
    public Double timestampSim;
    public Long runId;
    public Instant createdAt = Instant.now();

    public NetworkEvent() {}
}
