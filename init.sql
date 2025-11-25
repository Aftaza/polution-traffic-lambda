-- Tabel untuk menyimpan data mentah dari Ingestion Layer (Batch Layer data)
CREATE TABLE IF NOT EXISTS raw_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    latitude NUMERIC,
    longitude NUMERIC,
    aqi_value INTEGER,
    traffic_level INTEGER,
    -- Menandakan data ini sudah diproses oleh Speed Layer (opsional)
    is_processed BOOLEAN DEFAULT FALSE
);

-- Tabel untuk menyimpan hasil agregasi dari Batch Layer (Serving Layer - data historis)
CREATE TABLE IF NOT EXISTS daily_summary (
    date DATE PRIMARY KEY,
    avg_aqi_jakarta NUMERIC,
    max_traffic_level INTEGER
);