package com.premier.gateway.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/classification")
@CrossOrigin(origins = "*")
public class ClassificationController {

    private final WebClient classificationClient;

    public ClassificationController(WebClient classificationClient) {
        this.classificationClient = classificationClient;
    }

    @GetMapping("/health")
    public Mono<String> health() {
        return classificationClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Classification service non disponible");
    }

    @PostMapping("/predict")
    public Mono<String> predict(@RequestBody String body) {
        return classificationClient.post()
                .uri("/predict")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Erreur classification");
    }
}