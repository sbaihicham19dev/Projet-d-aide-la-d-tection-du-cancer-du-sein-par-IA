package com.premier.gateway.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/birads")
@CrossOrigin(origins = "*")
public class BiRadsController {

    private final WebClient biradsClient;

    public BiRadsController(WebClient biradsClient) {
        this.biradsClient = biradsClient;
    }

    @GetMapping("/health")
    public Mono<String> health() {
        return biradsClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("BI-RADS service non disponible");
    }

    @PostMapping("/analyze")
    public Mono<String> analyze(@RequestBody String body) {
        return biradsClient.post()
                .uri("/analyze")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Erreur BI-RADS");
    }
}