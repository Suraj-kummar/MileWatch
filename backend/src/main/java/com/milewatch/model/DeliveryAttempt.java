package com.milewatch.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * JPA Entity: Delivery Attempt
 *
 * Represents a single delivery attempt that has been scored by the ML model.
 * This is the core persistence entity — every scored attempt is saved here
 * so the dashboard can display historical data.
 *
 * DESIGN DECISION: reasons stored as JSON string (CLOB) rather than a
 * separate table because:
 * - Reasons are always read/written as a unit (never queried individually)
 * - Avoids N+1 query problems
 * - Simpler schema, easier migration to PostgreSQL JSONB later
 */
@Entity
@Table(name = "delivery_attempts")
public class DeliveryAttempt {

    @Id
    @Column(length = 36)
    private String id;

    @Column(name = "exec_id", length = 50)
    private String execId;

    @Column(name = "customer_address")
    private String customerAddress;

    // ── Model Features ────────────────────────────────────────────────

    @Column(name = "gps_distance_m", nullable = false)
    private Double gpsDistanceM;

    @Column(name = "time_gap_minutes", nullable = false)
    private Double timeGapMinutes;

    @Column(name = "call_made", nullable = false)
    private Boolean callMade;

    @Column(name = "is_cod", nullable = false)
    private Boolean isCod;

    @Column(name = "exec_historical_fake_rate", nullable = false)
    private Double execHistoricalFakeRate;

    @Column(name = "minutes_to_shift_end", nullable = false)
    private Double minutesToShiftEnd;

    @Column(name = "pincode_tier", nullable = false)
    private Integer pincodeTier;

    // ── ML Scoring Results ────────────────────────────────────────────

    @Column(name = "credibility_score")
    private Double credibilityScore;

    @Column(name = "risk_level", length = 20)
    private String riskLevel;

    @Lob
    @Column(name = "reasons", columnDefinition = "CLOB")
    private String reasons;  // JSON array of reason objects

    @Lob
    @Column(name = "dispute_draft", columnDefinition = "CLOB")
    private String disputeDraft;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    // ── Lifecycle ─────────────────────────────────────────────────────

    @PrePersist
    protected void onCreate() {
        if (this.id == null) {
            this.id = UUID.randomUUID().toString();
        }
        if (this.createdAt == null) {
            this.createdAt = LocalDateTime.now();
        }
    }

    // ── Constructors ──────────────────────────────────────────────────

    public DeliveryAttempt() {}

    // ── Getters and Setters ───────────────────────────────────────────

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getExecId() { return execId; }
    public void setExecId(String execId) { this.execId = execId; }

    public String getCustomerAddress() { return customerAddress; }
    public void setCustomerAddress(String customerAddress) { this.customerAddress = customerAddress; }

    public Double getGpsDistanceM() { return gpsDistanceM; }
    public void setGpsDistanceM(Double gpsDistanceM) { this.gpsDistanceM = gpsDistanceM; }

    public Double getTimeGapMinutes() { return timeGapMinutes; }
    public void setTimeGapMinutes(Double timeGapMinutes) { this.timeGapMinutes = timeGapMinutes; }

    public Boolean getCallMade() { return callMade; }
    public void setCallMade(Boolean callMade) { this.callMade = callMade; }

    public Boolean getIsCod() { return isCod; }
    public void setIsCod(Boolean isCod) { this.isCod = isCod; }

    public Double getExecHistoricalFakeRate() { return execHistoricalFakeRate; }
    public void setExecHistoricalFakeRate(Double execHistoricalFakeRate) { this.execHistoricalFakeRate = execHistoricalFakeRate; }

    public Double getMinutesToShiftEnd() { return minutesToShiftEnd; }
    public void setMinutesToShiftEnd(Double minutesToShiftEnd) { this.minutesToShiftEnd = minutesToShiftEnd; }

    public Integer getPincodeTier() { return pincodeTier; }
    public void setPincodeTier(Integer pincodeTier) { this.pincodeTier = pincodeTier; }

    public Double getCredibilityScore() { return credibilityScore; }
    public void setCredibilityScore(Double credibilityScore) { this.credibilityScore = credibilityScore; }

    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }

    public String getReasons() { return reasons; }
    public void setReasons(String reasons) { this.reasons = reasons; }

    public String getDisputeDraft() { return disputeDraft; }
    public void setDisputeDraft(String disputeDraft) { this.disputeDraft = disputeDraft; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
