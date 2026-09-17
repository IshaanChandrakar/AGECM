package com.agecm.gateway.controller;

import com.agecm.gateway.dto.TelemetryRequest;
import com.agecm.gateway.model.Telemetry;
import com.agecm.gateway.service.TelemetryService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/telemetry")
public class TelemetryController {

    private final TelemetryService service;

    public TelemetryController(TelemetryService service) {
        this.service = service;
    }

    @PostMapping
    public Telemetry ingest(@Valid @RequestBody TelemetryRequest req) {
        return service.ingest(req);
    }
}
