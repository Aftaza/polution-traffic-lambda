# Quick Start Guide: Running the Analysis Pipeline

## Overview

This guide will help you run the complete analysis pipeline for Jakarta Traffic & Pollution data, including preprocessing, analytics, model training, and evaluation.

## Prerequisites

1. **Docker Environment Running**
   ```bash
   docker-compose ps
   # Ensure all 7 services are running
   ```

2. **Data Available**
   - At least 7 days of data in the `raw_data` table
   - Recommended: 30+ days for better model performance

3. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Analysis

### Option 1: Complete Pipeline (Recommended)

Run the entire analysis pipeline with one command:

```bash
python analysis_pipeline.py
```

**What it does**:
1. Loads last 30 days of data from database
2. Preprocesses data (cleaning, feature engineering)
3. Performs descriptive analytics
4. Trains AQI and Traffic prediction models
5. Evaluates model performance
6. Generates comprehensive reports

**Expected Duration**: 10-15 minutes

**Output Location**: `analysis_results/`

### Option 2: Step-by-Step Execution

#### Step 1: Data Preprocessing

```python
from models.database import Database
from models.preprocessing import DataPreprocessor

db = Database()
preprocessor = DataPreprocessor()

# Load data
with db.get_connection() as conn:
    df_raw = preprocessor.load_data_from_db(conn, 'raw_data')

# Preprocess
df_processed = preprocessor.preprocess_pipeline(
    df_raw, 
    include_feature_engineering=True
)

# Save
df_processed.to_csv('processed_data.csv', index=False)
```

#### Step 2: Descriptive Analytics

```python
from models.analytics import DescriptiveAnalytics

analytics = DescriptiveAnalytics()

# Generate insights
insights = analytics.generate_insights(df_processed)

# Print report
print(analytics.generate_report())

# Save insights
analytics.save_insights('insights.json')
```

#### Step 3: Train Models

```python
from models.predictive_model import AQIPredictionModel, TrafficPredictionModel

# AQI Model
aqi_model = AQIPredictionModel(model_type='random_forest')
X_train, y_train = aqi_model.prepare_features(train_df, 'aqi_value')
aqi_model.train(X_train, y_train)
aqi_model.save_model('aqi_model.pkl')

# Traffic Model
traffic_model = TrafficPredictionModel(model_type='random_forest')
X_train, y_train = traffic_model.prepare_features(train_df, 'traffic_level')
traffic_model.train(X_train, y_train)
traffic_model.save_model('traffic_model.pkl')
```

#### Step 4: Evaluate Models

```python
from models.evaluation import ModelEvaluator

# Evaluate AQI model
evaluator = ModelEvaluator(model_name='AQI Model')
X_test, y_test = aqi_model.prepare_features(test_df, 'aqi_value')
y_pred = aqi_model.predict(X_test)

metrics = evaluator.evaluate_regression(y_test.values, y_pred, 'test')
print(f"RMSE: {metrics['test_rmse']:.2f}")
print(f"R²: {metrics['test_r2']:.4f}")
```

## Understanding the Output

### Directory Structure

```
analysis_results/
├── complete_results.json          # All results in JSON format
├── processed_data.csv             # Preprocessed dataset
├── analysis_pipeline.log          # Execution log
├── models/
│   ├── aqi_model.pkl             # Trained AQI model
│   └── traffic_model.pkl         # Trained traffic model
├── plots/
│   ├── aqi_residuals.png         # Residual analysis plots
│   ├── aqi_feature_importance.png
│   ├── traffic_confusion_matrix.png
│   └── traffic_feature_importance.png
└── reports/
    ├── ANALYSIS_SUMMARY.md        # Executive summary
    ├── analytics_insights.json    # Detailed analytics
    ├── analytics_report.txt       # Text report
    ├── evaluation_results.json    # Model metrics
    └── preprocessing_summary.json # Preprocessing stats
```

