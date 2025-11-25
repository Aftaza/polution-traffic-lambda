# Testing Guide - Map Base Layer Fix

## Quick Test Steps

### 1. Rebuild Docker Containers
```bash
# Stop and remove existing containers
docker-compose down

# Rebuild and start all services
docker-compose up --build
```

### 2. Wait for Services to Start
Watch the logs for these messages:
- ✅ PostgreSQL: "database system is ready to accept connections"
- ✅ Ingestion Service: "SQLAlchemy engine berhasil dibuat"
- ✅ Streamlit: "You can now view your Streamlit app in your browser"

### 3. Access the Application
Open your browser and navigate to:
```
http://localhost:8501
```

### 4. Verify the Fix
Check that you can see:
- ✅ Dark map background with street names
- ✅ Geographic features (roads, water bodies, etc.)
- ✅ Heatmap layers rendering on top of the map
- ✅ Both AQI and Traffic heatmaps display correctly

### 5. Expected Behavior
**Before the fix:**
- Map area was blank/white
- Only heatmap colors visible without geographic context

**After the fix:**
- Dark themed map with Carto basemap
- Clear street names and geographic features
- Heatmap overlays properly positioned on the map

## Troubleshooting

### If the map still doesn't appear:

1. **Check browser console for errors:**
   - Press F12 to open developer tools
   - Look for any network errors or warnings

2. **Verify internet connection:**
   - The Carto basemap requires internet access to load tiles

3. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

4. **Check Docker logs:**
   ```bash
   docker-compose logs streamlit_app
   ```

### If no data appears:

1. **Verify API keys are set in .env file:**
   - TOMTOM_API_KEY
   - AQICN_TOKEN

2. **Check ingestion service logs:**
   ```bash
   docker-compose logs ingestion_service
   ```

## Alternative: Using Mapbox (Optional)

If you prefer Mapbox styles:

1. Get a free token from https://www.mapbox.com/
2. Add to `.env`:
   ```
   MAPBOX_TOKEN=pk.your_token_here
   ```
3. Update `docker-compose.yml` streamlit_app service:
   ```yaml
   environment:
     MAPBOX_TOKEN: ${MAPBOX_TOKEN}
   ```
4. Change map_style in `models/visualization.py`:
   ```python
   map_style = "mapbox://styles/mapbox/dark-v10"
   ```
5. Rebuild: `docker-compose up --build`
