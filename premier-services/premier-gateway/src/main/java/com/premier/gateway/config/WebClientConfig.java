package com.premier.gateway.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Value("${services.detection}")
    private String detectionUrl;

    @Value("${services.classification}")
    private String classificationUrl;

    @Value("${services.segmentation}")
    private String segmentationUrl;

    @Value("${services.birads}")
    private String biradsUrl;

    @Value("${services.assembler}")
    private String assemblerUrl;

    @Value("${services.llm-narrative}")
    private String llmNarrativeUrl;

    private ExchangeStrategies largeBuffer() {
        return ExchangeStrategies.builder()
                .codecs(config -> config.defaultCodecs()
                        .maxInMemorySize(100 * 1024 * 1024)) // 100MB au lieu de 10MB
                .build();
    }

    @Bean
    public WebClient detectionClient() {
        return WebClient.builder()
                .baseUrl(detectionUrl)
                .exchangeStrategies(largeBuffer())
                .build();
    }

    @Bean
    public WebClient classificationClient() {
        return WebClient.builder()
                .baseUrl(classificationUrl)
                .exchangeStrategies(largeBuffer())
                .build();
    }

    @Bean
    public WebClient segmentationClient() {
        return WebClient.builder()
                .baseUrl(segmentationUrl)
                .exchangeStrategies(largeBuffer())
                .build();
    }

    @Bean
    public WebClient biradsClient() {
        return WebClient.builder()
                .baseUrl(biradsUrl)
                .exchangeStrategies(largeBuffer())
                .build();
    }

    @Bean
    public WebClient assemblerClient() {
        return WebClient.builder()
                .baseUrl(assemblerUrl)
                .exchangeStrategies(largeBuffer())
                .build();
    }

    @Bean
    public WebClient llmNarrativeClient() {
        return WebClient.builder()
                .baseUrl(llmNarrativeUrl)
                .exchangeStrategies(largeBuffer())
                .build();
    }
}