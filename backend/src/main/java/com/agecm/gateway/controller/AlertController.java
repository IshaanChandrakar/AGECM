package com.agecm.gateway.controller;

import com.agecm.gateway.model.Alert;
import com.agecm.gateway.repository.AlertRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/alerts")
public class AlertController {

    private final AlertRepository alertRepo;

    public AlertController(AlertRepository alertRepo) {
        this.alertRepo = alertRepo;
    }

    @GetMapping
    public List<Alert> all() {
        return alertRepo.findByOrderByActiveDescIdDesc();
    }
}
