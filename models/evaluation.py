"""
Model Evaluation and Performance Metrics Module

This module provides comprehensive model evaluation including:
- Regression metrics (RMSE, MAE, R², MAPE)
- Classification metrics (Accuracy, Precision, Recall, F1)
- Cross-validation
- Learning curves
- Residual analysis
- Feature importance analysis
- Model comparison
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
from sklearn.model_selection import cross_val_score, learning_curve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Comprehensive model evaluation and performance analysis."""
    
    def __init__(self, model_name: str = "Model"):
        self.model_name = model_name
        self.evaluation_results = {}
        
    def evaluate_regression(self, y_true: np.ndarray, y_pred: np.ndarray,
                           dataset_name: str = 'test') -> Dict[str, float]:
        """
        Evaluate regression model performance.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            dataset_name: Name of dataset (train/val/test)
            
        Returns:
            Dictionary with regression metrics
        """
        logger.info(f"Evaluating regression model on {dataset_name} set...")
        
        # Basic metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # MAPE (Mean Absolute Percentage Error)
        # Avoid division by zero
        mask = y_true != 0
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.sum() > 0 else 0
        
        # Additional metrics
        residuals = y_true - y_pred
        
        metrics = {
            f'{dataset_name}_mse': float(mse),
            f'{dataset_name}_rmse': float(rmse),
            f'{dataset_name}_mae': float(mae),
            f'{dataset_name}_r2': float(r2),
            f'{dataset_name}_mape': float(mape),
            f'{dataset_name}_residual_mean': float(np.mean(residuals)),
            f'{dataset_name}_residual_std': float(np.std(residuals)),
            f'{dataset_name}_residual_min': float(np.min(residuals)),
            f'{dataset_name}_residual_max': float(np.max(residuals))
        }
        
        # Adjusted R²
        n = len(y_true)
        p = 1  # Assuming simple model, adjust if needed
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)
        metrics[f'{dataset_name}_adj_r2'] = float(adj_r2)
        
        logger.info(f"{dataset_name.capitalize()} - RMSE: {rmse:.4f}, R²: {r2:.4f}, MAE: {mae:.4f}")
        
        return metrics
    
    def evaluate_classification(self, y_true: np.ndarray, y_pred: np.ndarray,
                               y_pred_proba: Optional[np.ndarray] = None,
                               dataset_name: str = 'test') -> Dict[str, Any]:
        """
        Evaluate classification model performance.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities (optional)
            dataset_name: Name of dataset
            
        Returns:
            Dictionary with classification metrics
        """
        logger.info(f"Evaluating classification model on {dataset_name} set...")
        
        # Basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        metrics = {
            f'{dataset_name}_accuracy': float(accuracy),
            f'{dataset_name}_precision': float(precision),
            f'{dataset_name}_recall': float(recall),
            f'{dataset_name}_f1': float(f1)
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics[f'{dataset_name}_confusion_matrix'] = cm.tolist()
        
        # Classification report
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        metrics[f'{dataset_name}_classification_report'] = report
        
        # ROC AUC if probabilities provided
        if y_pred_proba is not None:
            try:
                # For multi-class, use ovr (one-vs-rest)
                auc = roc_auc_score(y_true, y_pred_proba, multi_class='ovr', average='weighted')
                metrics[f'{dataset_name}_roc_auc'] = float(auc)
            except Exception as e:
                logger.warning(f"Could not calculate ROC AUC: {e}")
        
        logger.info(f"{dataset_name.capitalize()} - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        
        return metrics
    
    def cross_validate_model(self, model, X: pd.DataFrame, y: pd.Series,
                            cv: int = 5, scoring: str = 'neg_mean_squared_error') -> Dict[str, Any]:
        """
        Perform cross-validation.
        
        Args:
            model: Model to evaluate
            X: Features
            y: Target
            cv: Number of folds
            scoring: Scoring metric
            
        Returns:
            Dictionary with CV results
        """
        logger.info(f"Performing {cv}-fold cross-validation...")
        
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)
        
        # Convert negative scores back to positive for MSE
        if 'neg_' in scoring:
            scores = -scores
        
        cv_results = {
            'cv_scores': scores.tolist(),
            'cv_mean': float(np.mean(scores)),
            'cv_std': float(np.std(scores)),
            'cv_min': float(np.min(scores)),
            'cv_max': float(np.max(scores)),
            'cv_folds': cv,
            'scoring': scoring
        }
        
        logger.info(f"CV Mean: {cv_results['cv_mean']:.4f} ± {cv_results['cv_std']:.4f}")
        
        return cv_results
    
    def analyze_residuals(self, y_true: np.ndarray, y_pred: np.ndarray,
                         save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze residuals for regression models.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            save_path: Path to save residual plots
            
        Returns:
            Dictionary with residual analysis
        """
        logger.info("Analyzing residuals...")
        
        residuals = y_true - y_pred
        
        analysis = {
            'mean': float(np.mean(residuals)),
            'std': float(np.std(residuals)),
            'min': float(np.min(residuals)),
            'max': float(np.max(residuals)),
            'median': float(np.median(residuals)),
            'q25': float(np.percentile(residuals, 25)),
            'q75': float(np.percentile(residuals, 75))
        }
        
        # Test for normality (simple check)
        # Skewness and kurtosis
        from scipy import stats
        analysis['skewness'] = float(stats.skew(residuals))
        analysis['kurtosis'] = float(stats.kurtosis(residuals))
        
        # Shapiro-Wilk test for normality (if sample size is reasonable)
        if len(residuals) < 5000:
            stat, p_value = stats.shapiro(residuals)
            analysis['normality_test'] = {
                'statistic': float(stat),
                'p_value': float(p_value),
                'is_normal': p_value > 0.05
            }
        
        # Create residual plots
        if save_path:
            self._plot_residuals(y_true, y_pred, residuals, save_path)
        
        logger.info("Residual analysis complete")
        return analysis
    
    def _plot_residuals(self, y_true: np.ndarray, y_pred: np.ndarray,
                       residuals: np.ndarray, save_path: str):
        """Create and save residual plots."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Residuals vs Predicted
        axes[0, 0].scatter(y_pred, residuals, alpha=0.5)
        axes[0, 0].axhline(y=0, color='r', linestyle='--')
        axes[0, 0].set_xlabel('Predicted Values')
        axes[0, 0].set_ylabel('Residuals')
        axes[0, 0].set_title('Residuals vs Predicted')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Histogram of residuals
        axes[0, 1].hist(residuals, bins=50, edgecolor='black', alpha=0.7)
        axes[0, 1].set_xlabel('Residuals')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Distribution of Residuals')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Q-Q plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title('Q-Q Plot')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Actual vs Predicted
        axes[1, 1].scatter(y_true, y_pred, alpha=0.5)
        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        axes[1, 1].plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
        axes[1, 1].set_xlabel('Actual Values')
        axes[1, 1].set_ylabel('Predicted Values')
        axes[1, 1].set_title('Actual vs Predicted')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Residual plots saved to {save_path}")
    
    def plot_learning_curves(self, model, X: pd.DataFrame, y: pd.Series,
                            save_path: str, cv: int = 5):
        """
        Plot learning curves to diagnose bias/variance.
        
        Args:
            model: Model to evaluate
            X: Features
            y: Target
            save_path: Path to save plot
            cv: Number of CV folds
        """
        logger.info("Generating learning curves...")
        
        train_sizes, train_scores, val_scores = learning_curve(
            model, X, y, cv=cv, n_jobs=-1,
            train_sizes=np.linspace(0.1, 1.0, 10),
            scoring='neg_mean_squared_error'
        )
        
        # Convert to positive scores
        train_scores = -train_scores
        val_scores = -val_scores
        
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        plt.figure(figsize=(10, 6))
        plt.plot(train_sizes, train_mean, label='Training score', color='blue', marker='o')
        plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.15, color='blue')
        plt.plot(train_sizes, val_mean, label='Validation score', color='red', marker='s')
        plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.15, color='red')
        
        plt.xlabel('Training Set Size')
        plt.ylabel('MSE')
        plt.title(f'Learning Curves - {self.model_name}')
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Learning curves saved to {save_path}")
    
    def plot_feature_importance(self, feature_importance: pd.DataFrame,
                               save_path: str, top_n: int = 20):
        """
        Plot feature importance.
        
        Args:
            feature_importance: DataFrame with 'feature' and 'importance' columns
            save_path: Path to save plot
            top_n: Number of top features to show
        """
        logger.info("Plotting feature importance...")
        
        # Get top N features
        top_features = feature_importance.head(top_n)
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.title(f'Top {top_n} Feature Importances - {self.model_name}')
        plt.gca().invert_yaxis()
        plt.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Feature importance plot saved to {save_path}")
    
    def plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray,
                             save_path: str, labels: Optional[List[str]] = None):
        """
        Plot confusion matrix.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            save_path: Path to save plot
            labels: Class labels
        """
        logger.info("Plotting confusion matrix...")
        
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=labels, yticklabels=labels)
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title(f'Confusion Matrix - {self.model_name}')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Confusion matrix saved to {save_path}")
    
    def compare_models(self, results: Dict[str, Dict[str, float]],
                      metric: str = 'test_rmse',
                      save_path: Optional[str] = None) -> pd.DataFrame:
        """
        Compare multiple models.
        
        Args:
            results: Dictionary of model_name -> metrics
            metric: Metric to compare
            save_path: Path to save comparison plot
            
        Returns:
            DataFrame with comparison
        """
        logger.info(f"Comparing models on {metric}...")
        
        comparison = []
        for model_name, metrics in results.items():
            if metric in metrics:
                comparison.append({
                    'model': model_name,
                    'metric': metric,
                    'value': metrics[metric]
                })
        
        df_comparison = pd.DataFrame(comparison)
        df_comparison = df_comparison.sort_values('value')
        
        if save_path:
            plt.figure(figsize=(10, 6))
            plt.barh(df_comparison['model'], df_comparison['value'])
            plt.xlabel(metric)
            plt.ylabel('Model')
            plt.title(f'Model Comparison - {metric}')
            plt.grid(True, alpha=0.3, axis='x')
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Model comparison plot saved to {save_path}")
        
        return df_comparison
    
    def generate_evaluation_report(self, metrics: Dict[str, Any],
                                   model_type: str = 'regression') -> str:
        """
        Generate a text report of evaluation results.
        
        Args:
            metrics: Dictionary with evaluation metrics
            model_type: Type of model ('regression' or 'classification')
            
        Returns:
            Text report
        """
        report = []
        report.append("=" * 80)
        report.append(f"MODEL EVALUATION REPORT - {self.model_name}")
        report.append("=" * 80)
        report.append("")
        
        if model_type == 'regression':
            report.append("REGRESSION METRICS")
            report.append("-" * 80)
            
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and not key.endswith('_matrix'):
                    report.append(f"{key}: {value:.4f}")
        
        elif model_type == 'classification':
            report.append("CLASSIFICATION METRICS")
            report.append("-" * 80)
            
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    report.append(f"{key}: {value:.4f}")
        
        report.append("")
        report.append("=" * 80)
        report.append("End of Report")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_evaluation_results(self, filepath: str):
        """Save evaluation results to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.evaluation_results, f, indent=2, default=str)
        
        logger.info(f"Evaluation results saved to {filepath}")


class PerformanceMonitor:
    """Monitor model performance over time."""
    
    def __init__(self):
        self.performance_history = []
    
    def log_performance(self, timestamp: datetime, metrics: Dict[str, float],
                       metadata: Optional[Dict[str, Any]] = None):
        """
        Log performance metrics.
        
        Args:
            timestamp: Timestamp of evaluation
            metrics: Performance metrics
            metadata: Additional metadata
        """
        entry = {
            'timestamp': timestamp.isoformat(),
            'metrics': metrics,
            'metadata': metadata or {}
        }
        
        self.performance_history.append(entry)
        logger.info(f"Logged performance at {timestamp}")
    
    def get_performance_trend(self, metric: str) -> pd.DataFrame:
        """
        Get trend for a specific metric.
        
        Args:
            metric: Metric name
            
        Returns:
            DataFrame with timestamp and metric values
        """
        data = []
        for entry in self.performance_history:
            if metric in entry['metrics']:
                data.append({
                    'timestamp': entry['timestamp'],
                    metric: entry['metrics'][metric]
                })
        
        return pd.DataFrame(data)
    
    def plot_performance_trend(self, metric: str, save_path: str):
        """
        Plot performance trend over time.
        
        Args:
            metric: Metric to plot
            save_path: Path to save plot
        """
        df = self.get_performance_trend(metric)
        
        if df.empty:
            logger.warning(f"No data for metric: {metric}")
            return
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df[metric], marker='o', linestyle='-')
        plt.xlabel('Timestamp')
        plt.ylabel(metric)
        plt.title(f'Performance Trend - {metric}')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Performance trend plot saved to {save_path}")
    
    def save_history(self, filepath: str):
        """Save performance history to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.performance_history, f, indent=2, default=str)
        
        logger.info(f"Performance history saved to {filepath}")


def main():
    """Example usage of ModelEvaluator."""
    # This would typically be called after training models
    logger.info("Model evaluation module loaded successfully")
    logger.info("Use ModelEvaluator class to evaluate your trained models")


if __name__ == "__main__":
    main()
