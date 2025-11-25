# Bug Fixes - TypeError and Legend Color

## Issues Fixed

### 1. TypeError: Already tz-aware, use tz_convert to convert

**Problem:**
The `analyze_peak_hours` function was attempting to localize timestamps that were already timezone-aware, causing a TypeError.

**Root Cause:**
The code was calling `dt.tz_localize('UTC')` on timestamps that already had timezone information, which is not allowed in pandas.

**Solution:**
Added a check to determine if the timestamp column is already timezone-aware:
- If **not timezone-aware**: Use `tz_localize('UTC')` then `tz_convert(jakarta_tz)`
- If **already timezone-aware**: Use only `tz_convert(jakarta_tz)`

**Code Change in `utils.py`:**
```python
# Before (caused error):
df_analysis['timestamp_jakarta'] = df_analysis['timestamp'].dt.tz_localize('UTC').dt.tz_convert(jakarta_tz)

# After (fixed):
if df_analysis['timestamp'].dt.tz is None:
    # Not timezone-aware, localize first
    df_analysis['timestamp_jakarta'] = df_analysis['timestamp'].dt.tz_localize('UTC').dt.tz_convert(jakarta_tz)
else:
    # Already timezone-aware, just convert
    df_analysis['timestamp_jakarta'] = df_analysis['timestamp'].dt.tz_convert(jakarta_tz)
```

### 2. Legend Label Color Not Visible

**Problem:**
The legend category labels were using dark color (#333) which was not visible on Streamlit's dark background.

**Solution:**
Changed the text color from `#333` (dark gray) to `white` for better visibility.

**Code Change in `app.py`:**
```python
# Before:
<div style="font-size: 14px; color: #333;">
    {category}
</div>

# After:
<div style="font-size: 14px; color: white;">
    {category}
</div>
```

## Files Modified

1. **`utils.py`** (lines 74-80)
   - Added timezone-aware check in `analyze_peak_hours()` function
   
2. **`app.py`** (line 68)
   - Changed legend label color to white

## Testing

After these fixes, the application should:
- ✅ Display peak hours analysis without errors
- ✅ Show legend labels in white color (visible on dark background)
- ✅ Handle both timezone-aware and timezone-naive timestamps correctly

## How to Apply

1. The changes have been automatically applied to your files
2. Restart the Streamlit app:
   ```bash
   docker-compose restart streamlit_app
   ```
3. Refresh your browser (F5)
4. Verify:
   - No TypeError appears
   - Legend labels are visible in white
   - Peak hours analysis displays correctly

## Technical Details

### Timezone Handling Logic
```python
# Check if timestamp has timezone info
if df_analysis['timestamp'].dt.tz is None:
    # Naive datetime - needs localization
    # Step 1: Assume it's UTC
    # Step 2: Convert to Jakarta time (UTC+7)
    df_analysis['timestamp_jakarta'] = (
        df_analysis['timestamp']
        .dt.tz_localize('UTC')
        .dt.tz_convert(jakarta_tz)
    )
else:
    # Already has timezone - just convert
    df_analysis['timestamp_jakarta'] = (
        df_analysis['timestamp']
        .dt.tz_convert(jakarta_tz)
    )
```

This approach handles both cases:
- **PostgreSQL timestamps without timezone** (naive)
- **PostgreSQL timestamps with timezone** (aware)

## Date Fixed
2025-11-25 14:24 WIB
