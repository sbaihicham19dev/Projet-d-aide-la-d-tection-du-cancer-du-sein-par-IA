package com.premier.gateway.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/assembler")
@CrossOrigin(origins = "*")
public class AssemblerController {

    private final WebClient assemblerClient;

    public AssemblerController(WebClient assemblerClient) {
        this.assemblerClient = assemblerClient;
    }

    @GetMapping("/health")
    public Mono<String> health() {
        return assemblerClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Assembler service non disponible");
    }

    @PostMapping("/assemble")
    public Mono<String> assemble(@RequestBody String body) {
        return assemblerClient.post()
                .uri("/assemble")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(String.class)
                .onErrorReturn("Erreur assembler");
    }
}