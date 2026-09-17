package com.agecm.gateway.service;

import com.agecm.gateway.model.SimulationRun;
import com.agecm.gateway.repository.*;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.Optional;

/** Simulation-run lifecycle and a reset that clears the live tables. */
@Service
public class SimulationService {

    private final SimulationRunRepository runRepo;
    private final TelemetryRepository telemetryRepo;
    private final NodeRepository nodeRepo;
    private final ConsensusEventRepository consensusRepo;
    private final NetworkEventRepository networkRepo;
    private final AlertRepository alertRepo;
    private final FrontEstimationRepository frontRepo;
    private final SimpMessagingTemplate ws;

    public SimulationService(SimulationRunRepository runRepo, TelemetryRepository telemetryRepo,
                             NodeRepository nodeRepo, ConsensusEventRepository consensusRepo,
                             NetworkEventRepository networkRepo, AlertRepository alertRepo,
                             FrontEstimationRepository frontRepo, SimpMessagingTemplate ws) {
        this.runRepo = runRepo;
        this.telemetryRepo = telemetryRepo;
        this.nodeRepo = nodeRepo;
        this.consensusRepo = consensusRepo;
        this.networkRepo = networkRepo;
        this.alertRepo = alertRepo;
        this.frontRepo = frontRepo;
        this.ws = ws;
    }

    public SimulationRun start(String scenario, Integer nodeCount) {
        SimulationRun r = new SimulationRun();
        r.scenario = scenario;
        r.nodeCount = nodeCount;
        r.status = "RUNNING";
        return runRepo.save(r);
    }

    public Optional<SimulationRun> stop(Long runId) {
        return runRepo.findById(runId).map(r -> {
            r.status = "STOPPED";
            r.stoppedAt = Instant.now();
            return runRepo.save(r);
        });
    }

    /** Clear live tables (keeps simulation_runs history). */
    public void reset() {
        telemetryRepo.deleteAllInBatch();
        consensusRepo.deleteAllInBatch();
        networkRepo.deleteAllInBatch();
        alertRepo.deleteAllInBatch();
        frontRepo.deleteAllInBatch();
        nodeRepo.deleteAllInBatch();
        ws.convertAndSend("/topic/telemetry", Map.of("event", "reset"));
    }
}
