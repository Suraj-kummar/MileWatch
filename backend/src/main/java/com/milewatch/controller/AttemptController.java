package com.milewatch.controller;

import com.milewatch.dto.AttemptRequest;
import com.milewatch.dto.AttemptResponse;
import com.milewatch.service.AttemptService;
import com.milewatch.service.MlServiceClient;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

/**
 * REST Controller for Delivery Attempt operations.
 *
 * ENDPOINTS:
 *   POST /api/attempts           → Submit & score a new delivery attempt
 *   GET  /api/attempts/{id}      → Get a single scored attempt
 *   GET  /api/attempts           → List attempts (paginated, filterable)
 *   GET  /api/attempts/{id}/dispute → Get dispute draft text
 */
@RestController
@RequestMapping("/api/attempts")
public class AttemptController {

    private static final Logger log = LoggerFactory.getLogger(AttemptController.class);

    private final AttemptService attemptService;

    public AttemptController(AttemptService attemptService) {
        this.attemptService = attemptService;
    }

    // ── POST: Submit new attempt ──────────────────────────────────────

    @PostMapping
    public ResponseEntity<?> submitAttempt(@Valid @RequestBody AttemptRequest request) {
        try {
            log.info("POST /api/attempts — scoring new delivery attempt");
            AttemptResponse response = attemptService.submitAttempt(request);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (MlServiceClient.MlServiceUnavailableException e) {
            log.error("ML service unavailable: {}", e.getMessage());
            return ResponseEntity
                    .status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of(
                            "error", "Scoring service is currently unavailable",
                            "detail", e.getMessage()
                    ));
        } catch (Exception e) {
            log.error("Error scoring attempt: {}", e.getMessage(), e);
            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Failed to score attempt: " + e.getMessage()));
        }
    }

    // ── GET: Single attempt ───────────────────────────────────────────

    @GetMapping("/{id}")
    public ResponseEntity<?> getAttempt(@PathVariable String id) {
        try {
            AttemptResponse response = attemptService.getAttempt(id);
            return ResponseEntity.ok(response);
        } catch (NoSuchElementException e) {
            return ResponseEntity
                    .status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", e.getMessage()));
        }
    }

    // ── GET: List attempts (paginated) ────────────────────────────────

    @GetMapping
    public ResponseEntity<Page<AttemptResponse>> listAttempts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "desc") String direction,
            @RequestParam(required = false) String riskLevel) {

        if (riskLevel != null && !riskLevel.isEmpty()) {
            return ResponseEntity.ok(attemptService.listByRiskLevel(riskLevel, page, size));
        }

        return ResponseEntity.ok(attemptService.listAttempts(page, size, sortBy, direction));
    }

    // ── GET: Recent attempts ──────────────────────────────────────────

    @GetMapping("/recent")
    public ResponseEntity<List<AttemptResponse>> getRecentAttempts() {
        return ResponseEntity.ok(attemptService.getRecentAttempts());
    }

    // ── GET: Dispute draft ────────────────────────────────────────────

    @GetMapping("/{id}/dispute")
    public ResponseEntity<?> getDisputeDraft(@PathVariable String id) {
        try {
            String draft = attemptService.getDisputeDraft(id);
            return ResponseEntity.ok(Map.of("dispute_draft", draft != null ? draft : ""));
        } catch (NoSuchElementException e) {
            return ResponseEntity
                    .status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", e.getMessage()));
        }
    }

    // ── Validation Error Handler ──────────────────────────────────────

    @ExceptionHandler(org.springframework.web.bind.MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationErrors(
            org.springframework.web.bind.MethodArgumentNotValidException ex) {

        Map<String, String> fieldErrors = new java.util.LinkedHashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error ->
                fieldErrors.put(error.getField(), error.getDefaultMessage()));

        return ResponseEntity
                .status(HttpStatus.UNPROCESSABLE_ENTITY)
                .body(Map.of(
                        "error", "Validation failed",
                        "fields", fieldErrors
                ));
    }
}
