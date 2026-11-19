package com.premier.gateway.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/narrative")
@CrossOrigin(origins = "*")
public class LlmNarrativeController {

    private final WebClient llmNarrativeClient;

    public LlmNarrativeController(WebClient llmNarrativeClient) {
        this.llmNarrativeClient = llmNarrativeClient;
    }

    @GetMapping("/health")
    public Mono<String> health() {
        return llmNarrativeClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("LLM Narrative service non disponible");
    }

    @PostMapping("/generate")
    public Mono<String> generate(@RequestBody String body) {
        return llmNarrativeClient.post()
                .uri("/generate")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Erreur génération narrative");
    }
}