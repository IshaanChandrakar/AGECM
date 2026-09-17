package com.agecm.gateway.repository;

import com.agecm.gateway.model.NetworkEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface NetworkEventRepository extends JpaRepository<NetworkEvent, Long> {
    List<NetworkEvent> findTop100ByOrderByIdDesc();
}
