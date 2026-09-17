package com.agecm.gateway.service;

import com.agecm.gateway.dto.TelemetryRequest;
import com.agecm.gateway.model.Alert;
import com.agecm.gateway.model.Node;
import com.agecm.gateway.model.Telemetry;
import com.agecm.gateway.repository.AlertRepository;
import com.agecm.gateway.repository.NodeRepository;
import com.agecm.gateway.repository.TelemetryRepository;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;

/**
 * Ingests telemetry: persists it, updates the node snapshot, raises an alert on
 * CRITICAL, and broadcasts live updates to the dashboard over WebSocket.
 */
@Service
public class TelemetryService {

    private final TelemetryRepository telemetryRepo;
    private final NodeRepository nodeRepo;
    private final AlertRepository alertRepo;
    private final SimpMessagingTemplate ws;

    public TelemetryService(TelemetryRepository telemetryRepo, NodeRepository nodeRepo,
                            AlertRepository alertRepo, SimpMessagingTemplate ws) {
        this.telemetryRepo = telemetryRepo;
        this.nodeRepo = nodeRepo;
        this.alertRepo = alertRepo;
        this.ws = ws;
    }

    public Telemetry ingest(TelemetryRequest req) {
        Instant ts = parse(req.timestamp);

        Telemetry t = new Telemetry();
        t.nodeId = req.nodeId;
        t.timestamp = ts;
        t.tiltRate = req.tiltRate;
        t.displacementVelocity = req.displacementVelocity;
        t.vibration = req.vibration;
        t.state = req.state;
        t.consensusConfidence = req.consensusConfidence;
        t.samplingInterval = req.samplingInterval;
        t.spreadingFactor = req.spreadingFactor;
        t.txPowerDbm = req.txPowerDbm;
        t.nextHop = req.nextHop;
        t.sequence = req.sequence;
        t.hopCount = req.hopCount;
        t.runId = req.runId;
        telemetryRepo.save(t);

        // Upsert node snapshot.
        Node n = nodeRepo.findById(req.nodeId).orElseGet(Node::new);
        n.nodeId = req.nodeId;
        n.state = req.state;
        n.tiltRate = req.tiltRate;
        n.displacementVelocity = req.displacementVelocity;
        n.vibration = req.vibration;
        n.consensusConfidence = req.consensusConfidence;
        n.samplingInterval = req.samplingInterval;
        n.spreadingFactor = req.spreadingFactor;
        n.txPowerDbm = req.txPowerDbm;
        n.nextHop = req.nextHop;
        n.lastSequence = req.sequence;
        n.lastSeen = ts;
        nodeRepo.save(n);

        // Alert on CRITICAL.
        if ("CRITICAL".equals(req.state)) {
            Alert a = new Alert();
            a.nodeId = req.nodeId;
            a.state = req.state;
            a.sequence = req.sequence;
            a.active = true;
            alertRepo.save(a);
            ws.convertAndSend("/topic/alerts", a);
        }

        // Live push to dashboard.
        ws.convertAndSend("/topic/telemetry", t);
        return t;
    }

    private static Instant parse(String iso) {
        if (iso == null) return Instant.now();
        try {
            // Python emits offsets like +00:00; OffsetDateTime handles those.
            return java.time.OffsetDateTime.parse(iso).toInstant();
        } catch (Exception ignore) {
            try {
                return Instant.parse(iso);   // handles trailing 'Z'
            } catch (Exception e) {
                return Instant.now();
            }
        }
    }
}
