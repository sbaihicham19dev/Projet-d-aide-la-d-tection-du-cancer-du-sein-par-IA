package com.premier.gateway.controller;

import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/pipeline")
@CrossOrigin(origins = "*")
public class PipelineController {

    private final WebClient detectionClient;

    public PipelineController(WebClient detectionClient) {
        this.detectionClient = detectionClient;
    }

    @PostMapping(value = "/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Mono<String> analyze(@RequestParam("file") MultipartFile file) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        try {
            builder.part("file", file.getResource());
        } catch (Exception e) {
            return Mono.just("Erreur lecture fichier: " + e.getMessage());
        }

        return detectionClient.post()
                .uri("/api/v1/predict")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(String.class)
                .onErrorResume(e -> Mono.just("Erreur pipeline: " + e.getMessage()));
    }

    @PostMapping(value = "/analyze/gradcam", consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            produces = MediaType.TEXT_HTML_VALUE)
    public Mono<String> analyzeGradcam(@RequestParam("file") MultipartFile file) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        try {
            builder.part("file", file.getResource());
        } catch (Exception e) {
            return Mono.just("Erreur lecture fichier: " + e.getMessage());
        }

        return detectionClient.post()
                .uri("/api/v1/predict/gradcam")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(String.class)
                .onErrorResume(e -> Mono.just("Erreur gradcam: " + e.getMessage()));
    }

    @GetMapping("/health-all")
    public Mono<String> healthAll() {
        return detectionClient.get()
                .uri("/api/v1/health")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorResume(e -> Mono.just("{\"detection\": \"DOWN\"}"));
    }
}