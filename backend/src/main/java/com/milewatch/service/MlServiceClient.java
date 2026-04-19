package com.milewatch.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.milewatch.model.CredibilityResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * HTTP Client for the Flask ML Microservice.
 *
 * WHY A DEDICATED CLIENT (not inline RestTemplate calls):
 * - Encapsulates retry logic, error handling, and response mapping
 * - Single place to change if Flask API contract changes
 * - Testable in isolation with a mock RestTemplate
 *
 * RETRY STRATEGY:
 * - 2 retries with simple backoff (500ms, 1000ms)
 * - Only retries on connection errors, not on 4xx/5xx responses
 * - If all retries fail, throws MlServiceUnavailableException
 */
@Service
public class MlServiceClient {

    private static final Logger log = LoggerFactory.getLogger(MlServiceClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final int maxRetries;
    private final ObjectMapper objectMapper;

    public MlServiceClient(
            RestTemplate restTemplate,
            @Value("${ml-service.base-url}") String baseUrl,
            @Value("${ml-service.max-retries:2}") int maxRetries) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
        this.maxRetries = maxRetries;

        // Flask uses snake_case, Spring uses camelCase
        this.objectMapper = new ObjectMapper();
        this.objectMapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
    }

    /**
     * Check if the Flask ML service is healthy and ready.
     */
    public boolean isHealthy() {
        try {
            String response = restTemplate.getForObject(baseUrl + "/health", String.class);
            return response != null && response.contains("healthy");
        } catch (RestClientException e) {
            log.warn("ML service health check failed: {}", e.getMessage());
            return false;
        }
    }

    /**
     * Score a single delivery attempt via the Flask /predict endpoint.
     *
     * @param features Map of feature name → value (snake_case keys matching Flask API)
     * @return CredibilityResult with score, risk level, reasons, dispute draft
     * @throws MlServiceUnavailableException if Flask is unreachable after retries
     */
    public CredibilityResult predict(Map<String, Object> features) {
        String url = baseUrl + "/predict";

        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                log.debug("Calling ML service: attempt {}/{}", attempt + 1, maxRetries + 1);

                // Post features to Flask and get raw JSON response
                @SuppressWarnings("unchecked")
                Map<String, Object> rawResponse = restTemplate.postForObject(
                        url, features, Map.class);

                if (rawResponse == null) {
                    throw new RuntimeException("Null response from ML service");
                }

                return mapToCredibilityResult(rawResponse);

            } catch (ResourceAccessException e) {
                // Connection error — retry
                log.warn("ML service connection failed (attempt {}/{}): {}",
                        attempt + 1, maxRetries + 1, e.getMessage());

                if (attempt < maxRetries) {
                    sleep(500L * (attempt + 1));  // Simple backoff: 500ms, 1000ms
                } else {
                    throw new MlServiceUnavailableException(
                            "ML service unavailable after " + (maxRetries + 1) + " attempts", e);
                }
            } catch (RestClientException e) {
                // Non-connection error (4xx, 5xx) — don't retry
                log.error("ML service returned error: {}", e.getMessage());
                throw new MlServiceUnavailableException("ML service error: " + e.getMessage(), e);
            }
        }

        // Should never reach here
        throw new MlServiceUnavailableException("ML service unavailable");
    }

    /**
     * Map the raw Flask response map to a CredibilityResult object.
     */
    @SuppressWarnings("unchecked")
    private CredibilityResult mapToCredibilityResult(Map<String, Object> raw) {
        CredibilityResult result = new CredibilityResult();

        // Score
        Object scoreObj = raw.get("credibility_score");
        result.setCredibilityScore(scoreObj != null ? ((Number) scoreObj).doubleValue() : null);

        // Risk level
        result.setRiskLevel((String) raw.get("risk_level"));

        // Reasons (list of maps)
        Object reasonsObj = raw.get("reasons");
        if (reasonsObj instanceof java.util.List) {
            result.setReasons((java.util.List<Map<String, Object>>) reasonsObj);
        }

        // Dispute draft
        result.setDisputeDraft((String) raw.get("dispute_draft"));

        // Attempt ID
        result.setAttemptId((String) raw.get("attempt_id"));

        // Latency
        Object latencyObj = raw.get("latency_ms");
        result.setLatencyMs(latencyObj != null ? ((Number) latencyObj).doubleValue() : null);

        return result;
    }

    private void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    // ── Custom Exception ──────────────────────────────────────────────

    public static class MlServiceUnavailableException extends RuntimeException {
        public MlServiceUnavailableException(String message) {
            super(message);
        }

        public MlServiceUnavailableException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
