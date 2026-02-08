-- TICK Database Schema
-- TimescaleDB initialization script for OHLCV and features storage

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- =============================================================================
-- OHLCV Tables
-- =============================================================================

-- Live OHLCV data (for inference pipeline)
CREATE TABLE IF NOT EXISTS ohlcv_live (
    ticker VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    bar_ts TIMESTAMPTZ NOT NULL,
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (ticker, timeframe, bar_ts)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('ohlcv_live', 'bar_ts', if_not_exists => TRUE);

-- Create index for faster ticker+timeframe queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_live_ticker_tf 
ON ohlcv_live (ticker, timeframe, bar_ts DESC);

-- =============================================================================
-- Features Table
-- =============================================================================

-- Computed features for inference
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

-- Index for ticker queries
CREATE INDEX IF NOT EXISTS idx_features_live_ticker_tf 
ON features_live (ticker, timeframe, bar_ts DESC);

-- =============================================================================
-- Data Quality Table (for validation tracking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS data_quality_log (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    check_date DATE NOT NULL,
    total_bars INTEGER,
    missing_bars INTEGER,
    duplicate_bars INTEGER,
    null_values INTEGER,
    quality_score NUMERIC(5, 2),
    issues JSONB,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_log_ticker 
ON data_quality_log (ticker, timeframe, check_date DESC);

-- =============================================================================
-- Backfill Status Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS backfill_status (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    rows_inserted INTEGER,
    status VARCHAR(20) NOT NULL, -- pending, running, completed, failed
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backfill_status_ticker 
ON backfill_status (ticker, timeframe, status);

-- =============================================================================
-- Useful Views
-- =============================================================================

-- Latest bar for each ticker/timeframe
CREATE OR REPLACE VIEW v_latest_bars AS
SELECT DISTINCT ON (ticker, timeframe)
    ticker,
    timeframe,
    bar_ts,
    open,
    high,
    low,
    close,
    volume
FROM ohlcv_live
ORDER BY ticker, timeframe, bar_ts DESC;

-- Data coverage summary
CREATE OR REPLACE VIEW v_data_coverage AS
SELECT 
    ticker,
    timeframe,
    MIN(bar_ts) as earliest_bar,
    MAX(bar_ts) as latest_bar,
    COUNT(*) as total_bars,
    EXTRACT(DAY FROM (MAX(bar_ts) - MIN(bar_ts))) as days_coverage
FROM ohlcv_live
GROUP BY ticker, timeframe
ORDER BY ticker, timeframe;

-- =============================================================================
-- Functions
-- =============================================================================

-- Function to get recent bars for a ticker
CREATE OR REPLACE FUNCTION get_recent_bars(
    p_ticker VARCHAR(10),
    p_timeframe VARCHAR(10),
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    bar_ts TIMESTAMPTZ,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT o.bar_ts, o.open, o.high, o.low, o.close, o.volume
    FROM ohlcv_live o
    WHERE o.ticker = p_ticker AND o.timeframe = p_timeframe
    ORDER BY o.bar_ts DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate returns
CREATE OR REPLACE FUNCTION calc_returns(
    p_ticker VARCHAR(10),
    p_timeframe VARCHAR(10),
    p_periods INTEGER DEFAULT 1
)
RETURNS TABLE (
    bar_ts TIMESTAMPTZ,
    close NUMERIC,
    return_pct NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.bar_ts,
        o.close,
        (o.close - LAG(o.close, p_periods) OVER (ORDER BY o.bar_ts)) / 
            NULLIF(LAG(o.close, p_periods) OVER (ORDER BY o.bar_ts), 0) * 100 as return_pct
    FROM ohlcv_live o
    WHERE o.ticker = p_ticker AND o.timeframe = p_timeframe
    ORDER BY o.bar_ts;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Retention Policy (optional - uncomment if needed)
-- =============================================================================

-- Keep only last 2 years of 5-minute data
-- SELECT add_retention_policy('ohlcv_live', INTERVAL '2 years');

-- Compress old data (optional)
-- ALTER TABLE ohlcv_live SET (timescaledb.compress, timescaledb.compress_segmentby = 'ticker,timeframe');
-- SELECT add_compression_policy('ohlcv_live', INTERVAL '7 days');

-- =============================================================================
-- Grant Permissions (adjust as needed)
-- =============================================================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO tick;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tick;

