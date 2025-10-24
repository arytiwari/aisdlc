"""
FastAPI Backend for Automated Sales Forecasting System
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from database import (
    get_db, init_db, SessionLocal,
    Dataset, GeneratedModel, ModelEvaluation,
    Forecast, RetrainingLog, Notification, SystemConfig
)
from code_generator import CodeGenerator
from model_executor import ModelExecutor, BatchExecutor
from model_evaluator import ModelEvaluator
from auto_trainer import AutoTrainer, get_auto_trainer

# Initialize FastAPI
app = FastAPI(
    title="Automated Sales Forecasting System",
    description="AI-powered system that generates, tests, and improves forecasting models",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Global instances
code_generator = None
model_executor = ModelExecutor()
batch_executor = BatchExecutor()
model_evaluator = ModelEvaluator()
auto_trainer = None


# Pydantic models
class DatasetResponse(BaseModel):
    id: int
    name: str
    filename: str
    upload_date: datetime
    row_count: int
    date_range_start: str
    date_range_end: str
    is_active: bool

    class Config:
        from_attributes = True


class ModelResponse(BaseModel):
    id: int
    dataset_id: int
    model_type: str
    model_name: str
    created_date: datetime
    is_trained: bool

    class Config:
        from_attributes = True


class EvaluationResponse(BaseModel):
    id: int
    model_id: int
    mae: float
    rmse: float
    mape: float
    r2_score: float
    training_time_seconds: float
    is_best_model: bool

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    created_date: datetime
    notification_type: str
    title: str
    message: str
    is_read: bool

    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    config_key: str
    config_value: str


class RetrainRequest(BaseModel):
    dataset_id: int
    reason: Optional[str] = "manual"


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global code_generator, auto_trainer

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        code_generator = CodeGenerator(api_key=api_key)
        auto_trainer = get_auto_trainer()
        auto_trainer.initialize_code_generator(api_key)
        auto_trainer.start()
        print("✓ Code generator and auto-trainer initialized")
    else:
        print("⚠ ANTHROPIC_API_KEY not found. Code generation will not work.")

    print("✓ Server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if auto_trainer:
        auto_trainer.stop()
    print("✓ Server shutdown complete")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Automated Sales Forecasting System",
        "version": "1.0.0",
        "status": "running",
        "code_generator_ready": code_generator is not None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "code_generator": code_generator is not None,
            "auto_trainer": auto_trainer is not None
        }
    }


# Dataset Endpoints

@app.post("/api/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new sales dataset"""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(400, "Only CSV and Excel files are supported")

        # Save file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # Read and validate data
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        if df.shape[1] < 2:
            raise HTTPException(400, "Dataset must have at least 2 columns (date and sales)")

        # Assume first column is date, second is sales
        date_col = df.columns[0]
        sales_col = df.columns[1]

        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col])

        # Create dataset record
        dataset = Dataset(
            name=file.filename.rsplit('.', 1)[0],
            filename=file.filename,
            row_count=len(df),
            date_column=date_col,
            sales_column=sales_col,
            date_range_start=str(df[date_col].min().date()),
            date_range_end=str(df[date_col].max().date()),
            is_active=True
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return {
            "success": True,
            "message": "Dataset uploaded successfully",
            "dataset": DatasetResponse.from_orm(dataset)
        }

    except Exception as e:
        raise HTTPException(500, f"Error uploading dataset: {str(e)}")


@app.get("/api/datasets", response_model=List[DatasetResponse])
async def get_datasets(db: Session = Depends(get_db)):
    """Get all datasets"""
    datasets = db.query(Dataset).order_by(Dataset.upload_date.desc()).all()
    return datasets


@app.get("/api/datasets/{dataset_id}")
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get dataset details"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Get associated models
    models = db.query(GeneratedModel).filter(
        GeneratedModel.dataset_id == dataset_id
    ).all()

    # Get best model
    best_eval = db.query(ModelEvaluation).filter(
        ModelEvaluation.dataset_id == dataset_id,
        ModelEvaluation.is_best_model == True
    ).first()

    return {
        "dataset": DatasetResponse.from_orm(dataset),
        "model_count": len(models),
        "best_model": ModelResponse.from_orm(
            db.query(GeneratedModel).filter(GeneratedModel.id == best_eval.model_id).first()
        ) if best_eval else None
    }


@app.delete("/api/datasets/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Delete a dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Mark as inactive instead of deleting
    dataset.is_active = False
    db.commit()

    return {"success": True, "message": "Dataset deactivated"}


# Model Generation Endpoints

@app.post("/api/models/generate")
async def generate_models(
    dataset_id: int,
    model_types: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Generate forecasting models for a dataset"""
    if not code_generator:
        raise HTTPException(500, "Code generator not initialized. Check ANTHROPIC_API_KEY.")

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Default model types
    if not model_types:
        model_types = ["arima", "prophet", "xgboost", "random_forest", "lightgbm"]

    try:
        # Get dataset path
        dataset_path = os.path.join("data", "uploads", dataset.filename)

        # Analyze dataset
        df = pd.read_csv(dataset_path)
        analysis = code_generator.analyze_dataset(df)

        # Generate models
        generated_codes = code_generator.generate_multiple_models(
            dataset_path, analysis, model_types
        )

        generated_models = []

        for model_type, code in generated_codes.items():
            if code is None:
                continue

            # Save code
            code_path = code_generator.save_generated_code(model_type, code)

            # Save to database
            model = GeneratedModel(
                dataset_id=dataset_id,
                model_type=model_type,
                model_name=f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                code_path=code_path,
                generation_prompt=json.dumps(analysis),
                hyperparameters={},
                is_trained=False
            )
            db.add(model)
            db.commit()
            db.refresh(model)

            generated_models.append(ModelResponse.from_orm(model))

        return {
            "success": True,
            "message": f"Generated {len(generated_models)} models",
            "models": generated_models
        }

    except Exception as e:
        raise HTTPException(500, f"Error generating models: {str(e)}")


@app.post("/api/models/train")
async def train_models(
    dataset_id: int,
    model_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Train generated models"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Get models to train
    if model_ids:
        models = db.query(GeneratedModel).filter(
            GeneratedModel.id.in_(model_ids)
        ).all()
    else:
        models = db.query(GeneratedModel).filter(
            GeneratedModel.dataset_id == dataset_id,
            GeneratedModel.is_trained == False
        ).all()

    if not models:
        raise HTTPException(404, "No models found to train")

    results = []

    for model in models:
        # Execute model
        exec_result = model_executor.execute_model_with_retry(model.code_path)

        if exec_result["success"]:
            # Save evaluation
            metrics = exec_result["results"]["metrics"]
            evaluation = ModelEvaluation(
                model_id=model.id,
                dataset_id=dataset_id,
                mae=metrics.get("mae"),
                rmse=metrics.get("rmse"),
                mape=metrics.get("mape"),
                r2_score=metrics.get("r2"),
                train_size=0,
                test_size=0,
                training_time_seconds=exec_result.get("execution_time"),
                is_best_model=False
            )
            db.add(evaluation)

            # Mark model as trained
            model.is_trained = True

            # Save forecast
            forecast_data = exec_result["results"].get("forecast", [])
            if forecast_data:
                forecast = Forecast(
                    model_id=model.id,
                    dataset_id=dataset_id,
                    forecast_horizon=len(forecast_data),
                    forecast_data=forecast_data
                )
                db.add(forecast)

            db.commit()

            results.append({
                "model_id": model.id,
                "model_type": model.model_type,
                "success": True,
                "metrics": metrics
            })
        else:
            results.append({
                "model_id": model.id,
                "model_type": model.model_type,
                "success": False,
                "error": exec_result.get("error")
            })

    # Update best model
    await update_best_model(dataset_id, db)

    return {
        "success": True,
        "message": f"Trained {len(results)} models",
        "results": results
    }


async def update_best_model(dataset_id: int, db: Session):
    """Update the best model for a dataset"""
    # Get all evaluations for this dataset
    evaluations = db.query(ModelEvaluation).filter(
        ModelEvaluation.dataset_id == dataset_id
    ).all()

    if not evaluations:
        return

    # Find best based on MAE
    best_eval = min(evaluations, key=lambda e: e.mae)

    # Reset all best_model flags
    for eval in evaluations:
        eval.is_best_model = False

    # Set best model
    best_eval.is_best_model = True
    db.commit()


@app.get("/api/models", response_model=List[ModelResponse])
async def get_models(dataset_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all models, optionally filtered by dataset"""
    query = db.query(GeneratedModel)

    if dataset_id:
        query = query.filter(GeneratedModel.dataset_id == dataset_id)

    models = query.order_by(GeneratedModel.created_date.desc()).all()
    return models


@app.get("/api/models/{model_id}/evaluation")
async def get_model_evaluation(model_id: int, db: Session = Depends(get_db)):
    """Get model evaluation metrics"""
    evaluation = db.query(ModelEvaluation).filter(
        ModelEvaluation.model_id == model_id
    ).first()

    if not evaluation:
        raise HTTPException(404, "Evaluation not found")

    model = db.query(GeneratedModel).filter(GeneratedModel.id == model_id).first()

    return {
        "model": ModelResponse.from_orm(model),
        "evaluation": EvaluationResponse.from_orm(evaluation)
    }


@app.get("/api/models/best/{dataset_id}")
async def get_best_model(dataset_id: int, db: Session = Depends(get_db)):
    """Get the best model for a dataset"""
    evaluation = db.query(ModelEvaluation).filter(
        ModelEvaluation.dataset_id == dataset_id,
        ModelEvaluation.is_best_model == True
    ).first()

    if not evaluation:
        raise HTTPException(404, "No best model found")

    model = db.query(GeneratedModel).filter(
        GeneratedModel.id == evaluation.model_id
    ).first()

    # Get forecast
    forecast = db.query(Forecast).filter(
        Forecast.model_id == model.id
    ).order_by(Forecast.forecast_date.desc()).first()

    return {
        "model": ModelResponse.from_orm(model),
        "evaluation": EvaluationResponse.from_orm(evaluation),
        "forecast": forecast.forecast_data if forecast else None
    }


# Comparison Endpoints

@app.get("/api/compare/{dataset_id}")
async def compare_models(dataset_id: int, db: Session = Depends(get_db)):
    """Compare all models for a dataset"""
    evaluations = db.query(ModelEvaluation).filter(
        ModelEvaluation.dataset_id == dataset_id
    ).all()

    if not evaluations:
        raise HTTPException(404, "No evaluations found")

    comparison = []

    for eval in evaluations:
        model = db.query(GeneratedModel).filter(
            GeneratedModel.id == eval.model_id
        ).first()

        comparison.append({
            "model_id": model.id,
            "model_type": model.model_type,
            "model_name": model.model_name,
            "mae": eval.mae,
            "rmse": eval.rmse,
            "mape": eval.mape,
            "r2_score": eval.r2_score,
            "training_time": eval.training_time_seconds,
            "is_best": eval.is_best_model
        })

    # Sort by MAE
    comparison.sort(key=lambda x: x["mae"])

    return {
        "dataset_id": dataset_id,
        "model_count": len(comparison),
        "comparison": comparison
    }


# Notification Endpoints

@app.get("/api/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get notifications"""
    query = db.query(Notification)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(
        Notification.created_date.desc()
    ).limit(limit).all()

    return notifications


@app.patch("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(404, "Notification not found")

    notification.is_read = True
    db.commit()

    return {"success": True}


# Auto-Retraining Endpoints

@app.post("/api/retrain")
async def trigger_retrain(request: RetrainRequest, db: Session = Depends(get_db)):
    """Manually trigger retraining"""
    if not auto_trainer:
        raise HTTPException(500, "Auto-trainer not initialized")

    result = auto_trainer.trigger_immediate_retrain(request.dataset_id, request.reason)

    if "error" in result:
        raise HTTPException(404, result["error"])

    return result


@app.get("/api/retrain/history/{dataset_id}")
async def get_retrain_history(dataset_id: int, db: Session = Depends(get_db)):
    """Get retraining history for a dataset"""
    logs = db.query(RetrainingLog).filter(
        RetrainingLog.dataset_id == dataset_id
    ).order_by(RetrainingLog.retrain_date.desc()).all()

    return [
        {
            "id": log.id,
            "date": log.retrain_date,
            "reason": log.trigger_reason,
            "old_mae": log.old_mae,
            "new_mae": log.new_mae,
            "improvement": log.improvement_percentage,
            "details": log.details
        }
        for log in logs
    ]


# Configuration Endpoints

@app.get("/api/config")
async def get_config(db: Session = Depends(get_db)):
    """Get system configuration"""
    configs = db.query(SystemConfig).all()
    return {config.config_key: config.config_value for config in configs}


@app.patch("/api/config")
async def update_config(update: ConfigUpdate, db: Session = Depends(get_db)):
    """Update system configuration"""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == update.config_key
    ).first()

    if not config:
        config = SystemConfig(config_key=update.config_key)
        db.add(config)

    config.config_value = update.config_value
    config.last_updated = datetime.utcnow()
    db.commit()

    return {"success": True, "config": {update.config_key: update.config_value}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
