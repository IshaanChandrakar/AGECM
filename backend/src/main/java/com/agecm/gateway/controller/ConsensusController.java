package com.agecm.gateway.controller;

import com.agecm.gateway.model.ConsensusEvent;
import com.agecm.gateway.repository.ConsensusEventRepository;
import com.agecm.gateway.service.EventService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/consensus")
public class ConsensusController {

    private final ConsensusEventRepository repo;
    private final EventService service;

    public ConsensusController(ConsensusEventRepository repo, EventService service) {
        this.repo = repo;
        this.service = service;
    }

    @GetMapping
    public List<ConsensusEvent> recent() {
        return repo.findTop100ByOrderByIdDesc();
    }

    @PostMapping
    public ConsensusEvent add(@RequestBody Map<String, Object> body) {
        return service.saveConsensus(body);
    }
}
