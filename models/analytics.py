"""
Descriptive Analytics and Insights Module

This module provides comprehensive descriptive statistics and insights for
Jakarta Traffic & Pollution data, including:
- Statistical summaries
- Temporal patterns analysis
- Spatial analysis
- Correlation analysis
- Anomaly detection
- Visualization generation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DescriptiveAnalytics:
    """Comprehensive descriptive analytics for traffic and pollution data."""
    
    def __init__(self):
        self.insights = {}
        
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics.
        
        Args:
            df: DataFrame with processed data
            
        Returns:
            Dictionary with summary statistics
        """
        logger.info("Generating summary statistics...")
        
        summary = {
            'dataset_info': {
                'total_records': len(df),
                'date_range': {
                    'start': df['timestamp'].min().isoformat() if 'timestamp' in df.columns else None,
                    'end': df['timestamp'].max().isoformat() if 'timestamp' in df.columns else None,
                    'duration_days': (df['timestamp'].max() - df['timestamp'].min()).days if 'timestamp' in df.columns else None
                },
                'locations': df['location'].nunique() if 'location' in df.columns else 0,
                'location_list': df['location'].unique().tolist() if 'location' in df.columns else []
            },
            'aqi_statistics': {},
            'traffic_statistics': {},
            'missing_data': {}
        }
        
        # AQI Statistics
        if 'aqi_value' in df.columns:
            aqi_data = df['aqi_value'].dropna()
            summary['aqi_statistics'] = {
                'mean': float(aqi_data.mean()),
                'median': float(aqi_data.median()),
                'std': float(aqi_data.std()),
                'min': float(aqi_data.min()),
                'max': float(aqi_data.max()),
                'q25': float(aqi_data.quantile(0.25)),
                'q75': float(aqi_data.quantile(0.75)),
                'iqr': float(aqi_data.quantile(0.75) - aqi_data.quantile(0.25)),
                'skewness': float(aqi_data.skew()),
                'kurtosis': float(aqi_data.kurtosis())
            }
            
            # AQI Categories distribution
            aqi_categories = pd.cut(
                aqi_data,
                bins=[0, 50, 100, 150, 200, 300, 500],
                labels=['Good', 'Moderate', 'Unhealthy_Sensitive', 'Unhealthy', 'Very_Unhealthy', 'Hazardous']
            )
            summary['aqi_statistics']['category_distribution'] = aqi_categories.value_counts().to_dict()
        
        # Traffic Statistics
        if 'traffic_level' in df.columns:
            traffic_data = df['traffic_level'].dropna()
            summary['traffic_statistics'] = {
                'mean': float(traffic_data.mean()),
                'median': float(traffic_data.median()),
                'std': float(traffic_data.std()),
                'min': int(traffic_data.min()),
                'max': int(traffic_data.max()),
                'mode': int(traffic_data.mode()[0]) if len(traffic_data.mode()) > 0 else None,
                'distribution': traffic_data.value_counts().to_dict()
            }
        
        # Missing Data Analysis
        summary['missing_data'] = {
            'total_missing': int(df.isnull().sum().sum()),
            'missing_by_column': df.isnull().sum().to_dict(),
            'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict()
        }
        
        logger.info("Summary statistics generated")
        return summary
    
    def analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze temporal patterns in the data.
        
        Args:
            df: DataFrame with timestamp column
            
        Returns:
            Dictionary with temporal insights
        """
        logger.info("Analyzing temporal patterns...")
        
        if 'timestamp' not in df.columns:
            logger.warning("No timestamp column found")
            return {}
        
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        temporal_patterns = {
            'hourly_patterns': {},
            'daily_patterns': {},
            'monthly_patterns': {},
            'weekend_vs_weekday': {},
            'peak_hours': {}
        }
        
        # Hourly patterns
        if 'aqi_value' in df.columns:
            hourly_aqi = df.groupby('hour')['aqi_value'].agg(['mean', 'std', 'min', 'max'])
            temporal_patterns['hourly_patterns']['aqi'] = {
                'mean_by_hour': hourly_aqi['mean'].to_dict(),
                'std_by_hour': hourly_aqi['std'].to_dict(),
                'peak_hour': int(hourly_aqi['mean'].idxmax()),
                'peak_value': float(hourly_aqi['mean'].max()),
                'lowest_hour': int(hourly_aqi['mean'].idxmin()),
                'lowest_value': float(hourly_aqi['mean'].min())
            }
        
        if 'traffic_level' in df.columns:
            hourly_traffic = df.groupby('hour')['traffic_level'].agg(['mean', 'std', 'min', 'max'])
            temporal_patterns['hourly_patterns']['traffic'] = {
                'mean_by_hour': hourly_traffic['mean'].to_dict(),
                'std_by_hour': hourly_traffic['std'].to_dict(),
                'peak_hour': int(hourly_traffic['mean'].idxmax()),
                'peak_value': float(hourly_traffic['mean'].max()),
                'lowest_hour': int(hourly_traffic['mean'].idxmin()),
                'lowest_value': float(hourly_traffic['mean'].min())
            }
        
        # Day of week patterns
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if 'aqi_value' in df.columns:
            daily_aqi = df.groupby('day_of_week')['aqi_value'].mean()
            temporal_patterns['daily_patterns']['aqi'] = {
                day_names[i]: float(daily_aqi.get(i, 0)) for i in range(7)
            }
        
        if 'traffic_level' in df.columns:
            daily_traffic = df.groupby('day_of_week')['traffic_level'].mean()
            temporal_patterns['daily_patterns']['traffic'] = {
                day_names[i]: float(daily_traffic.get(i, 0)) for i in range(7)
            }
        
        # Monthly patterns
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if 'aqi_value' in df.columns:
            monthly_aqi = df.groupby('month')['aqi_value'].mean()
            temporal_patterns['monthly_patterns']['aqi'] = {
                month_names[i-1]: float(monthly_aqi.get(i, 0)) for i in range(1, 13) if i in monthly_aqi.index
            }
        
        # Weekend vs Weekday
        if 'aqi_value' in df.columns:
            weekend_aqi = df.groupby('is_weekend')['aqi_value'].mean()
            temporal_patterns['weekend_vs_weekday']['aqi'] = {
                'weekday': float(weekend_aqi.get(0, 0)),
                'weekend': float(weekend_aqi.get(1, 0)),
                'difference': float(weekend_aqi.get(1, 0) - weekend_aqi.get(0, 0))
            }
        
        if 'traffic_level' in df.columns:
            weekend_traffic = df.groupby('is_weekend')['traffic_level'].mean()
            temporal_patterns['weekend_vs_weekday']['traffic'] = {
                'weekday': float(weekend_traffic.get(0, 0)),
                'weekend': float(weekend_traffic.get(1, 0)),
                'difference': float(weekend_traffic.get(1, 0) - weekend_traffic.get(0, 0))
            }
        
        # Identify rush hours
        if 'traffic_level' in df.columns:
            rush_hour_threshold = df['traffic_level'].quantile(0.75)
            rush_hours = df.groupby('hour')['traffic_level'].mean()
            rush_hours = rush_hours[rush_hours >= rush_hour_threshold]
            temporal_patterns['peak_hours']['rush_hours'] = rush_hours.index.tolist()
            temporal_patterns['peak_hours']['rush_hour_threshold'] = float(rush_hour_threshold)
        
        logger.info("Temporal pattern analysis complete")
        return temporal_patterns
    
    def analyze_spatial_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze spatial patterns across locations.
        
        Args:
            df: DataFrame with location data
            
        Returns:
            Dictionary with spatial insights
        """
        logger.info("Analyzing spatial patterns...")
        
        if 'location' not in df.columns:
            logger.warning("No location column found")
            return {}
        
        spatial_patterns = {
            'location_statistics': {},
            'hotspots': {},
            'location_rankings': {}
        }
        
        # Statistics by location
        for location in df['location'].unique():
            loc_data = df[df['location'] == location]
            
            location_stats = {
                'total_records': len(loc_data),
                'coordinates': {
                    'latitude': float(loc_data['latitude'].mean()) if 'latitude' in loc_data.columns else None,
                    'longitude': float(loc_data['longitude'].mean()) if 'longitude' in loc_data.columns else None
                }
            }
            
            if 'aqi_value' in loc_data.columns:
                aqi_data = loc_data['aqi_value'].dropna()
                location_stats['aqi'] = {
                    'mean': float(aqi_data.mean()),
                    'median': float(aqi_data.median()),
                    'std': float(aqi_data.std()),
                    'min': float(aqi_data.min()),
                    'max': float(aqi_data.max())
                }
            
            if 'traffic_level' in loc_data.columns:
                traffic_data = loc_data['traffic_level'].dropna()
                location_stats['traffic'] = {
                    'mean': float(traffic_data.mean()),
                    'median': float(traffic_data.median()),
                    'std': float(traffic_data.std()),
                    'min': int(traffic_data.min()),
                    'max': int(traffic_data.max())
                }
            
            spatial_patterns['location_statistics'][location] = location_stats
        
        # Identify hotspots (highest pollution and traffic)
        if 'aqi_value' in df.columns:
            aqi_by_location = df.groupby('location')['aqi_value'].mean().sort_values(ascending=False)
            spatial_patterns['hotspots']['pollution'] = {
                'highest': aqi_by_location.head(3).to_dict(),
                'lowest': aqi_by_location.tail(3).to_dict()
            }
            
            spatial_patterns['location_rankings']['aqi'] = aqi_by_location.to_dict()
        
        if 'traffic_level' in df.columns:
            traffic_by_location = df.groupby('location')['traffic_level'].mean().sort_values(ascending=False)
            spatial_patterns['hotspots']['traffic'] = {
                'highest': traffic_by_location.head(3).to_dict(),
                'lowest': traffic_by_location.tail(3).to_dict()
            }
            
            spatial_patterns['location_rankings']['traffic'] = traffic_by_location.to_dict()
        
        logger.info("Spatial pattern analysis complete")
        return spatial_patterns
    
    def analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze correlations between variables.
        
        Args:
            df: DataFrame with numeric columns
            
        Returns:
            Dictionary with correlation insights
        """
        logger.info("Analyzing correlations...")
        
        # Select numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove ID columns
        numeric_cols = [col for col in numeric_cols if 'id' not in col.lower()]
        
        if len(numeric_cols) < 2:
            logger.warning("Not enough numeric columns for correlation analysis")
            return {}
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        correlations = {
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': {},
            'key_insights': []
        }
        
        # Find strong correlations (|r| > 0.5)
        strong_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:
                    strong_corr.append({
                        'variable1': corr_matrix.columns[i],
                        'variable2': corr_matrix.columns[j],
                        'correlation': float(corr_value),
                        'strength': 'strong' if abs(corr_value) > 0.7 else 'moderate'
                    })
        
        correlations['strong_correlations'] = strong_corr
        
        # Key insights
        if 'aqi_value' in numeric_cols and 'traffic_level' in numeric_cols:
            aqi_traffic_corr = corr_matrix.loc['aqi_value', 'traffic_level']
            correlations['key_insights'].append({
                'insight': 'AQI-Traffic Correlation',
                'value': float(aqi_traffic_corr),
                'interpretation': self._interpret_correlation(aqi_traffic_corr)
            })
        
        logger.info("Correlation analysis complete")
        return correlations
    
    def _interpret_correlation(self, corr_value: float) -> str:
        """Interpret correlation value."""
        abs_corr = abs(corr_value)
        direction = "positive" if corr_value > 0 else "negative"
        
        if abs_corr > 0.7:
            strength = "strong"
        elif abs_corr > 0.5:
            strength = "moderate"
        elif abs_corr > 0.3:
            strength = "weak"
        else:
            strength = "very weak"
        
        return f"{strength} {direction} correlation"
    
    def detect_anomalies(self, df: pd.DataFrame, 
                        columns: List[str] = None,
                        method: str = 'iqr') -> Dict[str, Any]:
        """
        Detect anomalies in the data.
        
        Args:
            df: DataFrame
            columns: Columns to check for anomalies
            method: Detection method ('iqr', 'zscore')
            
        Returns:
            Dictionary with anomaly information
        """
        logger.info(f"Detecting anomalies using {method} method...")
        
        if columns is None:
            columns = ['aqi_value', 'traffic_level']
        
        columns = [col for col in columns if col in df.columns]
        
        anomalies = {
            'method': method,
            'anomalies_by_column': {},
            'total_anomalies': 0
        }
        
        for col in columns:
            col_data = df[col].dropna()
            
            if method == 'iqr':
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                anomaly_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            
            elif method == 'zscore':
                mean = col_data.mean()
                std = col_data.std()
                z_scores = np.abs((df[col] - mean) / std)
                anomaly_mask = z_scores > 3
            
            else:
                logger.warning(f"Unknown method: {method}")
                continue
            
            num_anomalies = anomaly_mask.sum()
            anomalies['anomalies_by_column'][col] = {
                'count': int(num_anomalies),
                'percentage': float(num_anomalies / len(df) * 100),
                'indices': df[anomaly_mask].index.tolist()[:10]  # First 10 indices
            }
            
            anomalies['total_anomalies'] += num_anomalies
        
        logger.info(f"Detected {anomalies['total_anomalies']} total anomalies")
        return anomalies
    
    def generate_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive insights from all analyses.
        
        Args:
            df: DataFrame with processed data
            
        Returns:
            Dictionary with all insights
        """
        logger.info("Generating comprehensive insights...")
        
        insights = {
            'summary_statistics': self.generate_summary_statistics(df),
            'temporal_patterns': self.analyze_temporal_patterns(df),
            'spatial_patterns': self.analyze_spatial_patterns(df),
            'correlations': self.analyze_correlations(df),
            'anomalies': self.detect_anomalies(df),
            'key_findings': []
        }
        
        # Generate key findings
        key_findings = []
        
        # Finding 1: Overall air quality
        if 'aqi_statistics' in insights['summary_statistics']:
            avg_aqi = insights['summary_statistics']['aqi_statistics']['mean']
            if avg_aqi < 50:
                quality = "Good"
            elif avg_aqi < 100:
                quality = "Moderate"
            elif avg_aqi < 150:
                quality = "Unhealthy for Sensitive Groups"
            else:
                quality = "Unhealthy"
            
            key_findings.append({
                'category': 'Air Quality',
                'finding': f"Average AQI is {avg_aqi:.1f}, classified as '{quality}'",
                'severity': 'high' if avg_aqi > 100 else 'medium'
            })
        
        # Finding 2: Peak pollution hours
        if 'hourly_patterns' in insights['temporal_patterns']:
            if 'aqi' in insights['temporal_patterns']['hourly_patterns']:
                peak_hour = insights['temporal_patterns']['hourly_patterns']['aqi']['peak_hour']
                peak_value = insights['temporal_patterns']['hourly_patterns']['aqi']['peak_value']
                key_findings.append({
                    'category': 'Temporal Pattern',
                    'finding': f"Peak pollution occurs at {peak_hour}:00 with average AQI of {peak_value:.1f}",
                    'severity': 'medium'
                })
        
        # Finding 3: Most polluted location
        if 'hotspots' in insights['spatial_patterns']:
            if 'pollution' in insights['spatial_patterns']['hotspots']:
                highest = insights['spatial_patterns']['hotspots']['pollution']['highest']
                if highest:
                    top_location = list(highest.keys())[0]
                    top_value = list(highest.values())[0]
                    key_findings.append({
                        'category': 'Spatial Pattern',
                        'finding': f"'{top_location}' has the highest average AQI of {top_value:.1f}",
                        'severity': 'high'
                    })
        
        # Finding 4: Weekend vs Weekday
        if 'weekend_vs_weekday' in insights['temporal_patterns']:
            if 'aqi' in insights['temporal_patterns']['weekend_vs_weekday']:
                diff = insights['temporal_patterns']['weekend_vs_weekday']['aqi']['difference']
                if abs(diff) > 10:
                    direction = "higher" if diff > 0 else "lower"
                    key_findings.append({
                        'category': 'Temporal Pattern',
                        'finding': f"Weekend AQI is {abs(diff):.1f} points {direction} than weekdays",
                        'severity': 'medium'
                    })
        
        insights['key_findings'] = key_findings
        
        self.insights = insights
        logger.info("Comprehensive insights generated")
        
        return insights
    
    def save_insights(self, filepath: str):
        """Save insights to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.insights, f, indent=2, default=str)
        
        logger.info(f"Insights saved to {filepath}")
    
    def generate_report(self) -> str:
        """Generate a text report of insights."""
        if not self.insights:
            return "No insights available. Run generate_insights() first."
        
        report = []
        report.append("=" * 80)
        report.append("JAKARTA TRAFFIC & POLLUTION ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Dataset Info
        if 'summary_statistics' in self.insights:
            info = self.insights['summary_statistics']['dataset_info']
            report.append("DATASET INFORMATION")
            report.append("-" * 80)
            report.append(f"Total Records: {info['total_records']:,}")
            report.append(f"Date Range: {info['date_range']['start']} to {info['date_range']['end']}")
            report.append(f"Duration: {info['date_range']['duration_days']} days")
            report.append(f"Locations: {info['locations']}")
            report.append("")
        
        # Key Findings
        if 'key_findings' in self.insights:
            report.append("KEY FINDINGS")
            report.append("-" * 80)
            for i, finding in enumerate(self.insights['key_findings'], 1):
                report.append(f"{i}. [{finding['category']}] {finding['finding']}")
            report.append("")
        
        # Summary Statistics
        if 'summary_statistics' in self.insights:
            if 'aqi_statistics' in self.insights['summary_statistics']:
                aqi = self.insights['summary_statistics']['aqi_statistics']
                report.append("AIR QUALITY INDEX (AQI) STATISTICS")
                report.append("-" * 80)
                report.append(f"Mean: {aqi['mean']:.2f}")
                report.append(f"Median: {aqi['median']:.2f}")
                report.append(f"Std Dev: {aqi['std']:.2f}")
                report.append(f"Range: {aqi['min']:.0f} - {aqi['max']:.0f}")
                report.append("")
        
        report.append("=" * 80)
        report.append("End of Report")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Example usage of DescriptiveAnalytics."""
    from .database import Database
    from .preprocessing import DataPreprocessor
    
    # Initialize
    db = Database()
    preprocessor = DataPreprocessor()
    analytics = DescriptiveAnalytics()
    
    # Load and preprocess data
    with db.get_connection() as conn:
        df_raw = preprocessor.load_data_from_db(conn, 'raw_data')
    
    df_processed = preprocessor.preprocess_pipeline(df_raw, include_feature_engineering=True)
    
    # Generate insights
    insights = analytics.generate_insights(df_processed)
    
    # Save insights
    analytics.save_insights('analytics_insights.json')
    
    # Print report
    print(analytics.generate_report())


if __name__ == "__main__":
    main()
