import pydeck as pdk
import pandas as pd
from datetime import datetime


class VisualizationService:
    """Service class for creating visualizations."""
    
    def __init__(self):
        # Define AQI color scale (based on standard AQI categories)
        self.aqi_colors = {
            'Good': [76, 175, 80, 255],              # Green
            'Moderate': [255, 235, 59, 255],         # Yellow
            'Unhealthy for Sensitive Groups': [255, 152, 0, 255],  # Orange
            'Unhealthy': [244, 67, 54, 255],         # Red
            'Very Unhealthy': [156, 39, 176, 255],   # Purple
            'Hazardous': [126, 87, 194, 255]         # Dark Purple
        }
        
        # Define traffic color scale (1-5 levels)
        self.traffic_colors = {
            1: [76, 175, 80, 255],    # Green (Lancar)
            2: [139, 195, 74, 255],   # Light Green
            3: [255, 235, 59, 255],   # Yellow (Sedang)
            4: [255, 152, 0, 255],    # Orange (Padat)
            5: [244, 67, 54, 255]     # Red (Macet)
        }
    
    def get_aqi_color(self, aqi_value):
        """Get color based on AQI value."""
        if pd.isna(aqi_value):
            return [128, 128, 128, 255]
        
        aqi_value = int(aqi_value)
        if aqi_value <= 50:
            return [76, 175, 80, 255]  # Good - Green
        elif aqi_value <= 100:
            return [255, 235, 59, 255]  # Moderate - Yellow
        elif aqi_value <= 150:
            return [255, 152, 0, 255]  # Unhealthy for Sensitive - Orange
        elif aqi_value <= 200:
            return [244, 67, 54, 255]  # Unhealthy - Red
        elif aqi_value <= 300:
            return [156, 39, 176, 255]  # Very Unhealthy - Purple
        else:
            return [126, 87, 194, 255]  # Hazardous - Dark Purple
    
    def get_traffic_color(self, traffic_level):
        """Get color based on traffic level."""
        if pd.isna(traffic_level):
            return [128, 128, 128, 255]
        return self.traffic_colors.get(int(traffic_level), [128, 128, 128, 255])
    
    def format_timestamp(self, ts):
        """Format timestamp for display."""
        if pd.isna(ts):
            return "N/A"
        
        try:
            if isinstance(ts, str):
                dt = pd.to_datetime(ts)
            else:
                dt = ts
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(ts)
    
    def create_aqi_pinpoint_map(self, data) -> pdk.Deck:
        """Create AQI pinpoint map visualization with colored markers and text labels."""
        if data.empty or data['latitude'].empty or data['longitude'].empty:
            view_state = pdk.ViewState(
                latitude=-6.200000,
                longitude=106.816666,
                zoom=10,
                pitch=0,
            )
            map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
            return pdk.Deck(layers=[], initial_view_state=view_state, map_style=map_style)

        # Prepare data
        data = data.copy()
        data['fill_color'] = data['aqi_value'].apply(self.get_aqi_color)
        data['formatted_time'] = data['timestamp'].apply(self.format_timestamp)
        data['text_label'] = data['aqi_value'].apply(lambda x: str(int(x)) if pd.notna(x) else "")
        
        # Calculate center
        lat_mean = data['latitude'].dropna().mean()
        lon_mean = data['longitude'].dropna().mean()

        view_state = pdk.ViewState(
            latitude=lat_mean if pd.notna(lat_mean) else -6.200000,
            longitude=lon_mean if pd.notna(lon_mean) else 106.816666,
            zoom=10.5,
            pitch=0,
        )

        # ScatterplotLayer for colored circles
        scatterplot_layer = pdk.Layer(
            "ScatterplotLayer",
            data=data,
            get_position=["longitude", "latitude"],
            get_fill_color="fill_color",
            get_line_color=[255, 255, 255, 200],
            get_radius=1200,
            line_width_min_pixels=2,
            pickable=True,
            auto_highlight=True,
            opacity=0.9,
            stroked=True,
        )
        
        # TextLayer for values - LARGER and WHITE
        text_layer = pdk.Layer(
            "TextLayer",
            data=data,
            get_position=["longitude", "latitude"],
            get_text="text_label",
            get_size=150,  # MUCH LARGER
            get_color=[255, 255, 255, 255],  # WHITE TEXT
            get_angle=0,
            get_text_anchor='"middle"',
            get_alignment_baseline='"center"',
            pickable=False,
            billboard=True,
            font_family='"Arial Black", sans-serif',
            font_weight=500,
        )

        map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

        return pdk.Deck(
            layers=[scatterplot_layer, text_layer],
            initial_view_state=view_state,
            map_style=map_style,
            tooltip={
                "html": """
                <div style="background-color: rgba(0, 0, 0, 0.9); padding: 15px; border-radius: 8px; 
                            color: white; font-family: Arial, sans-serif; min-width: 220px; border: 2px solid #4CAF50;">
                    <div style="font-weight: bold; font-size: 16px; margin-bottom: 10px; 
                                border-bottom: 2px solid #4CAF50; padding-bottom: 6px;">
                        📍 {location}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #FFD700;">🌫️ AQI Value:</span> 
                        <span style="font-weight: bold; font-size: 20px; color: #FFD700;">{aqi_value}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #87CEEB;">📊 Category:</span> 
                        <span style="font-weight: bold;">{aqi_category}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #98FB98;">📅 Time:</span> 
                        <span>{formatted_time}</span>
                    </div>
                    <div style="font-size: 10px; color: #999; margin-top: 10px; font-style: italic;">
                        Lat: {latitude}, Lon: {longitude}
                    </div>
                </div>
                """,
                "style": {"backgroundColor": "transparent", "color": "white"}
            }
        )

    def create_traffic_pinpoint_map(self, data) -> pdk.Deck:
        """Create traffic pinpoint map visualization with colored markers and text labels."""
        if data.empty or data['latitude'].empty or data['longitude'].empty:
            view_state = pdk.ViewState(
                latitude=-6.200000,
                longitude=106.816666,
                zoom=10,
                pitch=0,
            )
            map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
            return pdk.Deck(layers=[], initial_view_state=view_state, map_style=map_style)

        # Prepare data
        data = data.copy()
        data['fill_color'] = data['traffic_level'].apply(self.get_traffic_color)
        data['formatted_time'] = data['timestamp'].apply(self.format_timestamp)
        data['text_label'] = data['traffic_level'].apply(lambda x: str(int(x)) if pd.notna(x) else "")
        
        # Calculate center
        lat_mean = data['latitude'].dropna().mean()
        lon_mean = data['longitude'].dropna().mean()

        view_state = pdk.ViewState(
            latitude=lat_mean if pd.notna(lat_mean) else -6.200000,
            longitude=lon_mean if pd.notna(lon_mean) else 106.816666,
            zoom=10.5,
            pitch=0,
        )

        # ScatterplotLayer for colored circles
        scatterplot_layer = pdk.Layer(
            "ScatterplotLayer",
            data=data,
            get_position=["longitude", "latitude"],
            get_fill_color="fill_color",
            get_line_color=[255, 255, 255, 200],
            get_radius=1200,
            line_width_min_pixels=2,
            pickable=True,
            auto_highlight=True,
            opacity=0.9,
            stroked=True,
        )
        
        # TextLayer for values - LARGER and WHITE
        text_layer = pdk.Layer(
            "TextLayer",
            data=data,
            get_position=["longitude", "latitude"],
            get_text="text_label",
            get_size=150,  # MUCH LARGER
            get_color=[255, 255, 255, 255],  # WHITE TEXT
            get_angle=0,
            get_text_anchor='"middle"',
            get_alignment_baseline='"center"',
            pickable=False,
            billboard=True,
            font_family='"Arial Black", sans-serif',
            font_weight=500,
        )

        map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

        return pdk.Deck(
            layers=[scatterplot_layer, text_layer],
            initial_view_state=view_state,
            map_style=map_style,
            tooltip={
                "html": """
                <div style="background-color: rgba(0, 0, 0, 0.9); padding: 15px; border-radius: 8px; 
                            color: white; font-family: Arial, sans-serif; min-width: 220px; border: 2px solid #2196F3;">
                    <div style="font-weight: bold; font-size: 16px; margin-bottom: 10px; 
                                border-bottom: 2px solid #2196F3; padding-bottom: 6px;">
                        📍 {location}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #FFD700;">🚗 Traffic Level:</span> 
                        <span style="font-weight: bold; font-size: 20px; color: #FFD700;">{traffic_level}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #87CEEB;">⏰ Peak Hour:</span> 
                        <span style="font-weight: bold;">{is_peak_hour}</span>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #98FB98;">📅 Time:</span> 
                        <span>{formatted_time}</span>
                    </div>
                    <div style="font-size: 10px; color: #999; margin-top: 10px; font-style: italic;">
                        Lat: {latitude}, Lon: {longitude}
                    </div>
                </div>
                """,
                "style": {"backgroundColor": "transparent", "color": "white"}
            }
        )
    
    # Keep old methods for backward compatibility
    def create_aqi_heatmap(self, data) -> pdk.Deck:
        """Legacy method - redirects to pinpoint map."""
        return self.create_aqi_pinpoint_map(data)
    
    def create_traffic_heatmap(self, data) -> pdk.Deck:
        """Legacy method - redirects to pinpoint map."""
        return self.create_traffic_pinpoint_map(data)