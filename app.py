import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from models.database import DatabaseConnection
from models.serving_layer import ServingLayer
from models.visualization import VisualizationService

# Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Heatmap Traffic & Polusi")
st.title("🚦 Heatmap Traffic & Polusi Jakarta (Real-Time)")

@st.cache_data(ttl=10)
def get_heatmap_data():
    """Get heatmap data from Serving Layer (Lambda Architecture)."""
    db_connection = DatabaseConnection()
    serving_layer = ServingLayer(db_connection)
    
    # Get combined data from Speed + Batch layers
    df, last_update = serving_layer.get_combined_heatmap_data()
    
    if not df.empty:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df['aqi_clean'] = pd.to_numeric(df.get('aqi_value', df.get('aqi_clean', 0)), errors='coerce')
        df['aqi_value'] = df['aqi_clean']  # Ensure both columns exist
        df['traffic_level'] = pd.to_numeric(df['traffic_level'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])
    
    return df, last_update

@st.cache_data(ttl=60)
def get_peak_hours_data():
    """Get peak hours analysis from Serving Layer."""
    db_connection = DatabaseConnection()
    serving_layer = ServingLayer(db_connection)
    
    # Get peak hours analysis (last 7 days)
    df = serving_layer.get_peak_hours_analysis(days=7)
    
    return df

# Load data
df_main, last_update = get_heatmap_data()
df_peak_hours = get_peak_hours_data()

# Initialize visualization service
visualization = VisualizationService()

# Display last update time and data source
if not df_main.empty:
    # Determine data source
    now = pd.Timestamp.now(tz='UTC')
    max_timestamp = df_main['timestamp'].max()
    
    if max_timestamp.tz is None:
        max_timestamp = pd.Timestamp(max_timestamp, tz='UTC')
    
    time_diff = (now - max_timestamp).total_seconds() / 60
    
    if time_diff < 60:
        data_source = "📡 Speed Layer (Real-time)"
        badge_color = "green"
    else:
        data_source = "📊 Batch Layer (Historical)"
        badge_color = "orange"
    
    # Format timestamp
    if isinstance(last_update, str):
        display_time = last_update
    else:
        display_time = last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else "N/A"
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"**Update Terakhir:** {display_time} | **Total Records:** {len(df_main)}")
    with col2:
        st.markdown(f":{badge_color}[{data_source}]")

# Sidebar - Peak Hours Info
with st.sidebar:
    st.header("⏰ Peak Hours Info")
    st.markdown("""
    **Morning Peak:** 06:00 - 10:00  
    **Evening Peak:** 16:00 - 20:00
    """)
    
    if not df_main.empty and 'is_peak_hour' in df_main.columns:
        try:
            current_peak = df_main.sort_values('timestamp', ascending=False)['is_peak_hour'].iloc[0]
            if current_peak:
                st.error("🔴 Currently in PEAK HOURS")
            else:
                st.success("🟢 Currently OFF-PEAK")
        except:
            st.info("Peak hour status unavailable")
    
    st.markdown("---")
    st.markdown("### 🏗️ Architecture")
    st.markdown("""
    **Lambda Architecture:**
    - **Speed Layer:** Real-time data
    - **Batch Layer:** Historical aggregations
    - **Serving Layer:** Unified access
    """)

# Main content - Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Heatmaps", "📊 Peak Hours Analysis", "📈 Statistics", "📋 Raw Data"])

with tab1:
    st.markdown("## Traffic & Pollution Heatmaps")
    
    if not df_main.empty:
        # TRAFFIC HEATMAP (using VisualizationService with Carto Dark)
        st.subheader("1️⃣ Peta Panas Kemacetan Lalu Lintas")
        st.caption("Semakin Merah = Semakin Macet")
        
        traffic_deck = visualization.create_traffic_heatmap(df_main)
        st.pydeck_chart(traffic_deck, use_container_width=True)
        
        st.markdown("---")
        
        # AQI HEATMAP (using VisualizationService with Carto Dark)
        st.subheader("2️⃣ Peta Panas Kualitas Udara (AQI)")
        st.caption("Semakin Merah = Semakin Berpolusi")
        
        aqi_deck = visualization.create_aqi_heatmap(df_main)
        st.pydeck_chart(aqi_deck, use_container_width=True)
    else:
        st.warning("⏳ Menunggu data... Pastikan semua services berjalan.")

