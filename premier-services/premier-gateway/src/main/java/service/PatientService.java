package com.premier.gateway.service;

import com.premier.gateway.entity.Patient;

import java.util.List;
import java.util.Optional;

public interface PatientService {

    Patient savePatient(Patient patient);

    List<Patient> getAllPatients();

    Optional<Patient> getPatientById(Long id);

    Optional<Patient> getPatientByCin(String cin);

    void deletePatient(Long id);
}