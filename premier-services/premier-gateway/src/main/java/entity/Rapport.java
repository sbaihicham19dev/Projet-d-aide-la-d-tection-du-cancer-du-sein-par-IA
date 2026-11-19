package com.premier.gateway.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "rapports")
public class Rapport {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long medecinId;

    private String cin;
    private String nom;
    private String prenom;
    private String resultat;
    private Double confidence;
    private Integer biradsScore;
    private String stade;

    @Column(columnDefinition = "TEXT")
    private String remarque;

    @Column(columnDefinition = "TEXT")
    private String pdfBase64;

    private LocalDateTime createdAt = LocalDateTime.now();

    public Long getId() { return id; }
    public Long getMedecinId() { return medecinId; }
    public void setMedecinId(Long medecinId) { this.medecinId = medecinId; }
    public String getCin() { return cin; }
    public void setCin(String cin) { this.cin = cin; }
    public String getNom() { return nom; }
    public void setNom(String nom) { this.nom = nom; }
    public String getPrenom() { return prenom; }
    public void setPrenom(String prenom) { this.prenom = prenom; }
    public String getResultat() { return resultat; }
    public void setResultat(String resultat) { this.resultat = resultat; }
    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }
    public Integer getBiradsScore() { return biradsScore; }
    public void setBiradsScore(Integer biradsScore) { this.biradsScore = biradsScore; }
    public String getStade() { return stade; }
    public void setStade(String stade) { this.stade = stade; }
    public String getRemarque() { return remarque; }
    public void setRemarque(String remarque) { this.remarque = remarque; }
    public String getPdfBase64() { return pdfBase64; }
    public void setPdfBase64(String pdfBase64) { this.pdfBase64 = pdfBase64; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}