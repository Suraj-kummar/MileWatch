package com.milewatch.dto;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * Response DTO for a scored delivery attempt.
 *
 * Combines the original attempt data with the ML scoring results.
 * This is what the React frontend receives and displays.
 */
public class AttemptResponse {

    private String id;
    private String execId;
    private String customerAddress;

    // Features
    private Double gpsDistanceM;
    private Double timeGapMinutes;
    private Boolean callMade;
    private Boolean isCod;
    private Double execHistoricalFakeRate;
    private Double minutesToShiftEnd;
    private Integer pincodeTier;

    // ML Results
    private Double credibilityScore;
    private String riskLevel;
    private List<Map<String, Object>> reasons;
    private String disputeDraft;

    // Metadata
    private LocalDateTime createdAt;

    public AttemptResponse() {}

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

    public List<Map<String, Object>> getReasons() { return reasons; }
    public void setReasons(List<Map<String, Object>> reasons) { this.reasons = reasons; }

    public String getDisputeDraft() { return disputeDraft; }
    public void setDisputeDraft(String disputeDraft) { this.disputeDraft = disputeDraft; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
