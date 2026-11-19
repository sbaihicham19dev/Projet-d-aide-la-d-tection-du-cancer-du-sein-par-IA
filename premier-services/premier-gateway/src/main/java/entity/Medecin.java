package com.premier.gateway.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "medecins")
public class Medecin {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String email;

    private String password;
    private String nom;
    private String prenom;
    private String role; // "admin" ou "medecin"

    // Getters & Setters
    public Long getId() { return id; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    public String getNom() { return nom; }
    public void setNom(String nom) { this.nom = nom; }
    public String getPrenom() { return prenom; }
    public void setPrenom(String prenom) { this.prenom = prenom; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
}