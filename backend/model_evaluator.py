"""
Model Evaluator - Compare and rank forecasting models
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd


class ModelEvaluator:
    """Evaluate and compare forecasting models"""

    def __init__(self):
        self.evaluation_weights = {
            "mae": 0.35,      # Mean Absolute Error (lower is better)
            "rmse": 0.25,     # Root Mean Squared Error (lower is better)
            "mape": 0.25,     # Mean Absolute Percentage Error (lower is better)
            "r2": 0.15        # R-squared (higher is better)
        }

    def evaluate_model(self, model_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single model's performance

        Args:
            model_results: Dictionary with model execution results

        Returns:
            Enhanced results with evaluation score
        """
        if not model_results.get("success"):
            return {
                **model_results,
                "evaluation_score": 0,
                "rank": None
            }

        metrics = model_results["results"]["metrics"]

        # Calculate normalized score (0-100)
        score = self._calculate_score(metrics)

        return {
            **model_results,
            "evaluation_score": score,
            "metrics": metrics
        }

    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate a composite score for model comparison

        Lower MAE, RMSE, MAPE are better (so we invert them)
        Higher R2 is better

        Returns score between 0-100
        """
        # Normalize metrics to 0-100 scale
        # For error metrics (MAE, RMSE, MAPE), lower is better
        # For R2, higher is better (already 0-1, so multiply by 100)

        mae = metrics.get("mae", float('inf'))
        rmse = metrics.get("rmse", float('inf'))
        mape = metrics.get("mape", float('inf'))
        r2 = metrics.get("r2", 0)

        # Avoid division by zero
        if mae == 0:
            mae = 0.01
        if rmse == 0:
            rmse = 0.01
        if mape == 0:
            mape = 0.01

        # For error metrics, we use inverse for scoring
        # Lower error = higher score
        mae_score = (1 / mae) * 100
        rmse_score = (1 / rmse) * 100
        mape_score = (1 / mape) * 100

        # R2 is already 0-1, convert to 0-100
        r2_score = max(0, r2) * 100

        # Weighted composite score
        composite_score = (
            mae_score * self.evaluation_weights["mae"] +
            rmse_score * self.evaluation_weights["rmse"] +
            mape_score * self.evaluation_weights["mape"] +
            r2_score * self.evaluation_weights["r2"]
        )

        # Normalize to 0-100 range (scale down since inverted errors can be large)
        normalized_score = min(100, composite_score / 10)

        return round(normalized_score, 2)

    def compare_models(self, model_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compare multiple models and rank them

        Args:
            model_results: List of model execution results

        Returns:
            Sorted list with rankings and evaluation scores
        """
        evaluated = []

        for result in model_results:
            evaluated_result = self.evaluate_model(result)
            evaluated.append(evaluated_result)

        # Sort by evaluation score (descending)
        evaluated.sort(key=lambda x: x.get("evaluation_score", 0), reverse=True)

        # Add rankings
        for i, result in enumerate(evaluated):
            result["rank"] = i + 1

        return evaluated

    def get_best_model(self, model_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Get the best performing model

        Args:
            model_results: List of model execution results

        Returns:
            Best model result or None
        """
        ranked = self.compare_models(model_results)

        if not ranked:
            return None

        return ranked[0]

    def generate_comparison_report(self, model_results: List[Dict[str, Any]]) -> str:
        """
        Generate a detailed comparison report

        Args:
            model_results: List of model execution results

        Returns:
            Formatted report string
        """
        ranked = self.compare_models(model_results)

        report = []
        report.append("=" * 80)
        report.append("MODEL COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Models: {len(ranked)}")
        report.append("")

        for result in ranked:
            if not result.get("success"):
                continue

            report.append(f"Rank #{result['rank']}: {result.get('model_name', 'Unknown')}")
            report.append(f"  Score: {result['evaluation_score']:.2f}/100")
            report.append(f"  Metrics:")

            metrics = result.get("metrics", {})
            report.append(f"    - MAE:  {metrics.get('mae', 'N/A')}")
            report.append(f"    - RMSE: {metrics.get('rmse', 'N/A')}")
            report.append(f"    - MAPE: {metrics.get('mape', 'N/A')}%")
            report.append(f"    - R²:   {metrics.get('r2', 'N/A')}")

            exec_time = result.get("execution_time", 0)
            report.append(f"  Training Time: {exec_time:.2f}s")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def export_comparison_json(self, model_results: List[Dict[str, Any]], output_path: str):
        """
        Export comparison results as JSON

        Args:
            model_results: List of model results
            output_path: Path to save JSON file
        """
        ranked = self.compare_models(model_results)

        export_data = {
            "timestamp": datetime.now().isoformat(),
            "total_models": len(ranked),
            "models": []
        }

        for result in ranked:
            model_data = {
                "rank": result.get("rank"),
                "name": result.get("model_name", "Unknown"),
                "type": result.get("model_type", "Unknown"),
                "score": result.get("evaluation_score"),
                "metrics": result.get("metrics", {}),
                "execution_time": result.get("execution_time"),
                "success": result.get("success")
            }
            export_data["models"].append(model_data)

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def should_retrain(self, current_metrics: Dict[str, float],
                       previous_metrics: Dict[str, float],
                       threshold: float = 0.10) -> bool:
        """
        Determine if model should be retrained based on performance degradation

        Args:
            current_metrics: Current model metrics
            previous_metrics: Previous model metrics
            threshold: Degradation threshold (default 10%)

        Returns:
            True if retraining recommended
        """
        if not previous_metrics:
            return False

        # Compare MAE (primary metric)
        current_mae = current_metrics.get("mae", float('inf'))
        previous_mae = previous_metrics.get("mae", float('inf'))

        if previous_mae == 0:
            return True

        # Calculate percentage increase in error
        degradation = (current_mae - previous_mae) / previous_mae

        return degradation > threshold

    def get_performance_summary(self, metrics: Dict[str, float]) -> str:
        """
        Get a human-readable performance summary

        Args:
            metrics: Model metrics

        Returns:
            Performance summary string
        """
        mae = metrics.get("mae", 0)
        r2 = metrics.get("r2", 0)

        if r2 > 0.9:
            quality = "Excellent"
        elif r2 > 0.8:
            quality = "Good"
        elif r2 > 0.7:
            quality = "Fair"
        else:
            quality = "Poor"

        return f"{quality} (MAE: {mae:.2f}, R²: {r2:.4f})"


class ModelComparator:
    """Advanced model comparison utilities"""

    @staticmethod
    def compare_forecasts(forecast1: List[Dict], forecast2: List[Dict]) -> Dict[str, Any]:
        """
        Compare two forecasts

        Args:
            forecast1: First forecast
            forecast2: Second forecast

        Returns:
            Comparison statistics
        """
        if len(forecast1) != len(forecast2):
            return {"error": "Forecasts have different lengths"}

        values1 = [item["value"] for item in forecast1]
        values2 = [item["value"] for item in forecast2]

        differences = [abs(v1 - v2) for v1, v2 in zip(values1, values2)]
        mean_diff = sum(differences) / len(differences)
        max_diff = max(differences)

        return {
            "mean_difference": mean_diff,
            "max_difference": max_diff,
            "correlation": ModelComparator._calculate_correlation(values1, values2)
        }

    @staticmethod
    def _calculate_correlation(values1: List[float], values2: List[float]) -> float:
        """Calculate correlation between two series"""
        if len(values1) != len(values2) or len(values1) == 0:
            return 0.0

        mean1 = sum(values1) / len(values1)
        mean2 = sum(values2) / len(values2)

        numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))
        denominator1 = sum((v1 - mean1) ** 2 for v1 in values1) ** 0.5
        denominator2 = sum((v2 - mean2) ** 2 for v2 in values2) ** 0.5

        if denominator1 == 0 or denominator2 == 0:
            return 0.0

        return numerator / (denominator1 * denominator2)


# Example usage
if __name__ == "__main__":
    evaluator = ModelEvaluator()

    # Sample model results
    model_results = [
        {
            "success": True,
            "model_name": "ARIMA",
            "model_type": "arima",
            "results": {
                "metrics": {
                    "mae": 125.5,
                    "rmse": 156.3,
                    "mape": 5.2,
                    "r2": 0.92
                },
                "forecast": []
            },
            "execution_time": 2.5
        },
        {
            "success": True,
            "model_name": "Prophet",
            "model_type": "prophet",
            "results": {
                "metrics": {
                    "mae": 110.2,
                    "rmse": 145.1,
                    "mape": 4.8,
                    "r2": 0.94
                },
                "forecast": []
            },
            "execution_time": 3.1
        },
        {
            "success": True,
            "model_name": "LSTM",
            "model_type": "lstm",
            "results": {
                "metrics": {
                    "mae": 95.3,
                    "rmse": 132.7,
                    "mape": 4.1,
                    "r2": 0.96
                },
                "forecast": []
            },
            "execution_time": 45.2
        }
    ]

    # Compare models
    print(evaluator.generate_comparison_report(model_results))

    # Get best model
    best = evaluator.get_best_model(model_results)
    print(f"\nBest Model: {best['model_name']} (Score: {best['evaluation_score']:.2f})")
