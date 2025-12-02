-- Tabel untuk menyimpan data mentah dari Ingestion Layer (All Data - untuk Batch Layer)
CREATE TABLE IF NOT EXISTS raw_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    latitude NUMERIC,
    longitude NUMERIC,
    aqi_value INTEGER,
    aqi_category VARCHAR(50),  -- NEW: Good, Moderate, Unhealthy, etc.
    traffic_level INTEGER,
    is_peak_hour BOOLEAN DEFAULT FALSE,  -- NEW: Peak hours detection
    -- Menandakan data ini sudah diproses oleh Speed Layer (opsional)
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index untuk query berdasarkan timestamp
CREATE INDEX IF NOT EXISTS idx_raw_data_timestamp ON raw_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_raw_data_location ON raw_data(location);
CREATE INDEX IF NOT EXISTS idx_raw_data_peak_hour ON raw_data(is_peak_hour);

-- Tabel untuk data real-time dari Speed Layer (Recent Data)
CREATE TABLE IF NOT EXISTS realtime_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    latitude NUMERIC,
    longitude NUMERIC,
    aqi_value INTEGER,
    aqi_category VARCHAR(50),  -- NEW: Good, Moderate, Unhealthy, etc.
    traffic_level INTEGER,
    is_peak_hour BOOLEAN DEFAULT FALSE,  -- NEW: Peak hours detection
    processing_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Data akan expired setelah beberapa jam (cleanup oleh batch job)
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_realtime_timestamp ON realtime_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_realtime_active ON realtime_data(is_active);
CREATE INDEX IF NOT EXISTS idx_realtime_peak_hour ON realtime_data(is_peak_hour);

-- Tabel untuk hasil agregasi dari Batch Layer (Serving Layer - data historis)
CREATE TABLE IF NOT EXISTS batch_aggregations (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    hour INTEGER, -- NULL untuk agregasi harian, 0-23 untuk agregasi per jam
    location VARCHAR(255),
    avg_aqi NUMERIC,
    avg_traffic NUMERIC,
    max_aqi INTEGER,
    max_traffic INTEGER,
    min_aqi INTEGER,
    min_traffic INTEGER,
    data_points_count INTEGER,
    is_peak_hour BOOLEAN DEFAULT FALSE,  -- NEW: Mark if this hour is a peak hour
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date, hour, location)
);

CREATE INDEX IF NOT EXISTS idx_batch_agg_date ON batch_aggregations(date DESC);
CREATE INDEX IF NOT EXISTS idx_batch_agg_hour ON batch_aggregations(hour);

-- Tabel untuk peak hours analysis dari Batch Layer
CREATE TABLE IF NOT EXISTS peak_hours (
    id SERIAL PRIMARY KEY,
    analysis_date DATE NOT NULL,
    peak_aqi_hour INTEGER,
    peak_aqi_value NUMERIC,
    peak_aqi_location VARCHAR(255),
    peak_traffic_hour INTEGER,
    peak_traffic_value NUMERIC,
    peak_traffic_location VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(analysis_date)
);

CREATE INDEX IF NOT EXISTS idx_peak_hours_date ON peak_hours(analysis_date DESC);

-- NEW: Tabel untuk hourly peak hours analysis (per hour per location)
-- This provides detailed hourly aggregation with peak hour indicators
CREATE TABLE IF NOT EXISTS peak_hours_analysis (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    hour INTEGER NOT NULL,  -- 0-23
    location VARCHAR(255),
    avg_traffic_level NUMERIC,
    avg_aqi_value NUMERIC,
    is_peak_hour BOOLEAN DEFAULT FALSE,
    total_records INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date, hour, location)
);

CREATE INDEX IF NOT EXISTS idx_peak_hours_analysis_date ON peak_hours_analysis(date DESC);
CREATE INDEX IF NOT EXISTS idx_peak_hours_analysis_hour ON peak_hours_analysis(hour);
CREATE INDEX IF NOT EXISTS idx_peak_hours_analysis_location ON peak_hours_analysis(location);
CREATE INDEX IF NOT EXISTS idx_peak_hours_analysis_is_peak ON peak_hours_analysis(is_peak_hour);

-- Tabel untuk daily summary (tetap dipertahankan untuk backward compatibility)
CREATE TABLE IF NOT EXISTS daily_summary (
    date DATE PRIMARY KEY,
    avg_aqi_jakarta NUMERIC,
    max_traffic_level INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);