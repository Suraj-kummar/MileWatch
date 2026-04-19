package com.milewatch.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

/**
 * RestTemplate Configuration for ML Service Communication
 *
 * WHY RestTemplate (not WebClient):
 * - Synchronous is fine for our use case (each request waits for ML score anyway)
 * - Simpler to debug and reason about
 * - Spring Boot auto-configures RestTemplateBuilder
 *
 * TIMEOUT STRATEGY:
 * - Connect timeout: 5s — if Flask isn't reachable, fail fast
 * - Read timeout: 10s — SHAP computation can take a few seconds under load
 */
@Configuration
public class RestTemplateConfig {

    @Value("${ml-service.connect-timeout-ms:5000}")
    private int connectTimeout;

    @Value("${ml-service.read-timeout-ms:10000}")
    private int readTimeout;

    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder
                .connectTimeout(Duration.ofMillis(connectTimeout))
                .readTimeout(Duration.ofMillis(readTimeout))
                .build();
    }
}