with tab2:
    st.header("📊 Peak Hours Analysis (Last 7 Days)")
    
    if not df_peak_hours.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Traffic by hour
            fig_traffic = go.Figure()
            fig_traffic.add_trace(go.Bar(
                x=df_peak_hours['hour'],
                y=df_peak_hours['avg_traffic'],
                name='Avg Traffic Level',
                marker_color=['#F44336' if is_peak else '#42A5F5' for is_peak in df_peak_hours['is_peak']]
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
                marker_color=['#FF9800' if is_peak else '#66BB6A' for is_peak in df_peak_hours['is_peak']]
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
            line=dict(color='#2196F3', width=3),
            mode='lines+markers'
        ))
        fig_combined.add_trace(go.Scatter(
            x=df_peak_hours['hour'],
            y=df_peak_hours['avg_aqi']/50,  # Scale AQI to fit
            name='AQI (scaled /50)',
            line=dict(color='#FF5722', width=3),
            mode='lines+markers',
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
            yaxis2=dict(title="AQI (scaled)", overlaying='y', side='right'),
            height=500
        )
        st.plotly_chart(fig_combined, use_container_width=True)
        
        st.info("💡 Yellow = Morning Peak (6-10 AM) | Orange = Evening Peak (4-8 PM)")
    else:
        st.warning("⏳ No peak hours data available yet. Wait for data to accumulate.")

with tab3:
    st.header("📈 Real-Time Statistics")
    
    if not df_main.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚗 Traffic Statistics")
            avg_traffic = df_main['traffic_level'].mean()
            max_traffic = df_main['traffic_level'].max()
            
            st.metric("Average Traffic Level", f"{avg_traffic:.2f}")
            st.metric("Max Traffic Level", int(max_traffic))
            
            if 'is_peak_hour' in df_main.columns:
                peak_count = df_main['is_peak_hour'].sum()
                st.metric("Peak Hour Records", f"{peak_count} / {len(df_main)}")
            
            # Traffic level distribution
            traffic_dist = df_main['traffic_level'].value_counts().sort_index()
            fig_traffic_dist = px.bar(
                x=traffic_dist.index,
                y=traffic_dist.values,
                labels={'x': 'Traffic Level', 'y': 'Count'},
                title='Traffic Level Distribution',
                color=traffic_dist.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_traffic_dist, use_container_width=True)
        
        with col2:
            st.subheader("🌫️ AQI Statistics")
            avg_aqi = df_main['aqi_value'].mean()
            max_aqi = df_main['aqi_value'].max()
            
            st.metric("Average AQI", f"{avg_aqi:.1f}")
            st.metric("Max AQI", int(max_aqi))
            
            # AQI category distribution
            if 'aqi_category' in df_main.columns:
                category_dist = df_main['aqi_category'].value_counts()
                fig_category = px.pie(
                    values=category_dist.values,
                    names=category_dist.index,
                    title='AQI Category Distribution',
                    color_discrete_sequence=px.colors.sequential.RdYlGn_r
                )
                st.plotly_chart(fig_category, use_container_width=True)
            else:
                # If no category, show AQI distribution
                st.info("AQI categories will be available once data is processed through Speed Layer")
    else:
        st.warning("⏳ No data available for statistics")

with tab4:
    st.header("📋 Raw Data Tables")
    
    if not df_main.empty:
        # Show available columns
        display_columns = ['timestamp', 'location', 'latitude', 'longitude', 'aqi_value', 'traffic_level']
        
        # Add optional columns if they exist
        if 'is_peak_hour' in df_main.columns:
            display_columns.append('is_peak_hour')
        if 'aqi_category' in df_main.columns:
            display_columns.append('aqi_category')
        
        # Filter to only existing columns
        display_columns = [col for col in display_columns if col in df_main.columns]
        
        st.dataframe(
            df_main[display_columns].head(100),
            use_container_width=True
        )
        
        # Download button
        csv = df_main[display_columns].to_csv(index=False)
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name="traffic_pollution_data.csv",
            mime="text/csv"
        )
    else:
        st.warning("⏳ No data available")

# Auto-refresh info
st.sidebar.markdown("---")
st.sidebar.info("🔄 Dashboard auto-refreshes every 10 seconds (cached)")
