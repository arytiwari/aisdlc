# Automated Sales Forecasting System

An intelligent, self-improving sales forecasting system that automatically generates, tests, compares, and retrains machine learning models using AI-powered code generation.

## Features

### Core Capabilities
- **AI-Powered Code Generation**: Uses Claude API to generate custom forecasting models tailored to your data
- **Multiple Model Types**: Automatically generates and compares:
  - ARIMA (Time Series)
  - Prophet (Facebook's forecasting tool)
  - XGBoost (Gradient Boosting)
  - Random Forest
  - LightGBM
  - LSTM (Deep Learning)
- **Automatic Model Selection**: Compares all models and automatically selects the best performer
- **Self-Improving**: Continuously monitors performance and retrains when accuracy degrades
- **Real-Time Notifications**: Get notified about model updates, retraining events, and performance changes
- **Interactive Dashboard**: Beautiful web interface for data visualization and model management

### Workflow
1. **Upload Data**: Simply upload your sales data (CSV/Excel)
2. **Generate Models**: System generates multiple forecasting approaches using AI
3. **Train & Compare**: Automatically trains and evaluates all models
4. **Auto-Improve**: Monitors performance and retrains periodically or when needed
5. **Forecast**: Get accurate predictions with confidence intervals

## System Requirements

### macOS
- macOS 10.15 (Catalina) or later
- 8GB RAM minimum (16GB recommended)
- 2GB free disk space

### Software
- Python 3.9 or later
- Node.js 16 or later
- Homebrew (will be installed automatically)

## Installation

### Quick Install

1. **Clone or download this repository**
   ```bash
   cd aisdlc
   ```

2. **Get your Anthropic API Key**
   - Sign up at [https://console.anthropic.com/](https://console.anthropic.com/)
   - Generate an API key
   - Keep it handy for the next step

3. **Run the installer**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

4. **Configure your API key**
   ```bash
   nano .env
   # Add your API key:
   # ANTHROPIC_API_KEY=sk-ant-xxxxx
   ```

5. **Start the system**
   ```bash
   ./run.sh
   ```

6. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Usage Guide

### 1. Upload Your Data

Your sales data should be in CSV or Excel format with at least two columns:
- **Date column**: Any date format (e.g., 2023-01-01, 01/01/2023)
- **Sales column**: Numeric sales values

**Example data format:**
```csv
date,sales
2023-01-01,1523
2023-01-02,1687
2023-01-03,1456
...
```

A sample dataset is provided in `data/sample_sales.csv` to get you started.

### 2. Generate Models

Once your data is uploaded:
1. Click **"Generate Models"** button
2. The system will use AI to create customized forecasting code for 5-6 different model types
3. This process takes 2-5 minutes depending on your data

### 3. Train Models

After models are generated:
1. Click **"Train Models"** button
2. The system will train all models and evaluate their performance
3. Training time varies by model type (30 seconds to 5 minutes per model)

### 4. View Results

The dashboard shows:
- **Best Model**: Automatically selected based on performance metrics
- **Performance Metrics**: MAE, RMSE, MAPE, R² for all models
- **Forecast Chart**: 30-day forecast visualization
- **Model Comparison**: Side-by-side comparison of all models
- **Retraining History**: Track of all improvements over time

### 5. Auto-Retraining

The system automatically:
- Monitors model performance
- Retrains on a schedule (default: every 24 hours)
- Retrains when performance degrades beyond threshold (default: 10%)
- Sends notifications about all retraining events

You can configure auto-retraining in the **Settings** tab.

## Architecture

### Backend (Python/FastAPI)
```
backend/
├── app.py              # Main FastAPI application
├── database.py         # SQLAlchemy models and database setup
├── code_generator.py   # AI-powered code generation using Claude
├── model_executor.py   # Safe execution of generated models
├── model_evaluator.py  # Model comparison and ranking
├── auto_trainer.py     # Automatic retraining system
└── requirements.txt    # Python dependencies
```

### Frontend (React/Vite)
```
frontend/
├── src/
│   ├── App.jsx         # Main application component
│   ├── services/api.js # API communication layer
│   └── index.css       # Styling
├── package.json        # Node.js dependencies
└── vite.config.js      # Vite configuration
```

### Data Storage
```
data/
├── sample_sales.csv    # Example dataset
└── uploads/            # User-uploaded datasets

database/
└── aisdlc.db          # SQLite database

models/
├── generated_code/     # AI-generated model code
└── saved_models/       # Trained model files
```

## API Documentation

Once the system is running, visit:
- **Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints

- `POST /api/datasets/upload` - Upload a new dataset
- `POST /api/models/generate` - Generate forecasting models
- `POST /api/models/train` - Train generated models
- `GET /api/models/best/{dataset_id}` - Get best performing model
- `GET /api/compare/{dataset_id}` - Compare all models
- `POST /api/retrain` - Trigger manual retraining
- `GET /api/notifications` - Get system notifications

## Configuration

Edit `.env` file to configure:

```bash
# Required: Your Anthropic API Key
ANTHROPIC_API_KEY=your_key_here

# Optional: Auto-retraining settings (can also be changed in UI)
AUTO_RETRAIN_ENABLED=true
RETRAIN_SCHEDULE_HOURS=24
PERFORMANCE_THRESHOLD=0.10
```

Settings can also be modified through the web interface in the **Settings** tab.

## Performance Metrics Explained

- **MAE (Mean Absolute Error)**: Average prediction error. Lower is better.
- **RMSE (Root Mean Squared Error)**: Similar to MAE but penalizes large errors more. Lower is better.
- **MAPE (Mean Absolute Percentage Error)**: Error as a percentage. Lower is better.
- **R² (R-squared)**: How well the model fits the data (0-1). Higher is better. Above 0.8 is good.

## Troubleshooting

### Installation Issues

**Problem**: Python dependencies fail to install
```bash
# Solution: Ensure you have Python 3.9+
python3 --version

# Upgrade pip
pip install --upgrade pip

# Install dependencies individually
pip install fastapi uvicorn pandas numpy
```

**Problem**: Node.js dependencies fail to install
```bash
# Solution: Clear npm cache
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Runtime Issues

**Problem**: Backend fails to start
```bash
# Check logs
cat logs/backend.log

# Common fix: Activate virtual environment
source venv/bin/activate
cd backend
python app.py
```

**Problem**: Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check firewall settings
- Verify CORS settings in `backend/app.py`

**Problem**: Code generation fails
- Verify your ANTHROPIC_API_KEY in `.env`
- Check your API quota at console.anthropic.com
- Review logs/backend.log for detailed error messages

### Data Issues

**Problem**: Dataset upload fails
- Ensure CSV has a date column and sales column
- Check for missing values or invalid dates
- Use the sample data to test: `data/sample_sales.csv`

## Development

### Running Tests
```bash
# Backend tests
source venv/bin/activate
pytest backend/

# Frontend tests
cd frontend
npm test
```

### Making Changes

**Backend**: Edit files in `backend/`, server will auto-reload

**Frontend**: Edit files in `frontend/src/`, Vite will auto-reload

### Adding New Model Types

1. Update `code_generator.py` with new model-specific prompts
2. Add model type to `model_types` list in `auto_trainer.py`
3. System will automatically generate and evaluate the new model type

## System Workflow

```
┌─────────────────┐
│  Upload Data    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AI Generates    │◄─── Claude API
│ Custom Models   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Train & Evaluate│
│  All Models     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select Best     │
│     Model       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Monitor & Auto  │
│    Retrain      │
└─────────────────┘
```

## Security Notes

- API keys are stored in `.env` and never exposed to frontend
- Generated code is executed in a controlled subprocess environment
- All file uploads are validated for type and size
- Database uses SQLAlchemy with parameterized queries

## Performance Tips

1. **Data Size**: For best results, use at least 100 data points
2. **Memory**: Close other applications when training LSTM models
3. **API Calls**: Code generation uses API credits, one call per model type
4. **Training Time**: First training takes longer; subsequent retraining is faster

## Logs

System logs are stored in:
- `logs/backend.log` - Backend server logs
- `logs/frontend.log` - Frontend server logs

View logs in real-time:
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

## Uninstallation

```bash
# Stop the system
# Press Ctrl+C in the terminal running the system

# Remove virtual environment and dependencies
rm -rf venv
rm -rf frontend/node_modules

# Remove generated data (optional)
rm -rf database/*.db
rm -rf models/generated_code/*
rm -rf models/saved_models/*
rm -rf data/uploads/*
```

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Review logs in `logs/` directory
3. Check API documentation at http://localhost:8000/docs

## License

This project is provided as-is for personal and educational use.

## Credits

Built with:
- **FastAPI** - Modern Python web framework
- **React** - Frontend UI framework
- **Anthropic Claude** - AI code generation
- **scikit-learn** - Machine learning
- **Prophet** - Time series forecasting
- **TensorFlow** - Deep learning
- **Recharts** - Data visualization

---

**Happy Forecasting!** 🚀📈
