package com.premier.gateway.controller;

import com.premier.gateway.entity.Patient;
import com.premier.gateway.service.PatientService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/patients")
@CrossOrigin(origins = "*")
public class PatientController {

    private final PatientService patientService;

    public PatientController(PatientService patientService) {
        this.patientService = patientService;
    }

    // ================= CREATE =================
    @PostMapping
    public ResponseEntity<Patient> createPatient(@RequestBody Patient patient) {
        Patient saved = patientService.savePatient(patient);
        return ResponseEntity.ok(saved);
    }

    // ================= GET ALL =================
    @GetMapping
    public ResponseEntity<List<Patient>> getAllPatients() {
        return ResponseEntity.ok(patientService.getAllPatients());
    }

    // ================= GET BY ID =================
    @GetMapping("/{id}")
    public ResponseEntity<Patient> getPatientById(@PathVariable Long id) {
        Optional<Patient> patient = patientService.getPatientById(id);
        return patient.map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    // ================= GET BY CIN =================
    @GetMapping("/cin/{cin}")
    public ResponseEntity<Patient> getPatientByCin(@PathVariable String cin) {
        Optional<Patient> patient = patientService.getPatientByCin(cin);
        return patient.map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    // ================= DELETE =================
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deletePatient(@PathVariable Long id) {
        patientService.deletePatient(id);
        return ResponseEntity.noContent().build();
    }
}