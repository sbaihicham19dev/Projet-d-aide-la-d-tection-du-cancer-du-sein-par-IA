package com.premier.gateway.controller;

import com.premier.gateway.entity.Rapport;
import com.premier.gateway.entity.RapportRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/rapports")
@CrossOrigin(origins = "http://localhost:5173")
public class RapportController {

    private final RapportRepository repo;

    public RapportController(RapportRepository repo) {
        this.repo = repo;
    }

    // GET /api/rapports?medecinId=X — liste les rapports (filtrés ou tous)
    @GetMapping
    public List<Rapport> getAll(@RequestParam(required = false) Long medecinId) {
        if (medecinId != null) {
            return repo.findByMedecinId(medecinId);
        }
        return repo.findAll();
    }

    // POST /api/rapports — enregistre un nouveau rapport
    @PostMapping
    public ResponseEntity<Rapport> create(@RequestBody Map<String, Object> body) {
        Rapport r = new Rapport();
        r.setCin((String) body.get("cin"));
        r.setNom((String) body.get("nom"));
        r.setPrenom((String) body.get("prenom"));
        r.setResultat((String) body.get("resultat"));
        r.setRemarque((String) body.get("remarque"));
        r.setPdfBase64((String) body.get("pdfBase64"));

        if (body.get("confidence") != null)
            r.setConfidence(((Number) body.get("confidence")).doubleValue());
        if (body.get("biradsScore") != null)
            r.setBiradsScore(((Number) body.get("biradsScore")).intValue());
        if (body.get("stade") != null)
            r.setStade((String) body.get("stade"));
        if (body.get("medecinId") != null)
            r.setMedecinId(((Number) body.get("medecinId")).longValue());

        return ResponseEntity.ok(repo.save(r));
    }
}