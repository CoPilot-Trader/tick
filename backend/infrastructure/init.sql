-- TICK Database Schema
-- TimescaleDB initialization script

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- OHLCV Tables
-- ============================================================================

-- Live OHLCV data (for inference pipeline)
CREATE TABLE IF NOT EXISTS ohlcv_live (
    ticker VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    bar_ts TIMESTAMPTZ NOT NULL,
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (ticker, timeframe, bar_ts)
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('ohlcv_live', 'bar_ts', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_live_ticker_timeframe 
    ON ohlcv_live (ticker, timeframe, bar_ts DESC);

-- ============================================================================
-- Features Tables
-- ============================================================================

-- Live features (for inference pipeline)
CREATE TABLE IF NOT EXISTS features_live (
    ticker VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    bar_ts TIMESTAMPTZ NOT NULL,
    features JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (ticker, timeframe, bar_ts)
);

-- Convert to hypertable
SELECT create_hypertable('features_live', 'bar_ts', if_not_exists => TRUE);

-- Create index for feature queries
CREATE INDEX IF NOT EXISTS idx_features_live_ticker_timeframe 
    ON features_live (ticker, timeframe, bar_ts DESC);

-- ============================================================================
-- Data Quality / Validation Tables
-- ============================================================================

-- Data quality log
CREATE TABLE IF NOT EXISTS data_quality_log (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    check_ts TIMESTAMPTZ DEFAULT NOW(),
    total_bars INTEGER,
    missing_bars INTEGER,
    duplicate_bars INTEGER,
    quality_score NUMERIC(5, 2),
    issues JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_quality_ticker 
    ON data_quality_log (ticker, timeframe, check_ts DESC);

-- ============================================================================
-- System Tables
-- ============================================================================

-- Backfill tracking
CREATE TABLE IF NOT EXISTS backfill_log (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    rows_inserted INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_backfill_ticker 
    ON backfill_log (ticker, timeframe, start_date DESC);

-- Streaming status
CREATE TABLE IF NOT EXISTS streaming_status (
    ticker VARCHAR(10) PRIMARY KEY,
    timeframe VARCHAR(10) NOT NULL,
    is_streaming BOOLEAN DEFAULT FALSE,
    last_update TIMESTAMPTZ,
    bars_received INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ
);

-- ============================================================================
-- Retention Policies (TimescaleDB)
-- ============================================================================

-- Keep live data for 30 days by default
-- SELECT add_retention_policy('ohlcv_live', INTERVAL '30 days', if_not_exists => TRUE);
-- SELECT add_retention_policy('features_live', INTERVAL '30 days', if_not_exists => TRUE);

-- Note: Retention policies are commented out by default
-- Enable them in production to manage data growth

-- ============================================================================
-- Continuous Aggregates (Optional - for analytics)
-- ============================================================================

-- Example: 1-hour aggregation of 5-minute data
-- CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_1h
-- WITH (timescaledb.continuous) AS
-- SELECT
--     ticker,
--     time_bucket('1 hour', bar_ts) AS bar_ts,
--     first(open, bar_ts) AS open,
--     max(high) AS high,
--     min(low) AS low,
--     last(close, bar_ts) AS close,
--     sum(volume) AS volume
-- FROM ohlcv_live
-- WHERE timeframe = '5m'
-- GROUP BY ticker, time_bucket('1 hour', bar_ts);

-- ============================================================================
-- Grant permissions
-- ============================================================================

-- Grant all privileges to tick_user (already owner, but explicit)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tick_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tick_user;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'TICK database schema initialized successfully';
END $$;




