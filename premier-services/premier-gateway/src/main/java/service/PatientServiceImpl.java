package com.premier.gateway.service;

import com.premier.gateway.entity.Patient;
import com.premier.gateway.repository.PatientRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class PatientServiceImpl implements PatientService {

    private final PatientRepository patientRepository;

    public PatientServiceImpl(PatientRepository patientRepository) {
        this.patientRepository = patientRepository;
    }

    @Override
    public Patient savePatient(Patient patient) {
        return patientRepository.save(patient);
    }

    @Override
    public List<Patient> getAllPatients() {
        return patientRepository.findAll();
    }

    @Override
    public Optional<Patient> getPatientById(Long id) {
        return patientRepository.findById(id);
    }

    @Override
    public Optional<Patient> getPatientByCin(String cin) {
        return patientRepository.findByCin(cin);
    }

    @Override
    public void deletePatient(Long id) {
        patientRepository.deleteById(id);
    }
}