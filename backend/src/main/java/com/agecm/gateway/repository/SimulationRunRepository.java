package com.agecm.gateway.repository;

import com.agecm.gateway.model.SimulationRun;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SimulationRunRepository extends JpaRepository<SimulationRun, Long> {
}
