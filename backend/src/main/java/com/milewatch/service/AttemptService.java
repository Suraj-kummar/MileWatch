package com.milewatch.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.milewatch.dto.AttemptRequest;
import com.milewatch.dto.AttemptResponse;
import com.milewatch.dto.DashboardStats;
import com.milewatch.model.CredibilityResult;
import com.milewatch.model.DeliveryAttempt;
import com.milewatch.repository.AttemptRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * Core Business Logic Service for Delivery Attempts.
 *
 * Orchestrates the full flow:
 * 1. Receive attempt data from controller
 * 2. Call ML service for credibility scoring
 * 3. Persist attempt + results to database
 * 4. Return formatted response to controller
 *
 * Also handles dashboard statistics computation and attempt retrieval.
 */
@Service
public class AttemptService {

    private static final Logger log = LoggerFactory.getLogger(AttemptService.class);

    private final AttemptRepository repository;
    private final MlServiceClient mlClient;
    private final ObjectMapper objectMapper;

    public AttemptService(AttemptRepository repository, MlServiceClient mlClient) {
        this.repository = repository;
        this.mlClient = mlClient;
        this.objectMapper = new ObjectMapper();
    }

    // ── Submit & Score ─────────────────────────────────────────────────

    /**
     * Submit a new delivery attempt for scoring.
     *
     * Flow: validate → call Flask → persist → return response
     */
    public AttemptResponse submitAttempt(AttemptRequest request) {
        log.info("Submitting attempt for scoring...");

        // Build the feature map for Flask (snake_case keys)
        Map<String, Object> features = buildFeatureMap(request);

        // Call ML service
        CredibilityResult mlResult = mlClient.predict(features);
        log.info("ML result: score={}, risk={}",
                mlResult.getCredibilityScore(), mlResult.getRiskLevel());

        // Create and persist the entity
        DeliveryAttempt entity = new DeliveryAttempt();
        entity.setExecId(request.getExecId());
        entity.setCustomerAddress(request.getCustomerAddress());
        entity.setGpsDistanceM(request.getGpsDistanceM());
        entity.setTimeGapMinutes(request.getTimeGapMinutes());
        entity.setCallMade(request.getCallMade());
        entity.setIsCod(request.getIsCod());
        entity.setExecHistoricalFakeRate(request.getExecHistoricalFakeRate());
        entity.setMinutesToShiftEnd(request.getMinutesToShiftEnd());
        entity.setPincodeTier(request.getPincodeTier());
        entity.setCredibilityScore(mlResult.getCredibilityScore());
        entity.setRiskLevel(mlResult.getRiskLevel());
        entity.setDisputeDraft(mlResult.getDisputeDraft());

        // Serialize reasons list to JSON string for storage
        try {
            entity.setReasons(objectMapper.writeValueAsString(mlResult.getReasons()));
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize reasons", e);
            entity.setReasons("[]");
        }

        DeliveryAttempt saved = repository.save(entity);
        log.info("Attempt saved: id={}", saved.getId());

        return toResponse(saved);
    }

    // ── Retrieval ─────────────────────────────────────────────────────

    /**
     * Get a single attempt by ID.
     */
    public AttemptResponse getAttempt(String id) {
        DeliveryAttempt attempt = repository.findById(id)
                .orElseThrow(() -> new NoSuchElementException("Attempt not found: " + id));
        return toResponse(attempt);
    }

    /**
     * List all attempts with pagination and sorting.
     */
    public Page<AttemptResponse> listAttempts(int page, int size, String sortBy, String direction) {
        Sort sort = direction.equalsIgnoreCase("asc")
                ? Sort.by(sortBy).ascending()
                : Sort.by(sortBy).descending();

        Pageable pageable = PageRequest.of(page, size, sort);
        Page<DeliveryAttempt> attempts = repository.findAll(pageable);

        return attempts.map(this::toResponse);
    }

