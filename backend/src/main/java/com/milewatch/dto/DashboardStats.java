package com.milewatch.dto;

/**
 * Dashboard statistics DTO.
 *
 * Aggregated metrics computed from all stored delivery attempts,
 * displayed on the React dashboard landing page.
 */
public class DashboardStats {

    private long totalAttempts;
    private double averageScore;
    private long highRiskCount;
    private long mediumRiskCount;
    private long lowRiskCount;
    private double flaggedRate;  // % of attempts that are HIGH or MEDIUM risk

    public DashboardStats() {}

    public DashboardStats(long totalAttempts, double averageScore,
                          long highRiskCount, long mediumRiskCount, long lowRiskCount) {
        this.totalAttempts = totalAttempts;
        this.averageScore = averageScore;
        this.highRiskCount = highRiskCount;
        this.mediumRiskCount = mediumRiskCount;
        this.lowRiskCount = lowRiskCount;
        this.flaggedRate = totalAttempts > 0
                ? ((double) (highRiskCount + mediumRiskCount) / totalAttempts) * 100
                : 0.0;
    }

    // ── Getters and Setters ───────────────────────────────────────────

    public long getTotalAttempts() { return totalAttempts; }
    public void setTotalAttempts(long totalAttempts) { this.totalAttempts = totalAttempts; }

    public double getAverageScore() { return averageScore; }
    public void setAverageScore(double averageScore) { this.averageScore = averageScore; }

    public long getHighRiskCount() { return highRiskCount; }
    public void setHighRiskCount(long highRiskCount) { this.highRiskCount = highRiskCount; }

    public long getMediumRiskCount() { return mediumRiskCount; }
    public void setMediumRiskCount(long mediumRiskCount) { this.mediumRiskCount = mediumRiskCount; }

    public long getLowRiskCount() { return lowRiskCount; }
    public void setLowRiskCount(long lowRiskCount) { this.lowRiskCount = lowRiskCount; }

    public double getFlaggedRate() { return flaggedRate; }
    public void setFlaggedRate(double flaggedRate) { this.flaggedRate = flaggedRate; }
}
