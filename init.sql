SET TIME ZONE 'Asia/Jakarta';

-- Tabel untuk data Traffic
CREATE TABLE IF NOT EXISTS traffic_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    latitude NUMERIC,
    longitude NUMERIC,
    traffic_level INTEGER,
    current_speed NUMERIC,
    free_flow_speed NUMERIC,
    is_peak_hour BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabel untuk data Air Quality (AQI)
CREATE TABLE IF NOT EXISTS aqi_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    latitude NUMERIC,
    longitude NUMERIC,
    aqi_value INTEGER,
    aqi_category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabel untuk Peak Hours Analysis (agregasi per jam)
CREATE TABLE IF NOT EXISTS peak_hours_analysis (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    hour INTEGER NOT NULL,
    location VARCHAR(255),
    avg_traffic_level NUMERIC,
    avg_aqi_value NUMERIC,
    is_peak_hour BOOLEAN DEFAULT FALSE,
    total_records INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, hour, location)
);

-- Tabel untuk daily summary (Serving Layer - data historis)
CREATE TABLE IF NOT EXISTS daily_summary (
    date DATE PRIMARY KEY,
    avg_aqi_jakarta NUMERIC,
    max_traffic_level INTEGER,
    peak_traffic_hour INTEGER,
    peak_aqi_hour INTEGER
);

-- Index untuk performance
CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_traffic_location ON traffic_data(location);
CREATE INDEX IF NOT EXISTS idx_aqi_timestamp ON aqi_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_aqi_location ON aqi_data(location);
CREATE INDEX IF NOT EXISTS idx_peak_hours_date ON peak_hours_analysis(date, hour);

-- View untuk gabungan data real-time (untuk kompatibilitas dengan app lama)
CREATE OR REPLACE VIEW raw_data AS
SELECT 
    t.id,
    t.timestamp,
    t.location,
    t.latitude,
    t.longitude,
    a.aqi_value,
    t.traffic_level
FROM traffic_data t
LEFT JOIN aqi_data a ON 
    t.location = a.location 
    AND DATE_TRUNC('minute', t.timestamp) = DATE_TRUNC('minute', a.timestamp)
WHERE t.timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY t.timestamp DESC
LIMIT 100;