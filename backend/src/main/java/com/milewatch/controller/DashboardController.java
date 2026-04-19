package com.milewatch.controller;

import com.milewatch.dto.DashboardStats;
import com.milewatch.service.AttemptService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * REST Controller for Dashboard endpoints.
 *
 * ENDPOINTS:
 *   GET /api/dashboard/stats    → Aggregate statistics for the dashboard
 *   GET /api/dashboard/health   → Check ML service connectivity
 */
@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    private static final Logger log = LoggerFactory.getLogger(DashboardController.class);

    private final AttemptService attemptService;

    public DashboardController(AttemptService attemptService) {
        this.attemptService = attemptService;
    }

    // ── GET: Dashboard Stats ──────────────────────────────────────────

    @GetMapping("/stats")
    public ResponseEntity<DashboardStats> getStats() {
        log.info("GET /api/dashboard/stats");
        DashboardStats stats = attemptService.getDashboardStats();
        return ResponseEntity.ok(stats);
    }

    // ── GET: ML Service Health ────────────────────────────────────────

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> checkMlHealth() {
        boolean healthy = attemptService.isMlServiceHealthy();
        return ResponseEntity.ok(Map.of(
                "ml_service_healthy", healthy,
                "backend_healthy", true
        ));
    }
}