    /**
     * List attempts filtered by risk level.
     */
    public Page<AttemptResponse> listByRiskLevel(String riskLevel, int page, int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
        Page<DeliveryAttempt> attempts = repository.findByRiskLevel(riskLevel, pageable);
        return attempts.map(this::toResponse);
    }

    /**
     * Get the 20 most recent attempts.
     */
    public List<AttemptResponse> getRecentAttempts() {
        return repository.findTop20ByOrderByCreatedAtDesc()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    // ── Dashboard ─────────────────────────────────────────────────────

    /**
     * Compute aggregate dashboard statistics.
     */
    public DashboardStats getDashboardStats() {
        long total = repository.count();

        if (total == 0) {
            return new DashboardStats(0, 0.0, 0, 0, 0);
        }

        Double avgScore = repository.findAverageScore();
        long highRisk = repository.countByRiskLevel("HIGH_RISK");
        long mediumRisk = repository.countByRiskLevel("MEDIUM_RISK");
        long lowRisk = repository.countByRiskLevel("LOW_RISK");

        return new DashboardStats(
                total,
                avgScore != null ? Math.round(avgScore * 10000.0) / 10000.0 : 0.0,
                highRisk,
                mediumRisk,
                lowRisk
        );
    }

    // ── Dispute Draft ─────────────────────────────────────────────────

    /**
     * Get dispute draft for a specific attempt.
     */
    public String getDisputeDraft(String id) {
        DeliveryAttempt attempt = repository.findById(id)
                .orElseThrow(() -> new NoSuchElementException("Attempt not found: " + id));
        return attempt.getDisputeDraft();
    }

    // ── ML Service Health ─────────────────────────────────────────────

    /**
     * Check if the ML service is reachable.
     */
    public boolean isMlServiceHealthy() {
        return mlClient.isHealthy();
    }

    // ── Private Helpers ───────────────────────────────────────────────

    /**
     * Build the feature map for the Flask ML service (snake_case keys).
     */
    private Map<String, Object> buildFeatureMap(AttemptRequest request) {
        Map<String, Object> features = new HashMap<>();
        features.put("gps_distance_m", request.getGpsDistanceM());
        features.put("time_gap_minutes", request.getTimeGapMinutes());
        features.put("call_made", request.getCallMade() ? 1 : 0);
        features.put("is_cod", request.getIsCod() ? 1 : 0);
        features.put("exec_historical_fake_rate", request.getExecHistoricalFakeRate());
        features.put("minutes_to_shift_end", request.getMinutesToShiftEnd());
        features.put("pincode_tier", request.getPincodeTier());
        return features;
    }

    /**
     * Convert a DeliveryAttempt entity to an AttemptResponse DTO.
     */
    private AttemptResponse toResponse(DeliveryAttempt entity) {
        AttemptResponse response = new AttemptResponse();
        response.setId(entity.getId());
        response.setExecId(entity.getExecId());
        response.setCustomerAddress(entity.getCustomerAddress());
        response.setGpsDistanceM(entity.getGpsDistanceM());
        response.setTimeGapMinutes(entity.getTimeGapMinutes());
        response.setCallMade(entity.getCallMade());
        response.setIsCod(entity.getIsCod());
        response.setExecHistoricalFakeRate(entity.getExecHistoricalFakeRate());
        response.setMinutesToShiftEnd(entity.getMinutesToShiftEnd());
        response.setPincodeTier(entity.getPincodeTier());
        response.setCredibilityScore(entity.getCredibilityScore());
        response.setRiskLevel(entity.getRiskLevel());
        response.setDisputeDraft(entity.getDisputeDraft());
        response.setCreatedAt(entity.getCreatedAt());

        // Deserialize reasons from JSON string
        if (entity.getReasons() != null) {
            try {
                List<Map<String, Object>> reasons = objectMapper.readValue(
                        entity.getReasons(),
                        new TypeReference<List<Map<String, Object>>>() {});
                response.setReasons(reasons);
            } catch (JsonProcessingException e) {
                log.error("Failed to deserialize reasons for attempt {}", entity.getId(), e);
                response.setReasons(List.of());
            }
        }

        return response;
    }
}