### Key Files to Review

1. **ANALYSIS_SUMMARY.md** - Start here for overview
2. **analytics_report.txt** - Descriptive statistics and patterns
3. **evaluation_results.json** - Model performance metrics
4. **plots/** - Visual analysis of model performance

## Interpreting Results

### Preprocessing Summary

```json
{
  "original_records": 50000,
  "processed_records": 47500,
  "records_removed": 2500,
  "removal_percentage": 5.0,
  "new_features": 15
}
```

**Good indicators**:
- Removal percentage < 10%
- New features: 10-20
- No missing values in processed data

### Analytics Insights

**Key Findings Example**:
```
1. [Air Quality] Average AQI is 95.3, classified as 'Moderate'
2. [Temporal Pattern] Peak pollution occurs at 8:00 with average AQI of 125.4
3. [Spatial Pattern] 'Sudirman' has the highest average AQI of 110.2
4. [Temporal Pattern] Weekend AQI is 12.3 points lower than weekdays
```

### Model Performance

**AQI Model (Regression)**:
```
RMSE: 12.5    # Lower is better (target: < 15)
MAE: 8.3      # Lower is better (target: < 10)
R²: 0.87      # Higher is better (target: > 0.85)
MAPE: 14.2%   # Lower is better (target: < 20%)
```

**Traffic Model (Classification)**:
```
Accuracy: 0.89   # Higher is better (target: > 0.85)
Precision: 0.87  # Higher is better (target: > 0.85)
Recall: 0.88     # Higher is better (target: > 0.85)
F1 Score: 0.87   # Higher is better (target: > 0.85)
```

## Common Issues & Solutions

### Issue 1: "No data found"

**Cause**: Database is empty or date range has no data

**Solution**:
```bash
# Check if data exists
docker exec pid-postgres-db psql -U pid_user -d pid_db -c "SELECT COUNT(*) FROM raw_data;"

# If count is 0, wait for ingestion service to collect data
docker logs pid-ingestion-producer
```

### Issue 2: "Not enough features for model training"

**Cause**: Data doesn't have required columns or too few records

**Solution**:
- Ensure at least 1000 records in database
- Check that `aqi_value` and `traffic_level` columns exist
- Verify data quality with preprocessing summary

### Issue 3: "Model performance is poor (R² < 0.7)"

**Possible Causes**:
1. Insufficient data (< 7 days)
2. Poor data quality (> 20% missing)
3. Data distribution changed

**Solutions**:
- Collect more data (aim for 30+ days)
- Check data quality metrics
- Retrain model with recent data

### Issue 4: "Out of memory error"

**Cause**: Dataset too large for available RAM

**Solution**:
```python
# Reduce date range
pipeline.run_complete_analysis(days_back=14)  # Instead of 30

# Or sample data
df_sampled = df.sample(frac=0.5, random_state=42)
```

## Advanced Usage

### Custom Date Range

```python
from datetime import datetime, timedelta

# Last 14 days
pipeline.run_complete_analysis(days_back=14)

# Specific date range (modify code)
start_date = datetime(2025, 11, 1)
end_date = datetime(2025, 11, 27)
```

### Hyperparameter Tuning

```python
# Enable hyperparameter tuning (takes longer)
aqi_model.train(X_train, y_train, tune_hyperparameters=True)
```

### Different Model Types

```python
# Try XGBoost instead of Random Forest
aqi_model = AQIPredictionModel(model_type='xgboost')

# Try Gradient Boosting
aqi_model = AQIPredictionModel(model_type='gradient_boosting')
```

### Custom Feature Engineering

```python
# Add custom features before training
df_processed['hour_squared'] = df_processed['hour'] ** 2
df_processed['aqi_traffic_ratio'] = df_processed['aqi_value'] / (df_processed['traffic_level'] + 1)
```

## Performance Optimization

### For Faster Execution

1. **Reduce data volume**:
   ```python
   pipeline.run_complete_analysis(days_back=7)  # Instead of 30
   ```

2. **Disable hyperparameter tuning**:
   ```python
   aqi_model.train(X_train, y_train, tune_hyperparameters=False)
   ```

3. **Use fewer trees**:
   ```python
   aqi_model = AQIPredictionModel(model_type='random_forest')
   aqi_model.model.n_estimators = 50  # Instead of 100
   ```

### For Better Accuracy

1. **Use more data**:
   ```python
   pipeline.run_complete_analysis(days_back=90)
   ```

2. **Enable hyperparameter tuning**:
   ```python
   aqi_model.train(X_train, y_train, tune_hyperparameters=True)
   ```

3. **Try ensemble methods**:
   ```python
   # Train multiple models and average predictions
   models = [
       AQIPredictionModel(model_type='random_forest'),
       AQIPredictionModel(model_type='xgboost'),
       AQIPredictionModel(model_type='gradient_boosting')
   ]
   ```

## Scheduling Automated Analysis

### Using Cron (Linux/Mac)

```bash
# Run analysis daily at 3 AM
0 3 * * * cd /path/to/case-based && python analysis_pipeline.py >> analysis_cron.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 3:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `analysis_pipeline.py`
7. Start in: `d:\Kuliahku\project\pemrosesan-data\case-based`

### Using Python Script

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from analysis_pipeline import AnalysisPipeline

def run_analysis():
    pipeline = AnalysisPipeline()
    pipeline.run_complete_analysis(days_back=30)

scheduler = BlockingScheduler()
scheduler.add_job(run_analysis, 'cron', hour=3, minute=0)
scheduler.start()
```

## Next Steps

After running the analysis:

1. **Review Results**: Read `ANALYSIS_SUMMARY.md`
2. **Check Model Performance**: Review metrics in `evaluation_results.json`
3. **Visualize**: Open plots in `plots/` directory
4. **Deploy Models**: Use trained models for predictions
5. **Monitor**: Set up automated retraining schedule

## Getting Help

- **Documentation**: See `docs/TECHNICAL_ANALYSIS_DOCUMENTATION.md`
- **Logs**: Check `analysis_pipeline.log` for detailed execution logs
- **Issues**: Review error messages and check common issues above

## Example: Complete Workflow

```bash
# 1. Ensure Docker is running
docker-compose ps

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run analysis
python analysis_pipeline.py

# 4. Review results
cat analysis_results/reports/ANALYSIS_SUMMARY.md

# 5. Check model performance
cat analysis_results/reports/evaluation_results.json

# 6. View plots (open in image viewer)
# analysis_results/plots/aqi_residuals.png
# analysis_results/plots/aqi_feature_importance.png
```

**Expected Output**:
```
================================================================================
STARTING COMPLETE ANALYSIS PIPELINE
================================================================================

[STEP 1/5] Loading and preprocessing data...
Loaded 45000 raw records
Removed 2250 duplicate records
...
Preprocessing complete. Final records: 42750

[STEP 2/5] Performing descriptive analytics...
Generating summary statistics...
Analyzing temporal patterns...
...
Analytics complete

[STEP 3/5] Training prediction models...
Training AQI prediction model...
Training complete in 125.34s
Train RMSE: 10.23, R²: 0.8912
...

[STEP 4/5] Evaluating model performance...
Evaluating AQI model on test set...
Test RMSE: 12.45, R²: 0.8701
...

[STEP 5/5] Generating reports...
Summary report saved to analysis_results/reports/ANALYSIS_SUMMARY.md

================================================================================
ANALYSIS PIPELINE COMPLETED SUCCESSFULLY in 487.23s
Results saved to: analysis_results/
================================================================================

✅ Analysis completed successfully!
📁 Results saved to: analysis_results/
```

---

**Last Updated**: 2025-11-27  
**Version**: 1.0
