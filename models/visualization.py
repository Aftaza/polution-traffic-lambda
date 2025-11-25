import pydeck as pdk
import pandas as pd
import os
from typing import List, Tuple


class VisualizationService:
    """Service class for creating visualizations."""
    
    def __init__(self):
        # Define risk matrix colors (Green to Red)
        self.risk_matrix_colors = [
            [76, 175, 80],    # Green (Safe)
            [139, 195, 74],   # Light Green
            [255, 235, 59],   # Yellow
            [255, 152, 0],    # Orange
            [244, 67, 54]     # Red (Danger)
        ]
    
    def create_heatmap_layer(self, data, get_weight: str, title: str) -> pdk.Layer:
        """Create a heatmap layer for visualization."""
        return pdk.Layer(
            "HeatmapLayer",
            data=data,
            get_position=["longitude", "latitude"],
            get_weight=get_weight,
            radiusPixels=60,
            colorRange=self.risk_matrix_colors,
            opacity=0.8,
            aggregation="SUM"
        )
    
    def create_aqi_heatmap(self, data) -> pdk.Deck:
        """Create AQI heatmap visualization."""
        if data.empty or data['latitude'].empty or data['longitude'].empty:
            # Return a default view if no data
            view_state = pdk.ViewState(
                latitude=-6.200000,
                longitude=106.816666,
                zoom=10,
                pitch=0,
            )
            # Use Carto basemap (no API key required)
            map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

            return pdk.Deck(
                layers=[],
                initial_view_state=view_state,
                map_style=map_style
            )

        # Calculate center coordinates, handling potential NaN values
        lat_mean = data['latitude'].dropna().mean()
        lon_mean = data['longitude'].dropna().mean()

        view_state = pdk.ViewState(
            latitude=lat_mean if pd.notna(lat_mean) else -6.200000,
            longitude=lon_mean if pd.notna(lon_mean) else 106.816666,
            zoom=10,
            pitch=40,
        )

        heatmap_layer_aqi = self.create_heatmap_layer(data, "aqi_clean", "AQI")

        # Use Carto basemap (no API key required)
        map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

        return pdk.Deck(
            layers=[heatmap_layer_aqi],
            initial_view_state=view_state,
            map_style=map_style,
            tooltip={"text": "Lokasi: {location}\nAQI: {aqi_value}"}
        )

    def create_traffic_heatmap(self, data) -> pdk.Deck:
        """Create traffic heatmap visualization."""
        if data.empty or data['latitude'].empty or data['longitude'].empty:
            # Return a default view if no data
            view_state = pdk.ViewState(
                latitude=-6.200000,
                longitude=106.816666,
                zoom=10,
                pitch=0,
            )
            # Use Carto basemap (no API key required)
            map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

            return pdk.Deck(
                layers=[],
                initial_view_state=view_state,
                map_style=map_style
            )

        # Calculate center coordinates, handling potential NaN values
        lat_mean = data['latitude'].dropna().mean()
        lon_mean = data['longitude'].dropna().mean()

        view_state = pdk.ViewState(
            latitude=lat_mean if pd.notna(lat_mean) else -6.200000,
            longitude=lon_mean if pd.notna(lon_mean) else 106.816666,
            zoom=10,
            pitch=40,
        )

        heatmap_layer_traffic = self.create_heatmap_layer(data, "traffic_level", "Traffic")

        # Use Carto basemap (no API key required)
        map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

        return pdk.Deck(
            layers=[heatmap_layer_traffic],
            initial_view_state=view_state,
            map_style=map_style,
            tooltip={"text": "Lokasi: {location}\nTraffic Level: {traffic_level}"}
        )