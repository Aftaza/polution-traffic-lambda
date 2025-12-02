---
description: Migrasi fitur-fitur baru dari branch v2 ke master dengan mempertahankan Lambda Architecture
---

# Analisis Fitur Branch v2 vs Master

## Branch v2 (Implementasi Sederhana)
**Struktur:**
- `app.py` - Streamlit dashboard dengan fitur lengkap
- `producer_service.py` - Polling data dari API (TomTom + AQICN)
- `consumer_service.py` - Kafka consumer + logic peak hours
- `db_connector.py` - Simple database connector

**Fitur Baru di v2:**
1. **Peak Hours Detection** - Deteksi jam padat (06:00-10:00, 16:00-20:00)
2. **AQI Categorization** - Klasifikasi AQI (Good, Moderate, Unhealthy, dll)
3. **Tab-based Dashboard** - 4 tabs: Heatmaps, Peak Hours Analysis, Statistics, Raw Data
4. **Plotly Charts** - Visualisasi interaktif untuk analisis peak hours
5. **Real-time Statistics** - Metric cards dan distribution charts
6. **Peak Hours Analysis Table** - `peak_hours_analysis` dengan aggregasi per jam
7. **Combined Traffic vs AQI View** - Chart yang menampilkan korelasi traffic dan AQI

**Database Schema v2:**
- `traffic_data` - Data traffic dengan kolom `is_peak_hour`
- `aqi_data` - Data AQI dengan kolom `aqi_category`
- `peak_hours_analysis` - Agregasi per jam untuk analisis peak hours

## Branch Master (Lambda Architecture)
**Struktur:**
- **Ingestion Layer** - mengumpulkan data dari API
- **Speed Layer** - real-time processing (Kafka Consumer + Stream Processor)
- **Batch Layer** - periodic aggregation & analysis
- **Serving Layer** - unified data access
- Dashboard mengkonsumsi dari Serving Layer

**Database Schema Master:**
- `raw_data` - Data mentah untuk batch processing
- `realtime_data` - Data real-time dari speed layer
- `batch_aggregations` - Hasil agregasi batch processing
- `peak_hours` - Analisis peak hours harian

## Strategi Migrasi

### 1. Update Database Schema
Tambahkan kolom dan tabel baru tanpa menghilangkan yang lama:
- Tambah kolom `is_peak_hour` di `realtime_data` dan `raw_data`
- Tambah kolom `aqi_category` di `realtime_data` dan `raw_data`
- Buat tabel `peak_hours_analysis` untuk agregasi per jam per lokasi

### 2. Update Speed Layer (Real-time Processing)
Di `models/stream_processor.py`:
- Tambahkan fungsi `is_peak_hour()` untuk deteksi jam padat
- Tambahkan fungsi `get_aqi_category()` untuk klasifikasi AQI
- Update `_insert_realtime_data()` untuk menyimpan peak_hour dan aqi_category
- Tambahkan logic untuk update `peak_hours_analysis` table secara incremental

### 3. Update Batch Layer
Di `models/batch_processor.py`:
- Tambahkan fungsi untuk menghitung peak hours analysis berdasarkan historical data
- Update daily/hourly aggregation untuk include peak hours metrics
- Perbaiki peak hour detection untuk menggunakan logic yang sama dengan speed layer

### 4. Update Serving Layer
Di `models/serving_layer.py`:
- Tambahkan method `get_peak_hours_analysis()` untuk mengambil data peak hours
- Update `get_combined_heatmap_data()` untuk include peak hour info dari batch dan speed layer

### 5. Update Dashboard (app.py)
- Tambahkan 4 tabs: Heatmaps, Peak Hours Analysis, Statistics, Raw Data
- Implementasi Plotly charts untuk visualisasi peak hours
- Tambahkan real-time statistics dengan metric cards
- Tambahkan combined view (Traffic vs AQI)
- Update sidebar dengan peak hours info

### 6. Dependencies
Tambahkan di requirements.txt:
- plotly (untuk interactive charts)
- apscheduler (sudah ada untuk batch layer)

## Langkah Implementasi

### Step 1: Update init.sql
Tambahkan kolom dan tabel baru yang dibutuhkan

### Step 2: Update Stream Processor
Implementasi peak hours detection dan AQI categorization di speed layer

### Step 3: Update Batch Processor
Tambahkan hourly aggregation untuk peak hours analysis

### Step 4: Update Serving Layer
Tambahkan method untuk mengambil peak hours analysis

### Step 5: Update Dashboard
Implementasi tab-based interface dengan visualisasi Plotly

### Step 6: Testing
Test semua layer untuk memastikan data flow dengan benar
