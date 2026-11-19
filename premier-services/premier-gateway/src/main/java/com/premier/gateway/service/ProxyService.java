package com.premier.gateway.service;

import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
public class ProxyService {

    private final WebClient detectionClient;
    private final WebClient classificationClient;

    public ProxyService(WebClient detectionClient, WebClient classificationClient) {
        this.detectionClient = detectionClient;
        this.classificationClient = classificationClient;
    }

    public Mono<String> callDetection(String path) {
        return detectionClient.get()
                .uri(path)
                .retrieve()
                .bodyToMono(String.class);
    }
}