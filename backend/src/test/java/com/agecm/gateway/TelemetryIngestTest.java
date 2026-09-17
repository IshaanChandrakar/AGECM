package com.agecm.gateway;

import com.agecm.gateway.dto.TelemetryRequest;
import com.agecm.gateway.model.Node;
import com.agecm.gateway.repository.AlertRepository;
import com.agecm.gateway.repository.NodeRepository;
import com.agecm.gateway.service.TelemetryService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/** Verifies telemetry ingest persists a node snapshot and raises a CRITICAL alert. */
@SpringBootTest
@Transactional
class TelemetryIngestTest {

    @Autowired TelemetryService telemetryService;
    @Autowired NodeRepository nodeRepo;
    @Autowired AlertRepository alertRepo;

    @Test
    void contextLoadsAndIngestsTelemetry() {
        TelemetryRequest req = new TelemetryRequest();
        req.nodeId = "node_01";
        req.timestamp = "2026-09-17T10:00:00+00:00";
        req.tiltRate = 0.031;
        req.state = "WARNING";
        req.consensusConfidence = 0.75;
        req.samplingInterval = 5.0;
        req.spreadingFactor = 12;
        req.txPowerDbm = 14;
        req.nextHop = "node_02";
        req.sequence = 1L;

        telemetryService.ingest(req);

        Optional<Node> n = nodeRepo.findById("node_01");
        assertTrue(n.isPresent());
        assertEquals("WARNING", n.get().state);
        assertEquals(0L, alertRepo.count());   // WARNING raises no alert
    }

    @Test
    void criticalRaisesAlert() {
        TelemetryRequest req = new TelemetryRequest();
        req.nodeId = "node_09";
        req.timestamp = "2026-09-17T10:00:01+00:00";
        req.tiltRate = 0.2;
        req.state = "CRITICAL";
        req.sequence = 2L;

        telemetryService.ingest(req);

        assertTrue(alertRepo.count() >= 1);
    }
}
