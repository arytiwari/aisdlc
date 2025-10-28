"""
Model Executor - Safely execute generated forecasting code
"""
import subprocess
import json
import os
import sys
import time
from pathlib import Path
import tempfile


class ModelExecutor:
    """Execute generated model code safely with timeouts and error handling"""

    def __init__(self, timeout=600):
        """
        Initialize executor

        Args:
            timeout: Maximum execution time in seconds (default: 10 minutes)
        """
        self.timeout = timeout
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        (self.models_dir / "saved_models").mkdir(exist_ok=True)
        (self.models_dir / "generated_code").mkdir(exist_ok=True)

    def execute_model(self, code_path):
        """
        Execute a model script and return results

        Args:
            code_path: Path to the Python script to execute

        Returns:
            Dictionary with execution results including metrics, forecast, errors
        """
        if not os.path.exists(code_path):
            return {
                "success": False,
                "error": f"Code file not found: {code_path}"
            }

        start_time = time.time()

        try:
            # Execute the Python script
            result = subprocess.run(
                [sys.executable, code_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.path.dirname(os.path.dirname(code_path))  # Run from project root
            )

            execution_time = time.time() - start_time

            # Check for errors
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr,
                    "stdout": result.stdout,
                    "execution_time": execution_time
                }

            # Try to parse JSON output from stdout
            try:
                # Get the last JSON object in stdout (in case there are print statements)
                output_lines = result.stdout.strip().split('\n')
                json_output = None

                # Search backwards for JSON output
                for line in reversed(output_lines):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            json_output = json.loads(line)
                            break
                        except:
                            continue

                if json_output is None:
                    # Try parsing the entire stdout
                    json_output = json.loads(result.stdout)

                return {
                    "success": True,
                    "results": json_output,
                    "execution_time": execution_time,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse model output as JSON: {str(e)}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": execution_time
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Execution timeout after {self.timeout} seconds",
                "execution_time": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "execution_time": time.time() - start_time
            }

    def execute_model_with_retry(self, code_path, max_retries=2):
        """
        Execute model with retry logic

        Args:
            code_path: Path to the model code
            max_retries: Maximum number of retries

        Returns:
            Execution results
        """
        for attempt in range(max_retries + 1):
            result = self.execute_model(code_path)

            if result["success"]:
                return result

            if attempt < max_retries:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2)  # Wait before retry

        return result

    def validate_model_output(self, results):
        """
        Validate that model output has required fields

        Args:
            results: Dictionary with model results

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(results, dict):
            return False, "Results must be a dictionary"

        required_fields = ["metrics", "forecast"]

        for field in required_fields:
            if field not in results:
                return False, f"Missing required field: {field}"

        # Validate metrics
        if not isinstance(results["metrics"], dict):
            return False, "Metrics must be a dictionary"

        required_metrics = ["mae", "rmse", "mape", "r2"]
        for metric in required_metrics:
            if metric not in results["metrics"]:
                return False, f"Missing required metric: {metric}"

        # Validate forecast
        if not isinstance(results["forecast"], list):
            return False, "Forecast must be a list"

        if len(results["forecast"]) == 0:
            return False, "Forecast list is empty"

        # Validate forecast items
        for item in results["forecast"]:
            if not isinstance(item, dict):
                return False, "Each forecast item must be a dictionary"
            if "date" not in item or "value" not in item:
                return False, "Forecast items must have 'date' and 'value' fields"

        return True, None

    def get_model_info(self, code_path):
        """Extract model information from code file"""
        model_name = Path(code_path).stem
        model_type = model_name.split('_')[0] if '_' in model_name else model_name

        return {
            "name": model_name,
            "type": model_type,
            "path": code_path
        }

    def cleanup_failed_models(self, model_path):
        """Clean up files from failed model execution"""
        try:
            # Remove the failed model file if needed
            # For now, we keep it for debugging
            pass
        except Exception as e:
            print(f"Error during cleanup: {e}")


class BatchExecutor:
    """Execute multiple models in sequence or parallel"""

    def __init__(self, timeout=600):
        self.executor = ModelExecutor(timeout=timeout)

    def execute_batch(self, code_paths, parallel=False):
        """
        Execute multiple model scripts

        Args:
            code_paths: List of paths to model scripts
            parallel: Whether to execute in parallel (not implemented yet)

        Returns:
            Dictionary mapping code_path to results
        """
        results = {}

        for code_path in code_paths:
            print(f"Executing {code_path}...")
            result = self.executor.execute_model_with_retry(code_path)
            results[code_path] = result

            if result["success"]:
                print(f"✓ {code_path} completed successfully")
            else:
                print(f"✗ {code_path} failed: {result.get('error', 'Unknown error')}")

        return results

    def get_best_model(self, results):
        """
        Find the best performing model from batch results

        Args:
            results: Dictionary of execution results

        Returns:
            Tuple (best_model_path, best_metrics)
        """
        best_model = None
        best_mae = float('inf')

        for code_path, result in results.items():
            if not result["success"]:
                continue

            if "results" not in result or "metrics" not in result["results"]:
                continue

            mae = result["results"]["metrics"].get("mae")
            if mae is not None and mae < best_mae:
                best_mae = mae
                best_model = code_path

        if best_model:
            return best_model, results[best_model]["results"]["metrics"]

        return None, None


# Example usage
if __name__ == "__main__":
    executor = ModelExecutor()

    # Test with a sample model file
    test_code = """
import json
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Simple test
data = {"date": ["2023-01-01", "2023-01-02"], "sales": [100, 110]}
df = pd.DataFrame(data)

metrics = {
    "mae": 5.2,
    "rmse": 7.1,
    "mape": 4.8,
    "r2": 0.95
}

forecast = [
    {"date": "2023-01-03", "value": 115},
    {"date": "2023-01-04", "value": 120}
]

result = {
    "metrics": metrics,
    "forecast": forecast,
    "training_time": 1.5
}

print(json.dumps(result))
"""

    # Write test code
    test_path = "models/generated_code/test_model.py"
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    with open(test_path, 'w') as f:
        f.write(test_code)

    # Execute
    result = executor.execute_model(test_path)
    print("\nExecution Result:")
    print(json.dumps(result, indent=2))

    # Validate
    if result["success"]:
        is_valid, error = executor.validate_model_output(result["results"])
        print(f"\nValidation: {'✓ Valid' if is_valid else '✗ Invalid - ' + error}")
