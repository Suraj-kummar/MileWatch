package com.milewatch.dto;

import jakarta.validation.constraints.*;

/**
 * Request DTO for submitting a delivery attempt for scoring.
 *
 * Validation happens here at the Spring Boot layer BEFORE calling Flask.
 * This is defense-in-depth — Flask also validates, but catching bad input
 * early avoids an unnecessary HTTP round-trip.
 */
public class AttemptRequest {

    private String execId;
    private String customerAddress;

    @NotNull(message = "gps_distance_m is required")
    @Min(value = 0, message = "gps_distance_m must be >= 0")
    @Max(value = 50000, message = "gps_distance_m must be <= 50000")
    private Double gpsDistanceM;

    @NotNull(message = "time_gap_minutes is required")
    @Min(value = 0, message = "time_gap_minutes must be >= 0")
    @Max(value = 1440, message = "time_gap_minutes must be <= 1440")
    private Double timeGapMinutes;

    @NotNull(message = "call_made is required")
    private Boolean callMade;

    @NotNull(message = "is_cod is required")
    private Boolean isCod;

    @NotNull(message = "exec_historical_fake_rate is required")
    @DecimalMin(value = "0.0", message = "exec_historical_fake_rate must be >= 0.0")
    @DecimalMax(value = "1.0", message = "exec_historical_fake_rate must be <= 1.0")
    private Double execHistoricalFakeRate;

    @NotNull(message = "minutes_to_shift_end is required")
    @Min(value = 0, message = "minutes_to_shift_end must be >= 0")
    @Max(value = 720, message = "minutes_to_shift_end must be <= 720")
    private Double minutesToShiftEnd;

    @NotNull(message = "pincode_tier is required")
    @Min(value = 1, message = "pincode_tier must be 1, 2, or 3")
    @Max(value = 3, message = "pincode_tier must be 1, 2, or 3")
    private Integer pincodeTier;

    // ── Getters and Setters ───────────────────────────────────────────

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
}
