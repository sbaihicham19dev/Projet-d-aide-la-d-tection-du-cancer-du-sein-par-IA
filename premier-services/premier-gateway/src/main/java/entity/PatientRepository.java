package com.premier.gateway.repository;

import com.premier.gateway.entity.Patient;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PatientRepository extends JpaRepository<Patient, Long> {

    // Optionnel mais utile : rechercher par CIN
    Optional<Patient> findByCin(String cin);
}