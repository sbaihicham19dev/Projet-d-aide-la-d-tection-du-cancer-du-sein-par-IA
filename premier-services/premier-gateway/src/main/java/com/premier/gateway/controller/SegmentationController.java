package com.premier.gateway.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/segmentation")
@CrossOrigin(origins = "*")
public class SegmentationController {

    private final WebClient segmentationClient;

    public SegmentationController(WebClient segmentationClient) {
        this.segmentationClient = segmentationClient;
    }

    @GetMapping("/health")
    public Mono<String> health() {
        return segmentationClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Segmentation service non disponible");
    }

    @PostMapping("/segment")
    public Mono<String> segment(@RequestBody String body) {
        return segmentationClient.post()
                .uri("/segment")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Erreur segmentation");
    }
}