package com.milewatch.model;

import java.util.List;
import java.util.Map;

/**
 * Represents the ML service prediction response.
 *
 * This is not a JPA entity — it's a plain POJO used to deserialize
 * the JSON response from the Flask /predict endpoint.
 */
public class CredibilityResult {

    private Double credibilityScore;
    private String riskLevel;
    private List<Map<String, Object>> reasons;
    private String disputeDraft;
    private String attemptId;
    private Double latencyMs;

    public CredibilityResult() {}

    // ── Getters and Setters ───────────────────────────────────────────

    public Double getCredibilityScore() { return credibilityScore; }
    public void setCredibilityScore(Double credibilityScore) { this.credibilityScore = credibilityScore; }

    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }

    public List<Map<String, Object>> getReasons() { return reasons; }
    public void setReasons(List<Map<String, Object>> reasons) { this.reasons = reasons; }

    public String getDisputeDraft() { return disputeDraft; }
    public void setDisputeDraft(String disputeDraft) { this.disputeDraft = disputeDraft; }

    public String getAttemptId() { return attemptId; }
    public void setAttemptId(String attemptId) { this.attemptId = attemptId; }

    public Double getLatencyMs() { return latencyMs; }
    public void setLatencyMs(Double latencyMs) { this.latencyMs = latencyMs; }
}
