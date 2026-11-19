package com.premier.gateway.entity;

import jakarta.persistence.*;
import java.time.LocalDate;

@Entity
@Table(name = "patients")
public class Patient {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String cin;

    @Column(nullable = false)
    private String nom;

    @Column(nullable = false)
    private String prenom;

    @Column(nullable = false)
    private String telephone;

    @Column(name = "date_naissance")
    private LocalDate dateNaissance;

    @Column(name = "date_examen")
    private LocalDate dateExamen;

    @Column(name = "cote_examine")
    private String coteExamine; // gauche / droite

    // ===== Constructors =====

    public Patient() {
    }

    public Patient(String cin, String nom, String prenom, String telephone,
                   LocalDate dateNaissance, LocalDate dateExamen, String coteExamine) {
        this.cin = cin;
        this.nom = nom;
        this.prenom = prenom;
        this.telephone = telephone;
        this.dateNaissance = dateNaissance;
        this.dateExamen = dateExamen;
        this.coteExamine = coteExamine;
    }

    // ===== Getters & Setters =====

    public Long getId() {
        return id;
    }

    public String getCin() {
        return cin;
    }

    public void setCin(String cin) {
        this.cin = cin;
    }

    public String getNom() {
        return nom;
    }

    public void setNom(String nom) {
        this.nom = nom;
    }

    public String getPrenom() {
        return prenom;
    }

    public void setPrenom(String prenom) {
        this.prenom = prenom;
    }

    public String getTelephone() {
        return telephone;
    }

    public void setTelephone(String telephone) {
        this.telephone = telephone;
    }

    public LocalDate getDateNaissance() {
        return dateNaissance;
    }

    public void setDateNaissance(LocalDate dateNaissance) {
        this.dateNaissance = dateNaissance;
    }

    public LocalDate getDateExamen() {
        return dateExamen;
    }

    public void setDateExamen(LocalDate dateExamen) {
        this.dateExamen = dateExamen;
    }

    public String getCoteExamine() {
        return coteExamine;
    }

    public void setCoteExamine(String coteExamine) {
        this.coteExamine = coteExamine;
    }
}