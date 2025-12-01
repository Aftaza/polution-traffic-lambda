"""
Complete Analysis Pipeline for Jakarta Traffic & Pollution Data

This script orchestrates the complete analysis workflow:
1. Data preprocessing
2. Descriptive analytics
3. Model training (AQI and Traffic prediction)
4. Model evaluation
5. Results export

Usage:
    python analysis_pipeline.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

# Add models directory to path
sys.path.append(os.path.dirname(__file__))

from models.database import Database
from models.preprocessing import DataPreprocessor
from models.analytics import DescriptiveAnalytics
from models.predictive_model import AQIPredictionModel, TrafficPredictionModel
from models.evaluation import ModelEvaluator, PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Complete analysis pipeline orchestrator."""
    
    def __init__(self, output_dir: str = 'analysis_results'):
        """
        Initialize analysis pipeline.
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = output_dir
        self.results = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'plots'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'models'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'reports'), exist_ok=True)
        
        logger.info(f"Analysis pipeline initialized. Output directory: {output_dir}")
    
    def run_complete_analysis(self, days_back: int = 30):
        """
        Run complete analysis pipeline.
        
        Args:
            days_back: Number of days of data to analyze
        """
        logger.info("=" * 80)
        logger.info("STARTING COMPLETE ANALYSIS PIPELINE")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Load and preprocess data
            logger.info("\n[STEP 1/5] Loading and preprocessing data...")
            df_processed = self._step1_preprocess_data(days_back)
            self.results['preprocessing'] = {
                'total_records': len(df_processed),
                'features': list(df_processed.columns),
                'date_range': {
                    'start': df_processed['timestamp'].min().isoformat(),
                    'end': df_processed['timestamp'].max().isoformat()
                }
            }
            
            # Step 2: Descriptive analytics
            logger.info("\n[STEP 2/5] Performing descriptive analytics...")
            insights = self._step2_descriptive_analytics(df_processed)
            self.results['analytics'] = insights
            
            # Step 3: Train prediction models
            logger.info("\n[STEP 3/5] Training prediction models...")
            models_results = self._step3_train_models(df_processed)
            self.results['models'] = models_results
            
            # Step 4: Evaluate models
            logger.info("\n[STEP 4/5] Evaluating model performance...")
            evaluation_results = self._step4_evaluate_models(df_processed, models_results)
            self.results['evaluation'] = evaluation_results
            
            # Step 5: Generate reports
            logger.info("\n[STEP 5/5] Generating reports...")
            self._step5_generate_reports()
            
            # Save complete results
            self._save_complete_results()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info(f"ANALYSIS PIPELINE COMPLETED SUCCESSFULLY in {duration:.2f}s")
            logger.info(f"Results saved to: {self.output_dir}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
    
    def _step1_preprocess_data(self, days_back: int) -> pd.DataFrame:
        """Step 1: Load and preprocess data."""
        db = Database()
        preprocessor = DataPreprocessor()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Load data
        with db.get_connection() as conn:
            df_raw = preprocessor.load_data_from_db(
                conn, 
                'raw_data',
                start_date=start_date,
                end_date=end_date
            )
        
        logger.info(f"Loaded {len(df_raw)} raw records")
        
        # Preprocess
        df_processed = preprocessor.preprocess_pipeline(
            df_raw,
            include_feature_engineering=True,
            normalize=False
        )
        
        # Get preprocessing summary
        summary = preprocessor.get_preprocessing_summary(df_raw, df_processed)
        
        # Save processed data
        processed_path = os.path.join(self.output_dir, 'processed_data.csv')
        df_processed.to_csv(processed_path, index=False)
        logger.info(f"Processed data saved to {processed_path}")
        
        # Save preprocessing summary
        summary_path = os.path.join(self.output_dir, 'reports', 'preprocessing_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return df_processed
    
    def _step2_descriptive_analytics(self, df: pd.DataFrame) -> Dict:
        """Step 2: Perform descriptive analytics."""
        analytics = DescriptiveAnalytics()
        
        # Generate insights
        insights = analytics.generate_insights(df)
        
        # Save insights
        insights_path = os.path.join(self.output_dir, 'reports', 'analytics_insights.json')
        analytics.save_insights(insights_path)
        
        # Generate and save text report
        report = analytics.generate_report()
        report_path = os.path.join(self.output_dir, 'reports', 'analytics_report.txt')
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Analytics report saved to {report_path}")
        
        return insights
    
    def _step3_train_models(self, df: pd.DataFrame) -> Dict:
        """Step 3: Train prediction models."""
        preprocessor = DataPreprocessor()
        
        # Split data
        train_df, test_df = preprocessor.create_train_test_split(
            df, 
            test_size=0.2,
            time_based=True
        )
        
        models_results = {}
        
        # Train AQI prediction model
        logger.info("Training AQI prediction model...")
        aqi_model = AQIPredictionModel(model_type='random_forest')
        X_train, y_train = aqi_model.prepare_features(train_df, 'aqi_value')
        X_test, y_test = aqi_model.prepare_features(test_df, 'aqi_value')
        
        # Split train into train/val
        val_size = int(len(X_train) * 0.2)
        X_val = X_train.iloc[-val_size:]
        y_val = y_train.iloc[-val_size:]
        X_train = X_train.iloc[:-val_size]
        y_train = y_train.iloc[:-val_size]
        
        aqi_history = aqi_model.train(X_train, y_train, X_val, y_val)
        
        # Save AQI model
        aqi_model_path = os.path.join(self.output_dir, 'models', 'aqi_model.pkl')
        aqi_model.save_model(aqi_model_path)
        
        models_results['aqi_model'] = {
            'model_path': aqi_model_path,
            'training_history': aqi_history,
            'feature_importance': aqi_model.feature_importance.to_dict() if aqi_model.feature_importance is not None else None
        }
        
        # Train Traffic prediction model
        logger.info("Training Traffic prediction model...")
        traffic_model = TrafficPredictionModel(model_type='random_forest')
        X_train, y_train = traffic_model.prepare_features(train_df, 'traffic_level')
        X_test, y_test = traffic_model.prepare_features(test_df, 'traffic_level')
        
        # Split train into train/val
        val_size = int(len(X_train) * 0.2)
        X_val = X_train.iloc[-val_size:]
        y_val = y_train.iloc[-val_size:]
        X_train = X_train.iloc[:-val_size]
        y_train = y_train.iloc[:-val_size]
        
        traffic_history = traffic_model.train(X_train, y_train, X_val, y_val)
        
        # Save Traffic model
        traffic_model_path = os.path.join(self.output_dir, 'models', 'traffic_model.pkl')
        traffic_model.save_model(traffic_model_path)
        
        models_results['traffic_model'] = {
            'model_path': traffic_model_path,
            'training_history': traffic_history,
            'feature_importance': traffic_model.feature_importance.to_dict() if traffic_model.feature_importance is not None else None
        }
        
        return models_results
    
    def _step4_evaluate_models(self, df: pd.DataFrame, models_results: Dict) -> Dict:
        """Step 4: Evaluate models."""
        preprocessor = DataPreprocessor()
        
        # Split data
        train_df, test_df = preprocessor.create_train_test_split(
            df, 
            test_size=0.2,
            time_based=True
        )
        
        evaluation_results = {}
        
        # Evaluate AQI model
        logger.info("Evaluating AQI model...")
        aqi_model = AQIPredictionModel()
        aqi_model.load_model(models_results['aqi_model']['model_path'])
        
        X_test, y_test = aqi_model.prepare_features(test_df, 'aqi_value')
        y_pred = aqi_model.predict(X_test)
        
        aqi_evaluator = ModelEvaluator(model_name='AQI Random Forest')
        aqi_metrics = aqi_evaluator.evaluate_regression(y_test.values, y_pred, 'test')
        
        # Residual analysis
        residual_plot_path = os.path.join(self.output_dir, 'plots', 'aqi_residuals.png')
        residual_analysis = aqi_evaluator.analyze_residuals(y_test.values, y_pred, residual_plot_path)
        
        # Feature importance plot
        if aqi_model.feature_importance is not None:
            fi_plot_path = os.path.join(self.output_dir, 'plots', 'aqi_feature_importance.png')
            aqi_evaluator.plot_feature_importance(aqi_model.feature_importance, fi_plot_path)
        
        evaluation_results['aqi_model'] = {
            'metrics': aqi_metrics,
            'residual_analysis': residual_analysis
        }
        
        # Evaluate Traffic model
        logger.info("Evaluating Traffic model...")
        traffic_model = TrafficPredictionModel()
        traffic_model.load_model(models_results['traffic_model']['model_path'])
        
        X_test, y_test = traffic_model.prepare_features(test_df, 'traffic_level')
        y_pred = traffic_model.predict(X_test)
        y_pred_proba = traffic_model.predict_proba(X_test)
        
        traffic_evaluator = ModelEvaluator(model_name='Traffic Random Forest')
        traffic_metrics = traffic_evaluator.evaluate_classification(
            y_test.values, y_pred, y_pred_proba, 'test'
        )
        
        # Confusion matrix plot
        cm_plot_path = os.path.join(self.output_dir, 'plots', 'traffic_confusion_matrix.png')
        traffic_evaluator.plot_confusion_matrix(
            y_test.values, y_pred, cm_plot_path,
            labels=['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5']
        )
        
        # Feature importance plot
        if traffic_model.feature_importance is not None:
            fi_plot_path = os.path.join(self.output_dir, 'plots', 'traffic_feature_importance.png')
            traffic_evaluator.plot_feature_importance(traffic_model.feature_importance, fi_plot_path)
        
        evaluation_results['traffic_model'] = {
            'metrics': traffic_metrics
        }
        
        # Save evaluation results
        eval_path = os.path.join(self.output_dir, 'reports', 'evaluation_results.json')
        with open(eval_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2, default=str)
        
        return evaluation_results
    
    def _step5_generate_reports(self):
        """Step 5: Generate comprehensive reports."""
        # Generate summary report
        summary_report = self._generate_summary_report()
        
        summary_path = os.path.join(self.output_dir, 'reports', 'ANALYSIS_SUMMARY.md')
        with open(summary_path, 'w') as f:
            f.write(summary_report)
        
        logger.info(f"Summary report saved to {summary_path}")
    
    def _generate_summary_report(self) -> str:
        """Generate markdown summary report."""
        report = []
        
        report.append("# Jakarta Traffic & Pollution Analysis - Summary Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Preprocessing
        if 'preprocessing' in self.results:
            prep = self.results['preprocessing']
            report.append("## 1. Data Preprocessing")
            report.append("")
            report.append(f"- **Total Records:** {prep['total_records']:,}")
            report.append(f"- **Features:** {len(prep['features'])}")
            report.append(f"- **Date Range:** {prep['date_range']['start']} to {prep['date_range']['end']}")
            report.append("")
        
        # Analytics
        if 'analytics' in self.results:
            analytics = self.results['analytics']
            report.append("## 2. Descriptive Analytics")
            report.append("")
            
            if 'summary_statistics' in analytics:
                stats = analytics['summary_statistics']
                
                if 'aqi_statistics' in stats:
                    aqi = stats['aqi_statistics']
                    report.append("### Air Quality Index (AQI)")
                    report.append("")
                    report.append(f"- **Mean AQI:** {aqi['mean']:.2f}")
                    report.append(f"- **Median AQI:** {aqi['median']:.2f}")
                    report.append(f"- **Range:** {aqi['min']:.0f} - {aqi['max']:.0f}")
                    report.append("")
                
                if 'traffic_statistics' in stats:
                    traffic = stats['traffic_statistics']
                    report.append("### Traffic Levels")
                    report.append("")
                    report.append(f"- **Mean Traffic Level:** {traffic['mean']:.2f}")
                    report.append(f"- **Median Traffic Level:** {traffic['median']:.2f}")
                    report.append("")
            
            # Key findings
            if 'key_findings' in analytics:
                report.append("### Key Findings")
                report.append("")
                for i, finding in enumerate(analytics['key_findings'], 1):
                    report.append(f"{i}. **[{finding['category']}]** {finding['finding']}")
                report.append("")
        
        # Models
        if 'models' in self.results:
            report.append("## 3. Predictive Models")
            report.append("")
            
            if 'aqi_model' in self.results['models']:
                aqi_model = self.results['models']['aqi_model']
                history = aqi_model['training_history']
                report.append("### AQI Prediction Model")
                report.append("")
                report.append(f"- **Model Type:** {history['model_type']}")
                report.append(f"- **Training Samples:** {history['train_samples']:,}")
                report.append(f"- **Training Time:** {history['training_time']:.2f}s")
                report.append("")
            
            if 'traffic_model' in self.results['models']:
                traffic_model = self.results['models']['traffic_model']
                history = traffic_model['training_history']
                report.append("### Traffic Prediction Model")
                report.append("")
                report.append(f"- **Model Type:** {history['model_type']}")
                report.append(f"- **Training Samples:** {history['train_samples']:,}")
                report.append(f"- **Training Time:** {history['training_time']:.2f}s")
                report.append("")
        
        # Evaluation
        if 'evaluation' in self.results:
            report.append("## 4. Model Performance")
            report.append("")
            
            if 'aqi_model' in self.results['evaluation']:
                aqi_eval = self.results['evaluation']['aqi_model']['metrics']
                report.append("### AQI Model Performance")
                report.append("")
                report.append(f"- **RMSE:** {aqi_eval.get('test_rmse', 0):.4f}")
                report.append(f"- **MAE:** {aqi_eval.get('test_mae', 0):.4f}")
                report.append(f"- **R² Score:** {aqi_eval.get('test_r2', 0):.4f}")
                report.append(f"- **MAPE:** {aqi_eval.get('test_mape', 0):.2f}%")
                report.append("")
            
            if 'traffic_model' in self.results['evaluation']:
                traffic_eval = self.results['evaluation']['traffic_model']['metrics']
                report.append("### Traffic Model Performance")
                report.append("")
                report.append(f"- **Accuracy:** {traffic_eval.get('test_accuracy', 0):.4f}")
                report.append(f"- **Precision:** {traffic_eval.get('test_precision', 0):.4f}")
                report.append(f"- **Recall:** {traffic_eval.get('test_recall', 0):.4f}")
                report.append(f"- **F1 Score:** {traffic_eval.get('test_f1', 0):.4f}")
                report.append("")
        
        report.append("## 5. Output Files")
        report.append("")
        report.append("- `processed_data.csv` - Preprocessed dataset")
        report.append("- `reports/analytics_insights.json` - Detailed analytics insights")
        report.append("- `reports/analytics_report.txt` - Text analytics report")
        report.append("- `reports/evaluation_results.json` - Model evaluation metrics")
        report.append("- `models/aqi_model.pkl` - Trained AQI prediction model")
        report.append("- `models/traffic_model.pkl` - Trained traffic prediction model")
        report.append("- `plots/` - Visualization plots")
        report.append("")
        
        return "\n".join(report)
    
    def _save_complete_results(self):
        """Save complete results to JSON."""
        results_path = os.path.join(self.output_dir, 'complete_results.json')
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Complete results saved to {results_path}")


def main():
    """Main entry point."""
    print("=" * 80)
    print("Jakarta Traffic & Pollution Analysis Pipeline")
    print("=" * 80)
    print()
    
    # Create pipeline
    pipeline = AnalysisPipeline(output_dir='analysis_results')
    
    # Run analysis
    try:
        pipeline.run_complete_analysis(days_back=30)
        
        print()
        print("✅ Analysis completed successfully!")
        print(f"📁 Results saved to: analysis_results/")
        print()
        print("Key outputs:")
        print("  - analysis_results/reports/ANALYSIS_SUMMARY.md")
        print("  - analysis_results/processed_data.csv")
        print("  - analysis_results/models/")
        print("  - analysis_results/plots/")
        
    except Exception as e:
        print()
        print(f"❌ Analysis failed: {e}")
        print("Check analysis_pipeline.log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
