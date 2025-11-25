import streamlit as st
import pandas as pd
from models.database import DatabaseConnection
from models.data_repository import DataRepository
from models.visualization import VisualizationService
from utils import format_datetime_for_display


@st.cache_data(ttl=10)
def get_realtime_heatmap_data():
    """Get the latest data for heatmap visualization."""
    # Create a new database connection and repository to avoid caching issues
    db_connection = DatabaseConnection()
    repository = DataRepository(db_connection)
    df, last_update = repository.get_realtime_heatmap_data()

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

    def display_data(self):
        """Display the heatmap data."""
        # Load data using the cached function
        df, last_update = get_realtime_heatmap_data()

        # Format time for display
        display_time = format_datetime_for_display(last_update)
        st.info(f"Update Terakhir: **{display_time}**")

        if not df.empty:
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