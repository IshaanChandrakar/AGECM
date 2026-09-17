package com.agecm.gateway.repository;

import com.agecm.gateway.model.Node;
import org.springframework.data.jpa.repository.JpaRepository;

public interface NodeRepository extends JpaRepository<Node, String> {
}
