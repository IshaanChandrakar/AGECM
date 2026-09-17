package com.agecm.gateway.repository;

import com.agecm.gateway.model.FrontEstimation;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FrontEstimationRepository extends JpaRepository<FrontEstimation, Long> {
    FrontEstimation findTopByOrderByIdDesc();
}
