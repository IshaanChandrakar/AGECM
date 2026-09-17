package com.agecm.gateway.controller;

import com.agecm.gateway.model.NetworkEvent;
import com.agecm.gateway.repository.NetworkEventRepository;
import com.agecm.gateway.service.EventService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/network")
public class NetworkController {

    private final NetworkEventRepository repo;
    private final EventService service;

    public NetworkController(NetworkEventRepository repo, EventService service) {
        this.repo = repo;
        this.service = service;
    }

    @GetMapping
    public List<NetworkEvent> recent() {
        return repo.findTop100ByOrderByIdDesc();
    }

    @PostMapping
    public NetworkEvent add(@RequestBody Map<String, Object> body) {
        return service.saveNetwork(body);
    }
}
