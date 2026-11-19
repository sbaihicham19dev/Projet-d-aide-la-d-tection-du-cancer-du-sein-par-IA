package com.premier.gateway.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/detection")
@CrossOrigin(origins = "*")
public class DetectionController {

    private final WebClient detectionClient;

    public DetectionController(WebClient detectionClient) {
        this.detectionClient = detectionClient;
    }

    @GetMapping("/health")
    public Mono<String> health() {
        return detectionClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Detection service non disponible");
    }

    @PostMapping("/predict")
    public Mono<String> predict(@RequestBody String body) {
        return detectionClient.post()
                .uri("/predict")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Erreur lors de la détection");
    }
}