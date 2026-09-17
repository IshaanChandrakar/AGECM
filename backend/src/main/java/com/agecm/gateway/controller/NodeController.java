package com.agecm.gateway.controller;

import com.agecm.gateway.model.Node;
import com.agecm.gateway.model.Telemetry;
import com.agecm.gateway.repository.NodeRepository;
import com.agecm.gateway.repository.TelemetryRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/nodes")
public class NodeController {

    private final NodeRepository nodeRepo;
    private final TelemetryRepository telemetryRepo;

    public NodeController(NodeRepository nodeRepo, TelemetryRepository telemetryRepo) {
        this.nodeRepo = nodeRepo;
        this.telemetryRepo = telemetryRepo;
    }

    @GetMapping
    public List<Node> all() {
        return nodeRepo.findAll();
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> one(@PathVariable String id) {
        return nodeRepo.findById(id)
                .<ResponseEntity<?>>map(n -> {
                    List<Telemetry> recent =
                            telemetryRepo.findByNodeIdOrderByIdDesc(id, PageRequest.of(0, 50));
                    return ResponseEntity.ok(Map.of("node", n, "recentTelemetry", recent));
                })
                .orElse(ResponseEntity.notFound().build());
    }
}
