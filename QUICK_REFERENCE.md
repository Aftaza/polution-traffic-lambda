# Quick Reference: New Features

## 🎯 What's New

### 1. AQI Legend (Air Quality Index)
A color-coded legend that helps you understand air quality levels at a glance.

**How to Read:**
- **Green (0-50)**: Good - Air quality is satisfactory
- **Yellow (50-100)**: Moderate - Acceptable for most people
- **Orange (100-150)**: Unhealthy for Sensitive Groups - May affect children, elderly, and people with respiratory conditions
- **Red (150-200)**: Unhealthy - Everyone may begin to experience health effects
- **Purple (200-300)**: Very Unhealthy - Health alert, everyone may experience serious effects
- **Dark Purple (300-500)**: Hazardous - Emergency conditions, entire population affected

### 2. Peak Hours Analysis
Shows when pollution and traffic are typically at their worst.

**Displays:**
- 🌫️ **Peak Pollution Hour**: When AQI is highest (in WIB timezone)
- 🚗 **Peak Traffic Hour**: When traffic congestion is worst (in WIB timezone)
- 📈 **Hourly Breakdown**: Detailed statistics for each hour of the day

**Timezone:** All times are shown in WIB (UTC+7) - Jakarta local time

## 📍 Where to Find

### On the Dashboard:
```
┌─────────────────────────────────────────────────────┐
│ 🚦 Heatmap Traffic & Polusi Jakarta (Real-Time)    │
├─────────────────────────────────────────────────────┤
│ Update Terakhir: 2025-11-25 14:17:34 WIB           │
├──────────────────┬──────────────────────────────────┤
│ 📊 Legenda AQI   │ ⏰ Analisis Jam Puncak (UTC+7)   │
│                  │                                  │
│ 0-50   Good      │ 🌫️ Polusi    🚗 Kemacetan      │
│ 50-100 Moderate  │ 08:00 WIB    17:00 WIB          │
│ ...              │ AQI: 125.3   Level: 4.2         │
│                  │                                  │
│                  │ [📈 Lihat Data Per Jam]         │
├──────────────────┴──────────────────────────────────┤
│ 1. Peta Panas Kualitas Udara (AQI)                 │
│ [MAP VISUALIZATION]                                 │
│                                                     │
│ 2. Peta Panas Kemacetan Lalu Lintas                │
│ [MAP VISUALIZATION]                                 │
└─────────────────────────────────────────────────────┘
```

## 💡 Usage Tips

### Understanding Peak Hours
1. **Avoid Peak Times**: Plan your outdoor activities outside peak pollution hours
2. **Traffic Planning**: Avoid traveling during peak traffic hours
3. **Health Considerations**: People with respiratory conditions should be extra careful during peak pollution hours

### Using the Hourly Breakdown
1. Click "📈 Lihat Data Per Jam" to expand
2. View average AQI and traffic levels for each hour
3. Identify patterns throughout the day
4. Plan your schedule accordingly

### Reading the Heatmaps
1. Check the legend to understand color meanings
2. Red areas = High pollution or heavy traffic
3. Green areas = Good air quality or light traffic
4. Use zoom and pan to explore specific areas

## 🔄 Data Updates

- **Refresh Rate**: Data updates every 10 seconds
- **Historical Analysis**: Peak hours calculated from all available data
- **Timezone**: All times automatically converted to WIB (UTC+7)

## 🛠️ Troubleshooting

### Legend Not Showing
- Ensure data is available in the database
- Check that the ingestion service is running
- Refresh the page (F5)

### Peak Hours Show "Data tidak cukup"
- Need at least a few hours of data
- Wait for more data to be collected
- Check ingestion service logs

### Times Look Wrong
- All times are in WIB (UTC+7)
- If you see UTC times, the timezone conversion may have failed
- Check browser console for errors

## 📊 Example Interpretation

**Scenario:**
```
Peak Pollution Hour: 08:00 WIB (AQI: 125.3)
Peak Traffic Hour: 17:00 WIB (Level: 4.2)
```

**Interpretation:**
- Morning rush hour (8 AM) has highest pollution - likely from vehicle emissions
- Evening rush hour (5 PM) has worst traffic congestion
- AQI of 125.3 = "Unhealthy for Sensitive Groups" (orange category)
- Traffic level 4.2 = Heavy congestion

**Recommendations:**
- Sensitive groups should avoid outdoor activities around 8 AM
- Plan trips to avoid 5 PM if possible
- Consider using public transportation during peak hours
- Check real-time data before going out

## 🚀 Quick Start

1. Open the dashboard: http://localhost:8501
2. Look at the top section for legend and peak hours
3. Use the legend to interpret heatmap colors
4. Note the peak hours for planning
5. Expand hourly data for detailed insights
6. Scroll down to view the heatmaps

## 📝 Notes

- Peak hours are based on historical averages
- Actual conditions may vary day-to-day
- Always check the "Update Terakhir" timestamp for data freshness
- Legend follows EPA (Environmental Protection Agency) AQI standards
