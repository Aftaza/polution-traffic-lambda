import streamlit as st
import pandas as pd
import pydeck as pdk
from db_connector import get_db_connection
import time

#Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Heatmap Traffic & Polusi")
st.title("🚦 Heatmap Traffic & Polusi Jakarta (Real-Time)")


@st.cache_data(ttl=10)
def get_realtime_heatmap_data():
    conn = None
    try:
        conn = get_db_connection()
        # Ambil 100 data terbaru agar peta terlihat 'ramai'
        query = "SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT 100"
        df_raw = pd.read_sql(query, conn)
        
        if df_raw.empty:
            return pd.DataFrame(), "Data Kosong"
            
        # Normalisasi AQI (Cleaning) agar menjadi angka valid
        def normalize_aqi(aqi):
            try:
                val = int(aqi)
            except:
                return 0 # Default 0 jika error/none
            return val

        df_raw['aqi_clean'] = df_raw['aqi_value'].apply(normalize_aqi)
        
        last_update = df_raw['timestamp'].max()
        
        # Pastikan kolom koordinat bertipe float
        df_raw['latitude'] = df_raw['latitude'].astype(float)
        df_raw['longitude'] = df_raw['longitude'].astype(float)
        
        return df_raw, last_update

    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame(), "Error"
    finally:
        if conn:
            conn.close()


#  2. LOAD DATA
df, last_update = get_realtime_heatmap_data()

# Format Waktu (Fix error strftime)
if isinstance(last_update, str):
    display_time = last_update
else:
    display_time = last_update.strftime('%Y-%m-%d %H:%M:%S')

st.info(f"Update Terakhir: **{display_time}**")


#  3. DEFINISI WARNA (HIJAU -> MERAH)
risk_matrix_colors = [
    [76, 175, 80],    # Hijau (Aman)
    [139, 195, 74],   # Hijau Muda
    [255, 235, 59],   # Kuning
    [255, 152, 0],    # Oranye
    [244, 67, 54]     # Merah (Bahaya)
]

#  4. VISUALISASI MAP (ATAS - BAWAH)
if not df.empty:

    # Hitung View State (Rata-rata koordinat)
    view_state = pdk.ViewState(
        latitude=df['latitude'].mean(),
        longitude=df['longitude'].mean(),
        zoom=10,
        pitch=40,
    )

    # MAP 1: POLUSI UDARA (AQI)
    st.subheader("1. Peta Panas Kualitas Udara (AQI)")
    st.caption("Semakin Merah = Semakin Berpolusi (AQI Tinggi)")
    
    heatmap_layer_aqi = pdk.Layer(
        "HeatmapLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_weight="aqi_clean",         # Bobot berdasarkan AQI
        radiusPixels=60,                # Titik Besar (Visualisasi Jelas)
        colorRange=risk_matrix_colors,
        opacity=0.8,
        aggregation="SUM"
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[heatmap_layer_aqi],
            initial_view_state=view_state,
            map_style='mapbox://styles/mapbox/dark-v10',
            tooltip={"text": "Lokasi: {location}\nAQI: {aqi_value}"}
        )
    )

    st.markdown("---") # Garis Pemisah

    # MAP 2: KEMACETAN (TRAFFIC)
    st.subheader("2. Peta Panas Kemacetan Lalu Lintas")
    st.caption("Semakin Merah = Semakin Macet (Traffic Level 4-5)")

    heatmap_layer_traffic = pdk.Layer(
        "HeatmapLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_weight="traffic_level",     # Bobot berdasarkan Traffic Level
        radiusPixels=60,                # Titik Besar (Visualisasi Jelas)
        colorRange=risk_matrix_colors,
        opacity=0.8,
        aggregation="SUM"
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[heatmap_layer_traffic],
            initial_view_state=view_state,
            map_style='mapbox://styles/mapbox/dark-v10',
            tooltip={"text": "Lokasi: {location}\nTraffic Level: {traffic_level}"}
        )
    )

    #DATA RAW (PALING BAWAH)
    with st.expander("Lihat Data Mentah"):
        st.dataframe(df[['timestamp', 'location', 'latitude', 'longitude', 'aqi_value', 'traffic_level']])

else:
    st.warning("Menunggu data masuk... (Pastikan Ingestion Service berjalan)")