package com.agecm.gateway.controller;

import com.agecm.gateway.model.SimulationRun;
import com.agecm.gateway.service.SimulationService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/simulation")
public class SimulationController {

    private final SimulationService service;

    public SimulationController(SimulationService service) {
        this.service = service;
    }

    @PostMapping("/start")
    public Map<String, Object> start(@RequestBody Map<String, Object> body) {
        String scenario = (String) body.getOrDefault("scenario", "unknown");
        Integer nodeCount = body.get("nodeCount") instanceof Number n ? n.intValue() : null;
        SimulationRun r = service.start(scenario, nodeCount);
        return Map.of("runId", r.id, "scenario", r.scenario, "status", r.status);
    }

    @PostMapping("/stop")
    public Map<String, Object> stop(@RequestBody Map<String, Object> body) {
        Long runId = body.get("runId") instanceof Number n ? n.longValue() : null;
        return service.stop(runId)
                .<Map<String, Object>>map(r -> Map.of("runId", r.id, "status", r.status))
                .orElse(Map.of("status", "not_found"));
    }

    @PostMapping("/reset")
    public Map<String, String> reset() {
        service.reset();
        return Map.of("status", "reset");
    }
}
