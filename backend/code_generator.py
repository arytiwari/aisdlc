"""
LLM-based code generator for forecasting models
Uses Anthropic's Claude API to generate customized forecasting code
"""
import os
import json
from anthropic import Anthropic
from datetime import datetime
import pandas as pd


class CodeGenerator:
    """Generates forecasting model code using Claude API"""

    def __init__(self, api_key=None):
        """Initialize with Anthropic API key"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=self.api_key)

    def analyze_dataset(self, df):
        """Analyze dataset to provide context for code generation"""
        analysis = {
            "row_count": len(df),
            "columns": list(df.columns),
            "date_range": f"{df.iloc[0, 0]} to {df.iloc[-1, 0]}",
            "sales_mean": float(df.iloc[:, 1].mean()),
            "sales_std": float(df.iloc[:, 1].std()),
            "sales_min": float(df.iloc[:, 1].min()),
            "sales_max": float(df.iloc[:, 1].max()),
            "has_trend": self._detect_trend(df),
            "has_seasonality": self._detect_seasonality(df),
        }
        return analysis

    def _detect_trend(self, df):
        """Simple trend detection"""
        sales = df.iloc[:, 1].values
        first_half = sales[:len(sales)//2].mean()
        second_half = sales[len(sales)//2:].mean()
        return abs(second_half - first_half) / first_half > 0.1

    def _detect_seasonality(self, df):
        """Simple seasonality detection"""
        # Basic check for weekly patterns
        return len(df) > 14

    def generate_model_code(self, model_type, dataset_path, dataset_analysis):
        """
        Generate forecasting model code using Claude API

        Args:
            model_type: Type of model (arima, prophet, lstm, xgboost, random_forest)
            dataset_path: Path to the dataset file
            dataset_analysis: Dictionary with dataset analysis results

        Returns:
            Generated Python code as string
        """
        prompt = self._build_prompt(model_type, dataset_path, dataset_analysis)

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            generated_code = response.content[0].text

            # Extract code from markdown if present
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()

            return generated_code

        except Exception as e:
            raise Exception(f"Error generating code with Claude API: {str(e)}")

    def _build_prompt(self, model_type, dataset_path, analysis):
        """Build the prompt for Claude to generate forecasting code"""

        base_prompt = f"""You are an expert data scientist specializing in time series forecasting. Generate a complete, production-ready Python script for a {model_type.upper()} forecasting model.

Dataset Information:
- Path: {dataset_path}
- Rows: {analysis['row_count']}
- Date Range: {analysis['date_range']}
- Sales Statistics: Mean={analysis['sales_mean']:.2f}, Std={analysis['sales_std']:.2f}, Min={analysis['sales_min']:.2f}, Max={analysis['sales_max']:.2f}
- Trend Detected: {analysis['has_trend']}
- Seasonality Detected: {analysis['has_seasonality']}

Requirements:
1. Create a complete Python script that can be executed standalone
2. Read data from the CSV file at the provided path
3. Split data into train/test sets (80/20 split)
4. Build and train a {model_type.upper()} model optimized for this dataset
5. Include comprehensive error handling
6. Calculate and return these metrics: MAE, RMSE, MAPE, R2
7. Save the trained model to 'models/saved_models/{model_type}_model.pkl' using joblib
8. Generate forecasts for the next 30 days
9. Return results as a JSON object with structure:
   {{
       "metrics": {{"mae": float, "rmse": float, "mape": float, "r2": float}},
       "forecast": [{{"date": "YYYY-MM-DD", "value": float}}, ...],
       "training_time": float,
       "model_path": "path/to/saved/model.pkl"
   }}

"""

        # Add model-specific instructions
        model_specific_prompts = {
            "arima": """
For ARIMA model:
- Use pmdarima's auto_arima to find optimal (p,d,q) parameters
- Handle non-stationary data with differencing
- Include seasonal components if seasonality detected
- Use AIC/BIC for model selection
""",
            "prophet": """
For Prophet model:
- Configure appropriate seasonality (daily, weekly, yearly)
- Add changepoint detection
- Handle holidays if relevant
- Tune seasonality_prior_scale and changepoint_prior_scale
""",
            "lstm": """
For LSTM model:
- Use TensorFlow/Keras
- Create sequences with appropriate lookback window (30-60 days)
- Use 2-3 LSTM layers with dropout (0.2-0.3)
- Include early stopping and model checkpointing
- Normalize data using MinMaxScaler
- Use Adam optimizer with learning rate 0.001
""",
            "xgboost": """
For XGBoost model:
- Create lag features (1, 7, 14, 30 days)
- Add rolling mean and std features
- Extract date features (day of week, month, quarter)
- Use appropriate hyperparameters: n_estimators=100-200, max_depth=5-7, learning_rate=0.1
- Use time-series cross-validation
""",
            "random_forest": """
For Random Forest model:
- Create lag features (1, 7, 14, 30 days)
- Add rolling statistics (mean, std, min, max)
- Extract cyclical date features (sin/cos transforms)
- Use 100-200 estimators with max_depth=10-15
- Enable out-of-bag scoring
""",
            "lightgbm": """
For LightGBM model:
- Create lag features and rolling statistics
- Extract date features
- Use appropriate parameters: n_estimators=100, num_leaves=31, learning_rate=0.1
- Enable early stopping with validation set
"""
        }

        specific_prompt = model_specific_prompts.get(model_type, "")

        footer_prompt = """
Important:
- Write clean, documented code with comments
- Handle missing values appropriately
- Ensure reproducibility (set random seeds)
- Include all necessary imports
- Make sure the code outputs valid JSON to stdout as the final print statement
- Create necessary directories if they don't exist
- The code should be completely self-contained and executable

Generate ONLY the Python code, no explanations before or after."""

        return base_prompt + specific_prompt + footer_prompt

    def generate_multiple_models(self, dataset_path, dataset_analysis, model_types=None):
        """
        Generate code for multiple model types

        Args:
            dataset_path: Path to dataset
            dataset_analysis: Analysis results
            model_types: List of model types to generate (default: all)

        Returns:
            Dictionary mapping model_type to generated code
        """
        if model_types is None:
            model_types = ["arima", "prophet", "lstm", "xgboost", "random_forest", "lightgbm"]

        generated_models = {}

        for model_type in model_types:
            print(f"Generating {model_type} model code...")
            try:
                code = self.generate_model_code(model_type, dataset_path, dataset_analysis)
                generated_models[model_type] = code
                print(f"✓ {model_type} code generated successfully")
            except Exception as e:
                print(f"✗ Error generating {model_type}: {str(e)}")
                generated_models[model_type] = None

        return generated_models

    def save_generated_code(self, model_type, code, output_dir="models/generated_code"):
        """Save generated code to file"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{model_type}_{timestamp}.py"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as f:
            f.write(code)

        return filepath


# Example usage
if __name__ == "__main__":
    # Test code generation
    generator = CodeGenerator()

    # Analyze sample dataset
    df = pd.read_csv("../data/sample_sales.csv")
    analysis = generator.analyze_dataset(df)

    print("Dataset Analysis:")
    print(json.dumps(analysis, indent=2))

    # Generate a single model
    print("\nGenerating Prophet model code...")
    code = generator.generate_model_code("prophet", "../data/sample_sales.csv", analysis)

    # Save it
    filepath = generator.save_generated_code("prophet", code)
    print(f"\nCode saved to: {filepath}")
