package com.agecm.gateway.model;

import jakarta.persistence.*;
import java.time.Instant;

/** Records the lifecycle of one simulation run. */
@Entity
@Table(name = "simulation_runs")
public class SimulationRun {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    public String scenario;
    public Integer nodeCount;
    public String status = "RUNNING";
    public Instant startedAt = Instant.now();
    public Instant stoppedAt;

    public SimulationRun() {}
}
