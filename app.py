import streamlit as st
import pandas as pd
from models.database import DatabaseConnection
from models.data_repository import DataRepository
from models.serving_layer import ServingLayer
from models.visualization import VisualizationService
from utils import format_datetime_for_display, get_aqi_category, analyze_peak_hours


@st.cache_data(ttl=10)
def get_realtime_heatmap_data():
    """Get the latest data for heatmap visualization from Serving Layer."""
    # Create a new database connection and serving layer to avoid caching issues
    db_connection = DatabaseConnection()
    serving_layer = ServingLayer(db_connection)
    
    # Get combined data from Serving Layer (Speed + Batch)
    df, last_update = serving_layer.get_combined_heatmap_data()

    # Ensure the data types are correct for pydeck
    if not df.empty:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df['aqi_clean'] = pd.to_numeric(df['aqi_clean'], errors='coerce')
        df['traffic_level'] = pd.to_numeric(df['traffic_level'], errors='coerce')

        # Drop rows with invalid coordinates
        df = df.dropna(subset=['latitude', 'longitude'])

    return df, last_update


class StreamlitApp:
    """Main Streamlit application class."""

    def __init__(self):
        self.db_connection = DatabaseConnection()
        self.visualization = VisualizationService()
        self.setup_page()

    def setup_page(self):
        """Configure the Streamlit page."""
        st.set_page_config(layout="wide", page_title="Heatmap Traffic & Polusi")
        st.title("🚦 Heatmap Traffic & Polusi Jakarta (Real-Time)")

    def display_aqi_legend(self):
        """Display AQI legend with color categories."""
        st.markdown("### 📊 Legenda Kualitas Udara (AQI)")
        
        # Create legend items
        legend_data = [
            (0, 50, "Good", "#4CAF50"),
            (50, 100, "Moderate", "#FFEB3B"),
            (100, 150, "Unhealthy for Sensitive Groups", "#FF9800"),
            (150, 200, "Unhealthy", "#F44336"),
            (200, 300, "Very Unhealthy", "#9C27B0"),
            (300, 500, "Hazardous", "#7B1FA2")
        ]
        
        # Display legend as a styled table
        for min_val, max_val, category, color in legend_data:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 60px; height: 25px; background-color: {color}; 
                                border-radius: 4px; margin-right: 12px; border: 1px solid #ddd;
                                display: flex; align-items: center; justify-content: center;
                                color: white; font-weight: bold; font-size: 11px;">
                        {min_val}-{max_val}
                    </div>
                    <div style="font-size: 14px; color: white;">
                        {category}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    def display_peak_hours(self, df):
        """Display peak hours analysis."""
        st.markdown("### ⏰ Analisis Jam Puncak (UTC+7)")
        
        peak_data = analyze_peak_hours(df)
        
        if peak_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🌫️ Polusi Udara (AQI)")
                st.metric(
                    label="Jam Puncak Polusi",
                    value=f"{peak_data['peak_aqi_hour']:02d}:00 WIB",
                    delta=f"AQI Rata-rata: {peak_data['peak_aqi_value']:.1f}"
                )
                
            with col2:
                st.markdown("#### 🚗 Kemacetan Lalu Lintas")
                st.metric(
                    label="Jam Puncak Kemacetan",
                    value=f"{peak_data['peak_traffic_hour']:02d}:00 WIB",
                    delta=f"Level Rata-rata: {peak_data['peak_traffic_value']:.1f}"
                )
            
            # Show hourly breakdown in expander
            with st.expander("📈 Lihat Data Per Jam"):
                st.dataframe(
                    peak_data['hourly_stats'].reset_index().rename(columns={
                        'hour': 'Jam (WIB)',
                        'aqi_value': 'AQI Rata-rata',
                        'traffic_level': 'Traffic Level Rata-rata'
                    }),
                    use_container_width=True
                )
        else:
            st.info("Data tidak cukup untuk analisis jam puncak")

    def display_data(self):
        """Display the heatmap data."""
        # Load data using the cached function
        df, last_update = get_realtime_heatmap_data()

        # Format time for display
        display_time = format_datetime_for_display(last_update)
        
        # Determine data source (Speed Layer vs Batch Layer)
        if not df.empty:
            # Get current time as timezone-aware (UTC)
            now = pd.Timestamp.now(tz='UTC')
            max_timestamp = df['timestamp'].max()
            
            # Convert max_timestamp to timezone-aware if it's naive
            if max_timestamp.tz is None:
                max_timestamp = pd.Timestamp(max_timestamp, tz='UTC')
            
            time_diff = (now - max_timestamp).total_seconds() / 60
            if time_diff < 60:  # Less than 1 hour old
                data_source = "Speed Layer (Real-time)"
                badge_color = "#00C851"  # Green
            else:
                data_source = "Batch Layer (Historical)"
                badge_color = "#FF8800"  # Orange
        else:
            data_source = "No Data"
            badge_color = "#999999"
        
        # Display update time with data source badge
        col_time, col_badge = st.columns([3, 1])
        with col_time:
            st.info(f"Update Terakhir: **{display_time}**")
        with col_badge:
            st.markdown(
                f'<div style="background-color: {badge_color}; color: white; padding: 8px 12px; '
                f'border-radius: 4px; text-align: center; font-size: 12px; font-weight: bold;">'
                f'📡 {data_source}</div>',
                unsafe_allow_html=True
            )

        if not df.empty:
            # Create two columns for legend and peak hours
            col1, col2 = st.columns([1, 2])
            
            with col1:
                self.display_aqi_legend()
            
            with col2:
                self.display_peak_hours(df)
            
            st.markdown("---")  # Separator
            
            # Visualization for AQI
            st.subheader("1. Peta Panas Kualitas Udara (AQI)")
            st.caption("Semakin Merah = Semakin Berpolusi (AQI Tinggi)")

            aqi_deck = self.visualization.create_aqi_heatmap(df)
            st.pydeck_chart(aqi_deck)

            st.markdown("---")  # Separator

            # Visualization for Traffic
            st.subheader("2. Peta Panas Kemacetan Lalu Lintas")
            st.caption("Semakin Merah = Semakin Macet (Traffic Level 4-5)")

            traffic_deck = self.visualization.create_traffic_heatmap(df)
            st.pydeck_chart(traffic_deck)

            # Raw data expander
            with st.expander("Lihat Data Mentah"):
                st.dataframe(df[['timestamp', 'location', 'latitude', 'longitude', 'aqi_value', 'traffic_level']])

        else:
            st.warning("Menunggu data masuk... (Pastikan Ingestion Service berjalan)")


if __name__ == "__main__":
    app = StreamlitApp()
    app.display_data()