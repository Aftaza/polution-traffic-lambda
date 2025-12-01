"""
Data Preprocessing Module for Jakarta Traffic & Pollution Analysis

This module provides comprehensive data preprocessing capabilities including:
- Data cleaning and validation
- Feature engineering
- Outlier detection and handling
- Missing value imputation
- Data normalization and scaling
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Comprehensive data preprocessing for traffic and pollution data."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        self.imputer = SimpleImputer(strategy='mean')
        self.feature_stats = {}
        
    def load_data_from_db(self, conn, table_name: str = 'raw_data', 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load data from database with optional date filtering.
        
        Args:
            conn: Database connection
            table_name: Name of the table to load
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            DataFrame with loaded data
        """
        query = f"SELECT * FROM {table_name}"
        conditions = []
        
        if start_date:
            conditions.append(f"timestamp >= '{start_date}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date}'")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY timestamp DESC"
        
        logger.info(f"Loading data from {table_name}...")
        df = pd.read_sql(query, conn)
        logger.info(f"Loaded {len(df)} records")
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean raw data by removing duplicates, invalid values, and outliers.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Starting data cleaning...")
        initial_rows = len(df)
        
        # Create a copy to avoid modifying original
        df_clean = df.copy()
        
        # Convert timestamp to datetime if not already
        if 'timestamp' in df_clean.columns:
            df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
        
        # Remove duplicates based on timestamp and location
        df_clean = df_clean.drop_duplicates(subset=['timestamp', 'location'], keep='first')
        logger.info(f"Removed {initial_rows - len(df_clean)} duplicate records")
        
        # Remove records with invalid coordinates
        if 'latitude' in df_clean.columns and 'longitude' in df_clean.columns:
            before = len(df_clean)
            df_clean = df_clean[
                (df_clean['latitude'].between(-90, 90)) & 
                (df_clean['longitude'].between(-180, 180))
            ]
            logger.info(f"Removed {before - len(df_clean)} records with invalid coordinates")
        
        # Remove records with negative AQI or traffic values
        if 'aqi_value' in df_clean.columns:
            before = len(df_clean)
            df_clean = df_clean[df_clean['aqi_value'] >= 0]
            logger.info(f"Removed {before - len(df_clean)} records with negative AQI")
        
        if 'traffic_level' in df_clean.columns:
            before = len(df_clean)
            df_clean = df_clean[df_clean['traffic_level'].between(1, 5)]
            logger.info(f"Removed {before - len(df_clean)} records with invalid traffic level")
        
        # Remove extreme outliers using IQR method
        df_clean = self._remove_outliers(df_clean, columns=['aqi_value'])
        
        logger.info(f"Data cleaning complete. Final records: {len(df_clean)}")
        return df_clean
    
    def _remove_outliers(self, df: pd.DataFrame, columns: List[str], 
                        threshold: float = 3.0) -> pd.DataFrame:
        """
        Remove outliers using IQR method.
        
        Args:
            df: DataFrame
            columns: Columns to check for outliers
            threshold: IQR multiplier threshold
            
        Returns:
            DataFrame with outliers removed
        """
        df_clean = df.copy()
        
        for col in columns:
            if col not in df_clean.columns:
                continue
                
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            before = len(df_clean)
            df_clean = df_clean[
                (df_clean[col] >= lower_bound) & 
                (df_clean[col] <= upper_bound)
            ]
            removed = before - len(df_clean)
            
            if removed > 0:
                logger.info(f"Removed {removed} outliers from {col}")
        
        return df_clean
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create new features from existing data.
        
        Features created:
        - Temporal features (hour, day_of_week, month, is_weekend, is_rush_hour)
        - Lag features (previous hour values)
        - Rolling statistics (moving averages)
        - Interaction features
        
        Args:
            df: DataFrame with cleaned data
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Engineering features...")
        df_feat = df.copy()
        
        # Ensure timestamp is datetime
        df_feat['timestamp'] = pd.to_datetime(df_feat['timestamp'])
        
        # Temporal features
        df_feat['hour'] = df_feat['timestamp'].dt.hour
        df_feat['day_of_week'] = df_feat['timestamp'].dt.dayofweek
        df_feat['month'] = df_feat['timestamp'].dt.month
        df_feat['day_of_month'] = df_feat['timestamp'].dt.day
        df_feat['is_weekend'] = (df_feat['day_of_week'] >= 5).astype(int)
        
        # Rush hour indicator (7-9 AM and 5-7 PM)
        df_feat['is_rush_hour'] = (
            ((df_feat['hour'] >= 7) & (df_feat['hour'] <= 9)) |
            ((df_feat['hour'] >= 17) & (df_feat['hour'] <= 19))
        ).astype(int)
        
        # Time of day categories
        df_feat['time_of_day'] = pd.cut(
            df_feat['hour'],
            bins=[0, 6, 12, 18, 24],
            labels=['night', 'morning', 'afternoon', 'evening'],
            include_lowest=True
        )
        
        # Sort by location and timestamp for lag features
        df_feat = df_feat.sort_values(['location', 'timestamp'])
        
        # Lag features (previous values)
        for col in ['aqi_value', 'traffic_level']:
            if col in df_feat.columns:
                df_feat[f'{col}_lag_1h'] = df_feat.groupby('location')[col].shift(1)
                df_feat[f'{col}_lag_2h'] = df_feat.groupby('location')[col].shift(2)
                df_feat[f'{col}_lag_24h'] = df_feat.groupby('location')[col].shift(24)
        
        # Rolling statistics (moving averages)
        for col in ['aqi_value', 'traffic_level']:
            if col in df_feat.columns:
                # 3-hour moving average
                df_feat[f'{col}_ma_3h'] = df_feat.groupby('location')[col].transform(
                    lambda x: x.rolling(window=3, min_periods=1).mean()
                )
                # 6-hour moving average
                df_feat[f'{col}_ma_6h'] = df_feat.groupby('location')[col].transform(
                    lambda x: x.rolling(window=6, min_periods=1).mean()
                )
                # 24-hour moving average
                df_feat[f'{col}_ma_24h'] = df_feat.groupby('location')[col].transform(
                    lambda x: x.rolling(window=24, min_periods=1).mean()
                )
        
        # Interaction features
        if 'aqi_value' in df_feat.columns and 'traffic_level' in df_feat.columns:
            df_feat['aqi_traffic_interaction'] = df_feat['aqi_value'] * df_feat['traffic_level']
        
        # AQI category
        if 'aqi_value' in df_feat.columns:
            df_feat['aqi_category'] = pd.cut(
                df_feat['aqi_value'],
                bins=[0, 50, 100, 150, 200, 300, 500],
                labels=['Good', 'Moderate', 'Unhealthy_Sensitive', 'Unhealthy', 'Very_Unhealthy', 'Hazardous']
            )
        
        logger.info(f"Feature engineering complete. Total features: {len(df_feat.columns)}")
        return df_feat
    
    def handle_missing_values(self, df: pd.DataFrame, 
                             strategy: str = 'interpolate') -> pd.DataFrame:
        """
        Handle missing values using various strategies.
        
        Args:
            df: DataFrame with potential missing values
            strategy: Strategy to use ('interpolate', 'mean', 'median', 'forward_fill')
            
        Returns:
            DataFrame with missing values handled
        """
        logger.info(f"Handling missing values using {strategy} strategy...")
        df_filled = df.copy()
        
        # Log missing values before handling
        missing_counts = df_filled.isnull().sum()
        if missing_counts.sum() > 0:
            logger.info(f"Missing values found:\n{missing_counts[missing_counts > 0]}")
        
        numeric_cols = df_filled.select_dtypes(include=[np.number]).columns
        
        if strategy == 'interpolate':
            # Time-based interpolation for numeric columns
            for col in numeric_cols:
                df_filled[col] = df_filled.groupby('location')[col].transform(
                    lambda x: x.interpolate(method='time', limit_direction='both')
                )
        elif strategy == 'mean':
            df_filled[numeric_cols] = df_filled.groupby('location')[numeric_cols].transform(
                lambda x: x.fillna(x.mean())
            )
        elif strategy == 'median':
            df_filled[numeric_cols] = df_filled.groupby('location')[numeric_cols].transform(
                lambda x: x.fillna(x.median())
            )
        elif strategy == 'forward_fill':
            df_filled[numeric_cols] = df_filled.groupby('location')[numeric_cols].fillna(method='ffill')
        
        # Fill any remaining NaN with 0 or appropriate default
        df_filled = df_filled.fillna(0)
        
        logger.info("Missing value handling complete")
        return df_filled
    
    def normalize_features(self, df: pd.DataFrame, 
                          features: List[str],
                          method: str = 'standard') -> pd.DataFrame:
        """
        Normalize/scale features.
        
        Args:
            df: DataFrame
            features: List of features to normalize
            method: 'standard' for StandardScaler or 'minmax' for MinMaxScaler
            
        Returns:
            DataFrame with normalized features
        """
        logger.info(f"Normalizing features using {method} scaling...")
        df_norm = df.copy()
        
        scaler = self.scaler if method == 'standard' else self.minmax_scaler
        
        # Only normalize existing features
        features_to_scale = [f for f in features if f in df_norm.columns]
        
        if features_to_scale:
            df_norm[features_to_scale] = scaler.fit_transform(df_norm[features_to_scale])
            logger.info(f"Normalized {len(features_to_scale)} features")
        
        return df_norm
    
    def create_train_test_split(self, df: pd.DataFrame, 
                               test_size: float = 0.2,
                               time_based: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into training and testing sets.
        
        Args:
            df: DataFrame to split
            test_size: Proportion of data for testing
            time_based: If True, use chronological split; if False, use random split
            
        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"Splitting data (test_size={test_size}, time_based={time_based})...")
        
        if time_based:
            # Chronological split
            df_sorted = df.sort_values('timestamp')
            split_idx = int(len(df_sorted) * (1 - test_size))
            train_df = df_sorted.iloc[:split_idx]
            test_df = df_sorted.iloc[split_idx:]
        else:
            # Random split
            test_df = df.sample(frac=test_size, random_state=42)
            train_df = df.drop(test_df.index)
        
        logger.info(f"Train set: {len(train_df)} records, Test set: {len(test_df)} records")
        return train_df, test_df
    
    def get_preprocessing_summary(self, df_original: pd.DataFrame, 
                                 df_processed: pd.DataFrame) -> Dict:
        """
        Generate summary statistics of preprocessing.
        
        Args:
            df_original: Original DataFrame
            df_processed: Processed DataFrame
            
        Returns:
            Dictionary with preprocessing statistics
        """
        summary = {
            'original_records': len(df_original),
            'processed_records': len(df_processed),
            'records_removed': len(df_original) - len(df_processed),
            'removal_percentage': ((len(df_original) - len(df_processed)) / len(df_original) * 100),
            'original_features': len(df_original.columns),
            'processed_features': len(df_processed.columns),
            'new_features': len(df_processed.columns) - len(df_original.columns),
            'missing_values_original': df_original.isnull().sum().sum(),
            'missing_values_processed': df_processed.isnull().sum().sum(),
            'date_range': {
                'start': df_processed['timestamp'].min(),
                'end': df_processed['timestamp'].max()
            },
            'locations': df_processed['location'].nunique() if 'location' in df_processed.columns else 0
        }
        
        return summary
    
    def preprocess_pipeline(self, df: pd.DataFrame, 
                           include_feature_engineering: bool = True,
                           normalize: bool = False) -> pd.DataFrame:
        """
        Complete preprocessing pipeline.
        
        Args:
            df: Raw DataFrame
            include_feature_engineering: Whether to engineer features
            normalize: Whether to normalize numeric features
            
        Returns:
            Fully preprocessed DataFrame
        """
        logger.info("Starting complete preprocessing pipeline...")
        
        # Step 1: Clean data
        df_clean = self.clean_data(df)
        
        # Step 2: Handle missing values
        df_filled = self.handle_missing_values(df_clean, strategy='interpolate')
        
        # Step 3: Engineer features (optional)
        if include_feature_engineering:
            df_feat = self.engineer_features(df_filled)
        else:
            df_feat = df_filled
        
        # Step 4: Normalize (optional)
        if normalize:
            numeric_features = df_feat.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude ID and timestamp-related columns
            exclude_cols = ['id', 'timestamp', 'latitude', 'longitude']
            numeric_features = [f for f in numeric_features if f not in exclude_cols]
            df_final = self.normalize_features(df_feat, numeric_features, method='standard')
        else:
            df_final = df_feat
        
        logger.info("Preprocessing pipeline complete!")
        return df_final


def main():
    """Example usage of DataPreprocessor."""
    from .database import Database
    
    # Initialize
    db = Database()
    preprocessor = DataPreprocessor()
    
    # Load data
    with db.get_connection() as conn:
        df_raw = preprocessor.load_data_from_db(conn, 'raw_data')
    
    # Preprocess
    df_processed = preprocessor.preprocess_pipeline(
        df_raw, 
        include_feature_engineering=True,
        normalize=False
    )
    
    # Get summary
    summary = preprocessor.get_preprocessing_summary(df_raw, df_processed)
    print("\n=== Preprocessing Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Save processed data
    with db.get_connection() as conn:
        df_processed.to_sql('processed_data', conn, if_exists='replace', index=False)
        print("\nProcessed data saved to 'processed_data' table")


if __name__ == "__main__":
    main()
