# Feature Update: AQI Legend & Peak Hours Analysis

## Summary
Added two new features to the Jakarta Traffic & Pollution Heatmap application:
1. **AQI Legend** - Color-coded legend showing air quality categories
2. **Peak Hours Analysis** - Displays peak pollution and traffic hours in UTC+7 (WIB) timezone

## Features Added

### 1. AQI Legend (📊 Legenda Kualitas Udara)
A visual legend that displays the standard AQI (Air Quality Index) categories with color coding:

| AQI Range | Category | Color |
|-----------|----------|-------|
| 0-50 | Good | Green (#4CAF50) |
| 50-100 | Moderate | Yellow (#FFEB3B) |
| 100-150 | Unhealthy for Sensitive Groups | Orange (#FF9800) |
| 150-200 | Unhealthy | Red (#F44336) |
| 200-300 | Very Unhealthy | Purple (#9C27B0) |
| 300-500 | Hazardous | Dark Purple (#7B1FA2) |

**Location:** Displayed in the left column at the top of the dashboard

### 2. Peak Hours Analysis (⏰ Analisis Jam Puncak)
Analyzes historical data to identify:
- **Peak Pollution Hour**: The hour with the highest average AQI
- **Peak Traffic Hour**: The hour with the highest average traffic level

**Features:**
- ✅ Uses UTC+7 (WIB) timezone for Jakarta
- ✅ Shows peak hours with average values
- ✅ Displays hourly breakdown in an expandable section
- ✅ Real-time calculation based on available data

**Location:** Displayed in the right column at the top of the dashboard

## Files Modified

### 1. `utils.py`
**New Functions Added:**
- `get_jakarta_timezone()` - Returns UTC+7 timezone object
- `get_aqi_category(aqi_value)` - Returns category and color for AQI value
- `analyze_peak_hours(df)` - Analyzes dataframe to find peak hours

**Modified Functions:**
- `format_datetime_for_display(dt)` - Now converts to UTC+7 and adds "WIB" suffix

**New Dependencies:**
```python
from datetime import datetime, timezone, timedelta
import pandas as pd
```

### 2. `app.py`
**New Methods Added:**
- `display_aqi_legend()` - Renders the AQI legend with styled HTML
- `display_peak_hours(df)` - Displays peak hours analysis with metrics

**Modified Methods:**
- `display_data()` - Now includes legend and peak hours display before heatmaps

**Layout Changes:**
- Added two-column layout at the top (1:2 ratio)
- Left column: AQI Legend
- Right column: Peak Hours Analysis

## Technical Details

### Timezone Handling
All timestamps are now properly converted to UTC+7 (WIB - Waktu Indonesia Barat):
```python
jakarta_tz = timezone(timedelta(hours=7))
dt = dt.replace(tzinfo=timezone.utc).astimezone(jakarta_tz)
```

### Peak Hours Algorithm
1. Convert all timestamps to UTC+7
2. Extract hour from each timestamp
3. Group data by hour
4. Calculate average AQI and traffic level for each hour
5. Identify hours with maximum averages

### Styling
The AQI legend uses inline HTML/CSS for consistent rendering:
- Colored boxes with white text showing AQI ranges
- Category names aligned to the right
- Responsive design that works in Streamlit

## Usage

### Viewing the Legend
The AQI legend is always visible when data is available, showing the standard EPA AQI categories.

### Understanding Peak Hours
- **Jam Puncak Polusi**: Shows the hour (in WIB) when air pollution is typically highest
- **Jam Puncak Kemacetan**: Shows the hour (in WIB) when traffic congestion is typically highest
- Click "📈 Lihat Data Per Jam" to see hourly breakdown

## Example Output

### Peak Hours Display
```
⏰ Analisis Jam Puncak (UTC+7)

🌫️ Polusi Udara (AQI)          🚗 Kemacetan Lalu Lintas
Jam Puncak Polusi               Jam Puncak Kemacetan
08:00 WIB                       17:00 WIB
AQI Rata-rata: 125.3            Level Rata-rata: 4.2
```

### Hourly Breakdown Table
| Jam (WIB) | AQI Rata-rata | Traffic Level Rata-rata |
|-----------|---------------|-------------------------|
| 0 | 45.2 | 1.5 |
| 1 | 42.1 | 1.2 |
| ... | ... | ... |
| 8 | 125.3 | 3.8 |
| ... | ... | ... |
| 17 | 98.5 | 4.2 |

## Benefits

1. **Better Understanding**: Users can quickly understand AQI values using the color-coded legend
2. **Planning**: Peak hours help users plan their activities to avoid high pollution/traffic times
3. **Timezone Accuracy**: All times are displayed in local Jakarta time (WIB)
4. **Data Insights**: Hourly breakdown provides detailed patterns throughout the day

## Testing

To test the new features:

1. Ensure you have data in the database
2. Restart the Streamlit app:
   ```bash
   docker-compose restart streamlit_app
   ```
3. Open http://localhost:8501
4. Verify:
   - ✅ AQI legend appears in the left column
   - ✅ Peak hours analysis appears in the right column
   - ✅ Times are shown in WIB format
   - ✅ Hourly breakdown is accessible via expander

## Future Enhancements

Potential improvements:
- Add traffic level legend (similar to AQI)
- Show peak hours on a 24-hour chart
- Add day-of-week analysis
- Compare current values to peak values
- Add notifications when approaching peak hours

## Date Added
2025-11-25
