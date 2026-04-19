package com.milewatch.repository;

import com.milewatch.model.DeliveryAttempt;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * JPA Repository for DeliveryAttempt entities.
 *
 * Spring Data JPA auto-implements these methods. Custom queries use JPQL
 * for aggregation (dashboard stats).
 */
@Repository
public interface AttemptRepository extends JpaRepository<DeliveryAttempt, String> {

    // ── Dashboard Stats Queries ───────────────────────────────────────

    @Query("SELECT AVG(d.credibilityScore) FROM DeliveryAttempt d WHERE d.credibilityScore IS NOT NULL")
    Double findAverageScore();

    @Query("SELECT COUNT(d) FROM DeliveryAttempt d WHERE d.riskLevel = :riskLevel")
    long countByRiskLevel(String riskLevel);

    // ── Filtering ─────────────────────────────────────────────────────

    Page<DeliveryAttempt> findByRiskLevel(String riskLevel, Pageable pageable);

    Page<DeliveryAttempt> findByCredibilityScoreBetween(
            Double minScore, Double maxScore, Pageable pageable);

    // ── Recent attempts (ordered by creation time) ────────────────────

    List<DeliveryAttempt> findTop20ByOrderByCreatedAtDesc();
}
