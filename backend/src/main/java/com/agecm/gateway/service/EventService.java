package com.agecm.gateway.service;

import com.agecm.gateway.model.ConsensusEvent;
import com.agecm.gateway.model.FrontEstimation;
import com.agecm.gateway.model.NetworkEvent;
import com.agecm.gateway.repository.ConsensusEventRepository;
import com.agecm.gateway.repository.FrontEstimationRepository;
import com.agecm.gateway.repository.NetworkEventRepository;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * Persists consensus / network / front-estimation events. The Python engine
 * posts these as raw JSON (snake_case), so payloads arrive as Maps and are
 * mapped to entities here — keeps the wire format identical to the engine's.
 */
@Service
public class EventService {

    private final ConsensusEventRepository consensusRepo;
    private final NetworkEventRepository networkRepo;
    private final FrontEstimationRepository frontRepo;
    private final SimpMessagingTemplate ws;

    public EventService(ConsensusEventRepository consensusRepo,
                        NetworkEventRepository networkRepo,
                        FrontEstimationRepository frontRepo,
                        SimpMessagingTemplate ws) {
        this.consensusRepo = consensusRepo;
        this.networkRepo = networkRepo;
        this.frontRepo = frontRepo;
        this.ws = ws;
    }

    public ConsensusEvent saveConsensus(Map<String, Object> m) {
        ConsensusEvent e = new ConsensusEvent();
        e.requestingNode = str(m.get("requesting_node"));
        Object responders = m.get("responders");
        e.responders = responders instanceof List<?> l ? String.join(",", l.stream().map(String::valueOf).toList())
                : str(responders);
        e.repliesReceived = intOf(m.get("replies_received"));
        e.corroborating = intOf(m.get("corroborating"));
        e.confidence = dbl(m.get("confidence"));
        e.sequence = lng(m.get("sequence"));
        e.timestampSim = dbl(m.get("timestamp"));
        e.runId = lng(m.get("runId"));
        return consensusRepo.save(e);
    }

    public NetworkEvent saveNetwork(Map<String, Object> m) {
        NetworkEvent e = new NetworkEvent();
        e.relayNode = str(m.get("relay_node"));
        e.originNode = str(m.get("origin_node"));
        e.nextHop = str(m.get("next_hop"));
        e.hopCount = intOf(m.get("hop_count"));
        e.ttl = intOf(m.get("ttl"));
        e.sequence = lng(m.get("sequence"));
        e.delivered = m.get("delivered") instanceof Boolean b ? b : false;
        e.timestampSim = dbl(m.get("timestamp"));
        e.runId = lng(m.get("runId"));
        return networkRepo.save(e);
    }

    public FrontEstimation saveFront(Map<String, Object> m) {
        FrontEstimation e = new FrontEstimation();
        e.active = m.get("active") instanceof Boolean b && b;
        e.directionX = dbl(m.get("direction_x"));
        e.directionY = dbl(m.get("direction_y"));
        e.bearingDeg = dbl(m.get("bearing_deg"));
        e.progressionSpeed = dbl(m.get("progression_speed"));
        Object sup = m.get("supporting_nodes");
        e.supportingNodes = sup instanceof List<?> l ? String.join(",", l.stream().map(String::valueOf).toList())
                : str(sup);
        e.runId = lng(m.get("runId"));
        frontRepo.save(e);
        ws.convertAndSend("/topic/front", e);
        return e;
    }

    // --- lenient converters (JSON numbers arrive as Integer/Double) ---
    private static String str(Object o) { return o == null ? null : String.valueOf(o); }
    private static Integer intOf(Object o) { return o instanceof Number n ? n.intValue() : null; }
    private static Long lng(Object o) { return o instanceof Number n ? n.longValue() : null; }
    private static Double dbl(Object o) { return o instanceof Number n ? n.doubleValue() : null; }
}
