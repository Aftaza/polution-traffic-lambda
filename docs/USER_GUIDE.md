# User Guide

Complete guide for using the Jakarta Traffic & Pollution Monitoring Dashboard.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Features Guide](#features-guide)
4. [Data Interpretation](#data-interpretation)
5. [FAQ](#faq)

---

## Getting Started

### Accessing the Dashboard

**Local Deployment:**
```
http://localhost:8501
```

**Production:**
```
http://your-domain.com
```

### First Time Setup

1. Wait 5-10 minutes after deployment for data to accumulate
2. Dashboard will show "Waiting for data..." until first data arrives
3. Refresh browser if needed

---

## Dashboard Overview

### Main Interface

The dashboard consists of 4 main tabs:

1. **🗺️ Heatmaps** - Visual maps of traffic and air quality
2. **📊 Peak Hours Analysis** - Hourly trends and patterns
3. **📈 Statistics** - Real-time metrics and distributions
4. **📋 Raw Data** - Detailed data table

### Header Information

```
┌─────────────────────────────────────────────────────────┐
│ Update Terakhir: 2025-12-02 09:15:00 WIB | Records: 150│
│ 📡 Speed Layer (Real-time)                              │
└─────────────────────────────────────────────────────────┘
```

- **Update Terakhir:** Last data update time (in WIB/UTC+7)
- **Total Records:** Number of data points currently displayed
- **Data Source:** 
  - 📡 Speed Layer (Real-time) - Data < 1 hour old
  - 📊 Batch Layer (Historical) - Data > 1 hour old

### Sidebar

**Peak Hours Info:**
- Morning Peak: 06:00 - 10:00
- Evening Peak: 16:00 - 20:00
- Current Status: Peak/Off-Peak indicator

**Architecture Info:**
- Speed Layer: Real-time data
- Batch Layer: Historical aggregations
- Serving Layer: Unified access

---

## Features Guide

### Tab 1: 🗺️ Heatmaps

#### Traffic Map

**Purpose:** Visualize traffic congestion across Jakarta

**How to Use:**
1. View colored pinpoints on map
2. Each pinpoint represents a location
3. Number inside = Traffic Level (1-5)
4. Color indicates severity:
   - 🟢 Green (1-2): Lancar
   - 🟡 Yellow (3): Sedang
   - 🟠 Orange (4): Padat
   - 🔴 Red (5): Macet Total

**Interactions:**
- **Hover:** View detailed information card
- **Zoom:** Use mouse wheel or pinch gesture
- **Pan:** Click and drag to move map

**Tooltip Information:**
```
📍 Jakarta Pusat
🚗 Traffic Level: 4
⏰ Peak Hour: Yes
📅 Time: 2025-12-02 09:15:00 WIB
Lat: -6.2088, Lon: 106.8456
```

#### AQI Map

**Purpose:** Visualize air quality across Jakarta

**How to Use:**
1. View colored pinpoints on map
2. Each pinpoint represents a location
3. Number inside = AQI Value
4. Color indicates air quality:
   - 🟢 Green (0-50): Good
   - 🟡 Yellow (51-100): Moderate
   - 🟠 Orange (101-150): Unhealthy for Sensitive
   - 🔴 Red (151-200): Unhealthy
   - 🟣 Purple (201-300): Very Unhealthy
   - ☠️ Dark Purple (300+): Hazardous

**Tooltip Information:**
```
📍 Jakarta Pusat
🌫️ AQI Value: 88
📊 Category: Moderate
📅 Time: 2025-12-02 09:15:00 WIB
Lat: -6.2088, Lon: 106.8456
```

#### Legend

Located below each map, shows:
- Color coding
- Value ranges
- Category names

---

### Tab 2: 📊 Peak Hours Analysis

#### Purpose
Analyze traffic and air quality patterns throughout the day over the last 7 days.

#### Charts

**1. Average Traffic Level by Hour**
- Bar chart showing average traffic for each hour
- Red bars = Peak hours (6-10 AM, 4-8 PM)
- Blue bars = Off-peak hours

**2. Average AQI by Hour**
- Bar chart showing average AQI for each hour
- Orange bars = Peak hours
- Green bars = Off-peak hours

**3. Combined View - Traffic vs AQI**
- Line chart with dual Y-axis
- Blue line = Traffic Level
- Red line = AQI (scaled)
- Yellow background = Morning peak
- Orange background = Evening peak

#### Interpretation

**Peak Hours Indicator:**
- Yellow/Orange background shows peak hours
- Compare traffic and AQI during peak vs off-peak
- Identify patterns and correlations

**Example Insights:**
- "Traffic highest at 8 AM (morning rush)"
- "AQI peaks at 7 PM (evening traffic + pollution)"
- "Best time to travel: 2-4 PM (lowest traffic)"

---

### Tab 3: 📈 Statistics

#### Traffic Statistics

**Metrics:**
- **Average Traffic Level:** Mean traffic across all locations
- **Max Traffic Level:** Highest traffic recorded
- **Peak Hour Records:** Count of data points during peak hours

**Traffic Level Distribution:**
- Bar chart showing frequency of each traffic level
- Helps understand overall traffic conditions

#### AQI Statistics

**Metrics:**
- **Average AQI:** Mean air quality across all locations
- **Max AQI:** Worst air quality recorded

**AQI Category Distribution:**
- Pie chart showing percentage of each AQI category
- Quick overview of air quality conditions

#### How to Use

1. **Monitor Trends:**
   - Check if average values are improving/worsening
   - Compare with previous days

2. **Identify Patterns:**
   - See which traffic levels are most common
   - Understand typical air quality conditions

3. **Make Decisions:**
   - Plan trips based on average conditions
   - Check air quality before outdoor activities

---

### Tab 4: 📋 Raw Data

#### Purpose
View and download detailed data for analysis.

#### Features

**Summary Metrics:**
```
┌─────────────────┬─────────────────┬─────────────────┐
│ Total Records   │ Average AQI     │ Average Traffic │
│      150        │     67.5        │      3.2        │
└─────────────────┴─────────────────┴─────────────────┘
```

**Data Table:**
- **Timestamp (WIB):** When data was collected
- **Location:** Area name
- **AQI Value:** Air quality index
- **AQI Category:** Quality classification
- **Traffic Level:** Congestion level (1-5)
- **Peak Hour:** Yes/No indicator
- **Latitude/Longitude:** GPS coordinates

**Sorting:**
- Click column headers to sort
- Default: Most recent first

**Download:**
- Click "💾 Download CSV" button
- Filename includes timestamp
- Contains top 100 records

#### Use Cases

1. **Data Analysis:**
   - Export for Excel/Python analysis
   - Create custom visualizations
   - Statistical analysis

2. **Reporting:**
   - Generate reports
   - Share with stakeholders
   - Documentation

3. **Verification:**
   - Check specific data points
   - Verify accuracy
   - Troubleshoot issues

---

## Data Interpretation

### Traffic Levels

| Level | Description | Typical Speed | Action |
|-------|-------------|---------------|--------|
| 1 | Lancar | > 50 km/h | ✅ Good time to travel |
| 2 | Agak Lancar | 40-50 km/h | ✅ Acceptable |
| 3 | Sedang | 30-40 km/h | ⚠️ Plan extra time |
| 4 | Padat | 20-30 km/h | ⚠️ Expect delays |
| 5 | Macet Total | < 20 km/h | ❌ Avoid if possible |

### AQI Categories

| Range | Category | Health Impact | Recommendation |
|-------|----------|---------------|----------------|
| 0-50 | Good | Minimal | ✅ Normal activities |
| 51-100 | Moderate | Acceptable | ✅ Sensitive groups be aware |
| 101-150 | Unhealthy for Sensitive | Sensitive groups affected | ⚠️ Limit prolonged outdoor |
| 151-200 | Unhealthy | Everyone affected | ⚠️ Reduce outdoor activities |
| 201-300 | Very Unhealthy | Serious effects | ❌ Avoid outdoor activities |
| 300+ | Hazardous | Emergency conditions | ❌ Stay indoors |

### Peak Hours

**Morning Peak (06:00 - 10:00):**
- Commuters going to work/school
- Highest traffic congestion
- Moderate to high AQI

**Evening Peak (16:00 - 20:00):**
- Commuters returning home
- High traffic congestion
- Often highest AQI (accumulated pollution)

**Off-Peak:**
- Lower traffic levels
- Better air quality
- Recommended for travel

---

## FAQ

### General

**Q: How often is data updated?**
A: Data is collected every 5 minutes from external APIs.

**Q: What timezone is used?**
A: All times are displayed in WIB (UTC+7) for user convenience.

**Q: How far back does historical data go?**
A: Depends on deployment date. System stores all data indefinitely.

**Q: Can I access data from specific dates?**
A: Currently shows last 7 days. Contact admin for historical data access.

### Data

**Q: Why is there no data showing?**
A: Wait 5-10 minutes after initial deployment for data to accumulate.

**Q: What does "Speed Layer" vs "Batch Layer" mean?**
A: 
- Speed Layer: Real-time data (< 1 hour old)
- Batch Layer: Historical aggregations (> 1 hour old)

**Q: Are the values accurate?**
A: Data comes from official sources (TomTom, AQICN). Accuracy depends on their sensors.

**Q: Why do some locations have no data?**
A: API might not have data for that location at that time.

### Technical

**Q: Dashboard is slow. What can I do?**
A: 
1. Refresh browser
2. Clear browser cache
3. Check internet connection
4. Contact administrator

**Q: Can I download all historical data?**
A: Contact administrator for database export.

**Q: Can I integrate this data into my application?**
A: Contact administrator for API access.

**Q: How can I report issues?**
A: Create issue on GitHub or contact administrator.

### Usage

**Q: How do I know if it's a good time to travel?**
A: Check Traffic Map - green/yellow areas are best.

**Q: Should I go outside for exercise?**
A: Check AQI Map - green (0-50) is safe, yellow (51-100) is acceptable.

**Q: When is the best time to avoid traffic?**
A: Check Peak Hours Analysis - typically 10 AM - 4 PM.

**Q: How can I plan my commute?**
A: 
1. Check current traffic on map
2. Review peak hours patterns
3. Plan to travel during off-peak if possible

---

## Tips & Tricks

### Best Practices

1. **Check Before You Go:**
   - View current traffic before leaving
   - Check AQI if planning outdoor activities
   - Review peak hours for planning

2. **Use Historical Data:**
   - Peak Hours Analysis shows patterns
   - Plan regular commutes based on trends
   - Identify best times for your route

3. **Download Data:**
   - Export for personal analysis
   - Track changes over time
   - Create custom reports

### Power User Features

1. **Keyboard Shortcuts:**
   - `Ctrl + R`: Refresh dashboard
   - `Ctrl + F`: Search in data table

2. **URL Parameters:**
   - Add `?tab=1` to open specific tab
   - Bookmark frequently used views

3. **Mobile Usage:**
   - Dashboard is mobile-responsive
   - Pinch to zoom on maps
   - Swipe to navigate tabs

---

## Getting Help

### Support Channels

1. **Documentation:**
   - README.md - Quick start guide
   - docs/ARCHITECTURE.md - Technical details
   - docs/DEPLOYMENT.md - Deployment guide

2. **Issues:**
   - GitHub Issues for bug reports
   - Feature requests welcome

3. **Contact:**
   - Email: your-email@example.com
   - Response time: 24-48 hours

---

**Last Updated:** 2025-12-02  
**Version:** 2.0.0
