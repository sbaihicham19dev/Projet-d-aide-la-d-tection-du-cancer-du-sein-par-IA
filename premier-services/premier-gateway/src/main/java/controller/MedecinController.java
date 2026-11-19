package com.premier.gateway.controller;

import com.premier.gateway.entity.Medecin;
import com.premier.gateway.entity.MedecinRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/medecins")
@CrossOrigin(origins = "http://localhost:5173")
public class MedecinController {

    private final MedecinRepository repo;

    public MedecinController(MedecinRepository repo) {
        this.repo = repo;
    }

    // POST /api/medecins/register
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> body) {
        String email = body.get("email");
        if (repo.findByEmail(email).isPresent()) {
            return ResponseEntity.badRequest().body(Map.of("error", "Cet email existe déjà."));
        }
        Medecin m = new Medecin();
        m.setEmail(email);
        m.setPassword(body.get("password"));
        m.setNom(body.get("nom"));
        m.setPrenom(body.get("prenom"));
        m.setRole("medecin"); // tout nouvel inscrit est médecin

        Medecin saved = repo.save(m);
        return ResponseEntity.ok(Map.of(
                "id", saved.getId(),
                "email", saved.getEmail(),
                "name", "Dr. " + saved.getNom(),
                "role", saved.getRole()
        ));
    }

    // POST /api/medecins/login
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> body) {
        Optional<Medecin> match = repo.findByEmail(body.get("email"));
        if (match.isPresent() && match.get().getPassword().equals(body.get("password"))) {
            Medecin m = match.get();
            return ResponseEntity.ok(Map.of(
                    "id", m.getId(),
                    "email", m.getEmail(),
                    "name", "Dr. " + m.getNom(),
                    "role", m.getRole()
            ));
        }
        return ResponseEntity.status(401).body(Map.of("error", "Email ou mot de passe incorrect."));
    }
}