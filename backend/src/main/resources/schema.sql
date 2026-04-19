-- ═══════════════════════════════════════════════════════════════════════
-- MileWatch — Database Schema
-- ═══════════════════════════════════════════════════════════════════════
-- NOTE: With spring.jpa.hibernate.ddl-auto=update, Hibernate creates
-- tables from entity annotations. This file serves as documentation
-- and can be used for manual setup if needed.
-- ═══════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS delivery_attempts (
    id                          VARCHAR(36) PRIMARY KEY,
    exec_id                     VARCHAR(50),
    customer_address            VARCHAR(255),
    gps_distance_m              DOUBLE NOT NULL,
    time_gap_minutes            DOUBLE NOT NULL,
    call_made                   BOOLEAN NOT NULL,
    is_cod                      BOOLEAN NOT NULL,
    exec_historical_fake_rate   DOUBLE NOT NULL,
    minutes_to_shift_end        DOUBLE NOT NULL,
    pincode_tier                INT NOT NULL,
    credibility_score           DOUBLE,
    risk_level                  VARCHAR(20),
    reasons                     CLOB,
    dispute_draft               CLOB,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on risk_level for dashboard filtering
CREATE INDEX IF NOT EXISTS idx_risk_level ON delivery_attempts(risk_level);

-- Index on created_at for chronological queries
CREATE INDEX IF NOT EXISTS idx_created_at ON delivery_attempts(created_at);

-- Index on credibility_score for range queries
CREATE INDEX IF NOT EXISTS idx_credibility_score ON delivery_attempts(credibility_score);
