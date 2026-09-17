package com.agecm.gateway.repository;

import com.agecm.gateway.model.Alert;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AlertRepository extends JpaRepository<Alert, Long> {
    List<Alert> findByOrderByActiveDescIdDesc();
}
