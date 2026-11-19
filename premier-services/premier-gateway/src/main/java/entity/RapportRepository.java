package com.premier.gateway.entity;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface RapportRepository extends JpaRepository<Rapport, Long> {
    List<Rapport> findByMedecinId(Long medecinId);
}