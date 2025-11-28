import streamlit as st
import pandas as pd
import pydeck as pdk
from db_connector import get_db_connection
import time
import os
import plotly.express as px
import plotly.graph_objects as go

# Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Heatmap Traffic & Polusi")
st.title("🚦 Heatmap Traffic & Polusi Jakarta (Real-Time)")

# SET MAPBOX TOKEN
MAPBOX_TOKEN = "pk.eyJ1IjoicmFkaWkiLCJhIjoiY21pZHl1OWR4MGJxaTJpcHBjb2c3Mm04NiJ9.7KxKjd4h4JMy79Lo8XOgow"
os.environ["MAPBOX_API_KEY"] = MAPBOX_TOKEN

@st.cache_data(ttl=10)
def get_traffic_data():
    """Get traffic data from database"""
    conn = None
    try:
        conn = get_db_connection()
        query = """
        SELECT timestamp, location, latitude, longitude, traffic_level, is_peak_hour
        FROM traffic_data
        ORDER BY timestamp DESC
        LIMIT 100
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=10)
def get_aqi_data():
    """Get AQI data from database"""
    conn = None
    try:
        conn = get_db_connection()
        query = """
        SELECT timestamp, location, latitude, longitude, aqi_value, aqi_category
        FROM aqi_data
        ORDER BY timestamp DESC
        LIMIT 100
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=60)
def get_peak_hours_analysis():
    """Get peak hours analysis"""
    conn = None
    try:
        conn = get_db_connection()
        query = """
        SELECT hour, 
               AVG(avg_traffic_level) as avg_traffic,
               AVG(avg_aqi_value) as avg_aqi,
               MAX(is_peak_hour::int) as is_peak
        FROM peak_hours_analysis
        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY hour
        ORDER BY hour
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# Load data
df_traffic = get_traffic_data()
df_aqi = get_aqi_data()
df_peak_hours = get_peak_hours_analysis()

# Display last update time
if not df_traffic.empty:
    last_update = df_traffic['timestamp'].max()
    if isinstance(last_update, str):
        display_time = last_update
    else:
        display_time = last_update.strftime('%Y-%m-%d %H:%M:%S')
    st.info(f"Update Terakhir: **{display_time}** | Traffic Records: **{len(df_traffic)}** | AQI Records: **{len(df_aqi)}**")

# Sidebar - Peak Hours Info
with st.sidebar:
    st.header("Peak Hours Info")
    st.markdown("""
    **Morning Peak:** 06:00 - 10:00  
    **Evening Peak:** 16:00 - 20:00
    """)
    
    if not df_traffic.empty:
        current_peak = df_traffic['is_peak_hour'].iloc[0]
        if current_peak:
            st.error("🔴 Currently in PEAK HOURS")
        else:
            st.success("🟢 Currently OFF-PEAK")

# Main content - Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Heatmaps", "Peak Hours Analysis", "Statistics", "Raw Data"])

with tab1:
    # Color definitions
    risk_matrix_colors = [
        [76, 175, 80],    # Hijau (Aman)
        [139, 195, 74],   # Hijau Muda
        [255, 235, 59],   # Kuning
        [255, 152, 0],    # Oranye
        [244, 67, 54]     # Merah (Bahaya)
    ]
    
    # TRAFFIC HEATMAP
    if not df_traffic.empty:
        df_traffic['lat'] = pd.to_numeric(df_traffic['latitude'], errors='coerce')
        df_traffic['lon'] = pd.to_numeric(df_traffic['longitude'], errors='coerce')
        df_traffic = df_traffic.dropna(subset=['lat', 'lon'])
        
        st.subheader("1️Peta Panas Kemacetan Lalu Lintas")
        st.caption("Semakin Merah = Semakin Macet")
        
        view_state = pdk.ViewState(
            latitude=df_traffic['lat'].mean(),
            longitude=df_traffic['lon'].mean(),
            zoom=10.5,
            pitch=45,
        )
        
        heatmap_layer_traffic = pdk.Layer(
            "HeatmapLayer",
            data=df_traffic,
            get_position=["lon", "lat"],
            get_weight="traffic_level",
            radiusPixels=100,
            intensity=2,
            threshold=0.03,
            colorRange=risk_matrix_colors,
            opacity=0.9,
        )
        
        st.pydeck_chart(
            pdk.Deck(
                layers=[heatmap_layer_traffic],
                initial_view_state=view_state,
                map_style='mapbox://styles/mapbox/dark-v10',
                tooltip={"text": "Lokasi: {location}\nTraffic Level: {traffic_level}\nPeak: {is_peak_hour}"}
            ),
            use_container_width=True
        )
        
        st.markdown("---")
    
    # AQI HEATMAP
    if not df_aqi.empty:
        df_aqi['lat'] = pd.to_numeric(df_aqi['latitude'], errors='coerce')
        df_aqi['lon'] = pd.to_numeric(df_aqi['longitude'], errors='coerce')
        df_aqi = df_aqi.dropna(subset=['lat', 'lon'])
        df_aqi['aqi'] = pd.to_numeric(df_aqi['aqi_value'], errors='coerce').fillna(1).astype(int)
        
        st.subheader("2️Peta Panas Kualitas Udara (AQI)")
        st.caption("Semakin Merah = Semakin Berpolusi")
        
        view_state_aqi = pdk.ViewState(
            latitude=df_aqi['lat'].mean(),
            longitude=df_aqi['lon'].mean(),
            zoom=10.5,
            pitch=45,
        )
        
        heatmap_layer_aqi = pdk.Layer(
            "HeatmapLayer",
            data=df_aqi,
            get_position=["lon", "lat"],
            get_weight="aqi",
            radiusPixels=100,
            intensity=2,
            threshold=0.03,
            colorRange=risk_matrix_colors,
            opacity=0.9,
        )
        
        st.pydeck_chart(
            pdk.Deck(
                layers=[heatmap_layer_aqi],
                initial_view_state=view_state_aqi,
                map_style='mapbox://styles/mapbox/dark-v10',
                tooltip={"text": "Lokasi: {location}\nAQI: {aqi_value}\nCategory: {aqi_category}"}
            ),
            use_container_width=True
        )

with tab2:
    st.header("Peak Hours Analysis (Last 7 Days)")
    
    if not df_peak_hours.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Traffic by hour
            fig_traffic = go.Figure()
            fig_traffic.add_trace(go.Bar(
                x=df_peak_hours['hour'],
                y=df_peak_hours['avg_traffic'],
                name='Avg Traffic Level',
                marker_color=['red' if is_peak else 'lightblue' for is_peak in df_peak_hours['is_peak']]
            ))
            fig_traffic.update_layout(
                title="Average Traffic Level by Hour",
                xaxis_title="Hour of Day",
                yaxis_title="Average Traffic Level",
                height=400
            )
            st.plotly_chart(fig_traffic, use_container_width=True)
        
        with col2:
            # AQI by hour
            fig_aqi = go.Figure()
            fig_aqi.add_trace(go.Bar(
                x=df_peak_hours['hour'],
                y=df_peak_hours['avg_aqi'],
                name='Avg AQI',
                marker_color=['orange' if is_peak else 'lightgreen' for is_peak in df_peak_hours['is_peak']]
            ))
            fig_aqi.update_layout(
                title="Average AQI by Hour",
                xaxis_title="Hour of Day",
                yaxis_title="Average AQI",
                height=400
            )
            st.plotly_chart(fig_aqi, use_container_width=True)
        
        # Combined view
        st.subheader("Combined View - Traffic vs AQI")
        fig_combined = go.Figure()
        fig_combined.add_trace(go.Scatter(
            x=df_peak_hours['hour'],
            y=df_peak_hours['avg_traffic'],
            name='Traffic Level',
            line=dict(color='blue', width=3)
        ))
        fig_combined.add_trace(go.Scatter(
            x=df_peak_hours['hour'],
            y=df_peak_hours['avg_aqi']/50,  # Scale AQI to fit
            name='AQI (scaled)',
            line=dict(color='red', width=3),
            yaxis='y2'
        ))
        
        # Add peak hour backgrounds
        morning_peak = [6, 7, 8, 9]
        evening_peak = [16, 17, 18, 19]
        
        for hour in morning_peak:
            fig_combined.add_vrect(x0=hour-0.5, x1=hour+0.5, fillcolor="yellow", opacity=0.2, line_width=0)
        for hour in evening_peak:
            fig_combined.add_vrect(x0=hour-0.5, x1=hour+0.5, fillcolor="orange", opacity=0.2, line_width=0)
        
        fig_combined.update_layout(
            title="Traffic Level and AQI Throughout the Day",
            xaxis_title="Hour of Day",
            yaxis_title="Traffic Level",
            yaxis2=dict(title="AQI", overlaying='y', side='right'),
            height=500
        )
        st.plotly_chart(fig_combined, use_container_width=True)
        
        st.info("Yellow = Morning Peak (6-10 AM) | Orange = Evening Peak (4-8 PM)")
    else:
        st.warning("No peak hours data available yet. Wait for data to accumulate.")

with tab3:
    st.header("Real-Time Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚗 Traffic Statistics")
        if not df_traffic.empty:
            avg_traffic = df_traffic['traffic_level'].mean()
            max_traffic = df_traffic['traffic_level'].max()
            peak_count = df_traffic['is_peak_hour'].sum()
            
            st.metric("Average Traffic Level", f"{avg_traffic:.2f}")
            st.metric("Max Traffic Level", int(max_traffic))
            st.metric("Peak Hour Records", f"{peak_count} / {len(df_traffic)}")
            
            # Traffic level distribution
            traffic_dist = df_traffic['traffic_level'].value_counts().sort_index()
            fig_traffic_dist = px.bar(
                x=traffic_dist.index,
                y=traffic_dist.values,
                labels={'x': 'Traffic Level', 'y': 'Count'},
                title='Traffic Level Distribution'
            )
            st.plotly_chart(fig_traffic_dist, use_container_width=True)
    
    with col2:
        st.subheader("AQI Statistics")
        if not df_aqi.empty:
            avg_aqi = df_aqi['aqi_value'].mean()
            max_aqi = df_aqi['aqi_value'].max()
            
            st.metric("Average AQI", f"{avg_aqi:.1f}")
            st.metric("Max AQI", int(max_aqi))
            
            # AQI category distribution
            category_dist = df_aqi['aqi_category'].value_counts()
            fig_category = px.pie(
                values=category_dist.values,
                names=category_dist.index,
                title='AQI Category Distribution'
            )
            st.plotly_chart(fig_category, use_container_width=True)

with tab4:
    st.header("Raw Data Tables")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Traffic Data")
        if not df_traffic.empty:
            st.dataframe(
                df_traffic[['timestamp', 'location', 'latitude', 'longitude', 'traffic_level', 'is_peak_hour']].head(50),
                use_container_width=True
            )
    
    with col2:
        st.subheader("AQI Data")
        if not df_aqi.empty:
            st.dataframe(
                df_aqi[['timestamp', 'location', 'latitude', 'longitude', 'aqi_value', 'aqi_category']].head(50),
                use_container_width=True
            )