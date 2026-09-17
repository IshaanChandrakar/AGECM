package com.agecm.gateway.repository;

import com.agecm.gateway.model.ConsensusEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ConsensusEventRepository extends JpaRepository<ConsensusEvent, Long> {
    List<ConsensusEvent> findTop100ByOrderByIdDesc();
}
