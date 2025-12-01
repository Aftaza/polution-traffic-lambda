"""
Predictive Models for Jakarta Traffic & Pollution Analysis

This module implements various machine learning models for predicting:
1. AQI (Air Quality Index) values
2. Traffic levels
3. Time series forecasting

Models included:
- Random Forest Regressor/Classifier
- Gradient Boosting (XGBoost)
- LSTM for time series
- Linear Regression (baseline)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
import pickle
import json

# Scikit-learn models
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

# Try to import XGBoost (optional)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available. Install with: pip install xgboost")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AQIPredictionModel:
    """Model for predicting AQI values."""
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize AQI prediction model.
        
        Args:
            model_type: Type of model ('random_forest', 'xgboost', 'gradient_boosting', 'linear')
        """
        self.model_type = model_type
        self.model = None
        self.feature_importance = None
        self.training_history = {}
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the selected model."""
        if self.model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=8,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=8,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'linear':
            self.model = Ridge(alpha=1.0, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        logger.info(f"Initialized {self.model_type} model for AQI prediction")
    
    def prepare_features(self, df: pd.DataFrame, target_col: str = 'aqi_value') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target for training.
        
        Args:
            df: DataFrame with features
            target_col: Name of target column
            
        Returns:
            Tuple of (X, y)
        """
        # Define feature columns
        feature_cols = [
            'hour', 'day_of_week', 'month', 'is_weekend', 'is_rush_hour',
            'traffic_level', 'latitude', 'longitude'
        ]
        
        # Add lag features if available
        lag_features = [col for col in df.columns if 'lag' in col or 'ma' in col]
        feature_cols.extend(lag_features)
        
        # Filter to only existing columns
        feature_cols = [col for col in feature_cols if col in df.columns]
        
        # Remove rows with NaN in target or features
        df_clean = df.dropna(subset=[target_col] + feature_cols)
        
        X = df_clean[feature_cols]
        y = df_clean[target_col]
        
        logger.info(f"Prepared {len(feature_cols)} features with {len(X)} samples")
        return X, y
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None,
              y_val: Optional[pd.Series] = None,
              tune_hyperparameters: bool = False) -> Dict[str, Any]:
        """
        Train the model.
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            tune_hyperparameters: Whether to perform hyperparameter tuning
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training {self.model_type} model...")
        start_time = datetime.now()
        
        if tune_hyperparameters:
            self.model = self._tune_hyperparameters(X_train, y_train)
        else:
            self.model.fit(X_train, y_train)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate training metrics
        y_train_pred = self.model.predict(X_train)
        train_metrics = self._calculate_metrics(y_train, y_train_pred, 'train')
        
        # Calculate validation metrics if provided
        val_metrics = {}
        if X_val is not None and y_val is not None:
            y_val_pred = self.model.predict(X_val)
            val_metrics = self._calculate_metrics(y_val, y_val_pred, 'validation')
        
        # Store feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': X_train.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
        
        # Store training history
        self.training_history = {
            'model_type': self.model_type,
            'training_time': training_time,
            'train_samples': len(X_train),
            'features': list(X_train.columns),
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Training complete in {training_time:.2f}s")
        logger.info(f"Train RMSE: {train_metrics['rmse']:.2f}, R²: {train_metrics['r2']:.4f}")
        
        return self.training_history
    
    def _tune_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Perform hyperparameter tuning using GridSearchCV."""
        logger.info("Tuning hyperparameters...")
        
        if self.model_type == 'random_forest':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 15, 20],
                'min_samples_split': [2, 5, 10]
            }
        elif self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 8, 10],
                'learning_rate': [0.01, 0.1, 0.2]
            }
        else:
            logger.warning("Hyperparameter tuning not implemented for this model type")
            return self.model
        
        grid_search = GridSearchCV(
            self.model,
            param_grid,
            cv=3,
            scoring='neg_mean_squared_error',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        logger.info(f"Best parameters: {grid_search.best_params_}")
        
        return grid_search.best_estimator_
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray, 
                          prefix: str = '') -> Dict[str, float]:
        """Calculate regression metrics."""
        metrics = {
            f'{prefix}_rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            f'{prefix}_mae': mean_absolute_error(y_true, y_pred),
            f'{prefix}_r2': r2_score(y_true, y_pred),
            f'{prefix}_mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        }
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            raise ValueError("Model not trained yet")
        return self.model.predict(X)
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test features
            y_test: Test target
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating model on test set...")
        
        y_pred = self.predict(X_test)
        metrics = self._calculate_metrics(y_test, y_pred, 'test')
        
        # Additional analysis
        residuals = y_test - y_pred
        metrics['test_residual_mean'] = np.mean(residuals)
        metrics['test_residual_std'] = np.std(residuals)
        
        logger.info(f"Test RMSE: {metrics['test_rmse']:.2f}, R²: {metrics['test_r2']:.4f}")
        
        return metrics
    
    def save_model(self, filepath: str):
        """Save model to file."""
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_importance': self.feature_importance,
            'training_history': self.training_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model from file."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.feature_importance = model_data.get('feature_importance')
        self.training_history = model_data.get('training_history', {})
        
        logger.info(f"Model loaded from {filepath}")


class TrafficPredictionModel:
    """Model for predicting traffic levels (classification)."""
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize traffic prediction model.
        
        Args:
            model_type: Type of model ('random_forest', 'xgboost', 'gradient_boosting')
        """
        self.model_type = model_type
        self.model = None
        self.feature_importance = None
        self.training_history = {}
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the selected model."""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=8,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        logger.info(f"Initialized {self.model_type} model for traffic prediction")
    
    def prepare_features(self, df: pd.DataFrame, target_col: str = 'traffic_level') -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for training."""
        feature_cols = [
            'hour', 'day_of_week', 'month', 'is_weekend', 'is_rush_hour',
            'aqi_value', 'latitude', 'longitude'
        ]
        
        # Add lag features if available
        lag_features = [col for col in df.columns if 'lag' in col or 'ma' in col]
        feature_cols.extend(lag_features)
        
        # Filter to only existing columns
        feature_cols = [col for col in feature_cols if col in df.columns]
        
        # Remove rows with NaN
        df_clean = df.dropna(subset=[target_col] + feature_cols)
        
        X = df_clean[feature_cols]
        y = df_clean[target_col]
        
        logger.info(f"Prepared {len(feature_cols)} features with {len(X)} samples")
        return X, y
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None,
              y_val: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Train the classification model."""
        logger.info(f"Training {self.model_type} classifier...")
        start_time = datetime.now()
        
        self.model.fit(X_train, y_train)
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate training metrics
        y_train_pred = self.model.predict(X_train)
        train_metrics = {
            'train_accuracy': accuracy_score(y_train, y_train_pred),
            'train_f1': f1_score(y_train, y_train_pred, average='weighted')
        }
        
        # Validation metrics
        val_metrics = {}
        if X_val is not None and y_val is not None:
            y_val_pred = self.model.predict(X_val)
            val_metrics = {
                'val_accuracy': accuracy_score(y_val, y_val_pred),
                'val_f1': f1_score(y_val, y_val_pred, average='weighted')
            }
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': X_train.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
        
        self.training_history = {
            'model_type': self.model_type,
            'training_time': training_time,
            'train_samples': len(X_train),
            'features': list(X_train.columns),
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Training complete. Accuracy: {train_metrics['train_accuracy']:.4f}")
        return self.training_history
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            raise ValueError("Model not trained yet")
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities."""
        if self.model is None:
            raise ValueError("Model not trained yet")
        return self.model.predict_proba(X)
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """Evaluate model on test set."""
        logger.info("Evaluating traffic model on test set...")
        
        y_pred = self.predict(X_test)
        
        metrics = {
            'test_accuracy': accuracy_score(y_test, y_pred),
            'test_precision': precision_score(y_test, y_pred, average='weighted'),
            'test_recall': recall_score(y_test, y_pred, average='weighted'),
            'test_f1': f1_score(y_test, y_pred, average='weighted'),
            'classification_report': classification_report(y_test, y_pred)
        }
        
        logger.info(f"Test Accuracy: {metrics['test_accuracy']:.4f}, F1: {metrics['test_f1']:.4f}")
        
        return metrics
    
    def save_model(self, filepath: str):
        """Save model to file."""
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_importance': self.feature_importance,
            'training_history': self.training_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model from file."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.feature_importance = model_data.get('feature_importance')
        self.training_history = model_data.get('training_history', {})
        
        logger.info(f"Model loaded from {filepath}")


class TimeSeriesForecaster:
    """Time series forecasting for AQI and traffic."""
    
    def __init__(self, forecast_horizon: int = 24):
        """
        Initialize time series forecaster.
        
        Args:
            forecast_horizon: Number of hours to forecast ahead
        """
        self.forecast_horizon = forecast_horizon
        self.models = {}  # One model per location
        
    def prepare_sequences(self, df: pd.DataFrame, 
                         target_col: str,
                         lookback: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for time series prediction.
        
        Args:
            df: DataFrame sorted by timestamp
            target_col: Column to predict
            lookback: Number of past timesteps to use
            
        Returns:
            Tuple of (X, y) arrays
        """
        data = df[target_col].values
        X, y = [], []
        
        for i in range(lookback, len(data) - self.forecast_horizon):
            X.append(data[i-lookback:i])
            y.append(data[i:i+self.forecast_horizon])
        
        return np.array(X), np.array(y)
    
    def train_per_location(self, df: pd.DataFrame, target_col: str = 'aqi_value'):
        """Train separate models for each location."""
        logger.info(f"Training time series models for {target_col}...")
        
        for location in df['location'].unique():
            df_loc = df[df['location'] == location].sort_values('timestamp')
            
            X, y = self.prepare_sequences(df_loc, target_col)
            
            if len(X) > 0:
                # Use simple linear model for each location
                model = LinearRegression()
                model.fit(X, y)
                self.models[location] = model
                
                logger.info(f"Trained model for {location}")
    
    def forecast(self, df: pd.DataFrame, location: str, 
                target_col: str = 'aqi_value',
                lookback: int = 24) -> np.ndarray:
        """Make forecast for a specific location."""
        if location not in self.models:
            raise ValueError(f"No model trained for location: {location}")
        
        # Get last lookback values
        df_loc = df[df['location'] == location].sort_values('timestamp')
        last_values = df_loc[target_col].tail(lookback).values
        
        if len(last_values) < lookback:
            raise ValueError(f"Not enough data for forecast (need {lookback} points)")
        
        X = last_values.reshape(1, -1)
        forecast = self.models[location].predict(X)
        
        return forecast[0]


def main():
    """Example usage of predictive models."""
    from .database import Database
    from .preprocessing import DataPreprocessor
    
    # Initialize
    db = Database()
    preprocessor = DataPreprocessor()
    
    # Load and preprocess data
    with db.get_connection() as conn:
        df_raw = preprocessor.load_data_from_db(conn, 'raw_data')
    
    df_processed = preprocessor.preprocess_pipeline(df_raw, include_feature_engineering=True)
    
    # Train/test split
    train_df, test_df = preprocessor.create_train_test_split(df_processed, test_size=0.2)
    
    # AQI Prediction Model
    print("\n=== Training AQI Prediction Model ===")
    aqi_model = AQIPredictionModel(model_type='random_forest')
    X_train, y_train = aqi_model.prepare_features(train_df, 'aqi_value')
    X_test, y_test = aqi_model.prepare_features(test_df, 'aqi_value')
    
    aqi_model.train(X_train, y_train, X_test, y_test)
    aqi_metrics = aqi_model.evaluate(X_test, y_test)
    
    print("\nAQI Model Performance:")
    for key, value in aqi_metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
    
    # Save model
    aqi_model.save_model('aqi_model.pkl')
    
    # Traffic Prediction Model
    print("\n=== Training Traffic Prediction Model ===")
    traffic_model = TrafficPredictionModel(model_type='random_forest')
    X_train, y_train = traffic_model.prepare_features(train_df, 'traffic_level')
    X_test, y_test = traffic_model.prepare_features(test_df, 'traffic_level')
    
    traffic_model.train(X_train, y_train, X_test, y_test)
    traffic_metrics = traffic_model.evaluate(X_test, y_test)
    
    print("\nTraffic Model Performance:")
    for key, value in traffic_metrics.items():
        if isinstance(value, (int, float)):
            print(f"{key}: {value:.4f}")
    
    traffic_model.save_model('traffic_model.pkl')
    
    print("\n✅ Models trained and saved successfully!")


if __name__ == "__main__":
    main()
