package com.agecm.gateway.controller;

import com.agecm.gateway.model.FrontEstimation;
import com.agecm.gateway.repository.FrontEstimationRepository;
import com.agecm.gateway.service.EventService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/front-estimation")
public class FrontEstimationController {

    private final FrontEstimationRepository repo;
    private final EventService service;

    public FrontEstimationController(FrontEstimationRepository repo, EventService service) {
        this.repo = repo;
        this.service = service;
    }

    /** Latest front estimate (empty object if none yet). */
    @GetMapping
    public Object latest() {
        FrontEstimation f = repo.findTopByOrderByIdDesc();
        return f == null ? Map.of("active", false) : f;
    }

    @PostMapping
    public FrontEstimation add(@RequestBody Map<String, Object> body) {
        return service.saveFront(body);
    }
}
