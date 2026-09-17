package com.agecm.gateway.repository;

import com.agecm.gateway.model.Telemetry;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TelemetryRepository extends JpaRepository<Telemetry, Long> {
    List<Telemetry> findByNodeIdOrderByIdDesc(String nodeId, Pageable page);
    List<Telemetry> findTop200ByOrderByIdDesc();
}
