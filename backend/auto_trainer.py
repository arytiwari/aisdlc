"""
Auto-Retraining System - Automatically retrain models and notify users
"""
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
import pandas as pd
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from database import (
    SessionLocal, Dataset, GeneratedModel, ModelEvaluation,
    RetrainingLog, Notification, SystemConfig
)
from code_generator import CodeGenerator
from model_executor import ModelExecutor, BatchExecutor
from model_evaluator import ModelEvaluator


class AutoTrainer:
    """Automatic model retraining and improvement system"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.code_generator = None  # Initialized when API key is available
        self.model_executor = ModelExecutor()
        self.batch_executor = BatchExecutor()
        self.model_evaluator = ModelEvaluator()

    def initialize_code_generator(self, api_key: str):
        """Initialize code generator with API key"""
        self.code_generator = CodeGenerator(api_key=api_key)

    def start(self):
        """Start the auto-retraining scheduler"""
        db = SessionLocal()
        try:
            # Get schedule from config
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == "retrain_schedule_hours"
            ).first()

            hours = int(config.config_value) if config else 24

            # Schedule retraining
            self.scheduler.add_job(
                func=self.check_and_retrain,
                trigger=IntervalTrigger(hours=hours),
                id='auto_retrain_job',
                name='Automatic Model Retraining',
                replace_existing=True
            )

            self.scheduler.start()
            print(f"Auto-retraining scheduler started (every {hours} hours)")

        finally:
            db.close()

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Auto-retraining scheduler stopped")

    def check_and_retrain(self):
        """Check if retraining is needed and perform it"""
        db = SessionLocal()
        try:
            # Check if auto-retrain is enabled
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == "auto_retrain_enabled"
            ).first()

            if not config or config.config_value.lower() != "true":
                print("Auto-retraining is disabled")
                return

            # Get all active datasets
            datasets = db.query(Dataset).filter(Dataset.is_active == True).all()

            for dataset in datasets:
                self._retrain_dataset(dataset, db, reason="scheduled")

        except Exception as e:
            print(f"Error in check_and_retrain: {e}")
            self._create_notification(
                db,
                "error",
                "Auto-Retraining Error",
                f"Error during scheduled retraining: {str(e)}"
            )
        finally:
            db.close()

    def _retrain_dataset(self, dataset: Dataset, db: Session, reason: str):
        """Retrain models for a specific dataset"""
        print(f"Retraining models for dataset: {dataset.name}")

        # Create notification
        self._create_notification(
            db,
            "info",
            "Retraining Started",
            f"Starting automatic retraining for dataset '{dataset.name}'. Reason: {reason}",
            dataset_id=dataset.id
        )

        try:
            # Get current best model
            current_best = db.query(ModelEvaluation).filter(
                ModelEvaluation.dataset_id == dataset.id,
                ModelEvaluation.is_best_model == True
            ).order_by(ModelEvaluation.evaluation_date.desc()).first()

            # Get dataset path
            dataset_path = os.path.join("data", "uploads", dataset.filename)

            if not os.path.exists(dataset_path):
                print(f"Dataset file not found: {dataset_path}")
                return

            # Analyze dataset
            df = pd.read_csv(dataset_path)
            analysis = self.code_generator.analyze_dataset(df)

            # Generate new models (all types)
            model_types = ["arima", "prophet", "xgboost", "random_forest", "lightgbm"]

            generated_codes = self.code_generator.generate_multiple_models(
                dataset_path, analysis, model_types
            )

            # Save and execute models
            results = []
            model_ids = []

            for model_type, code in generated_codes.items():
                if code is None:
                    continue

                # Save code
                code_path = self.code_generator.save_generated_code(model_type, code)

                # Save to database
                model = GeneratedModel(
                    dataset_id=dataset.id,
                    model_type=model_type,
                    model_name=f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    code_path=code_path,
                    generation_prompt=f"Auto-generated for retraining - {reason}",
                    hyperparameters={},
                    is_trained=False
                )
                db.add(model)
                db.commit()
                db.refresh(model)
                model_ids.append(model.id)

                # Execute model
                exec_result = self.model_executor.execute_model_with_retry(code_path)
                exec_result["model_name"] = model_type
                exec_result["model_type"] = model_type
                exec_result["model_id"] = model.id
                results.append(exec_result)

                # Save evaluation to database
                if exec_result["success"]:
                    metrics = exec_result["results"]["metrics"]
                    evaluation = ModelEvaluation(
                        model_id=model.id,
                        dataset_id=dataset.id,
                        mae=metrics.get("mae"),
                        rmse=metrics.get("rmse"),
                        mape=metrics.get("mape"),
                        r2_score=metrics.get("r2"),
                        train_size=0,  # Updated by model
                        test_size=0,
                        training_time_seconds=exec_result.get("execution_time"),
                        is_best_model=False
                    )
                    db.add(evaluation)
                    db.commit()

            # Compare and select best model
            best_model_result = self.model_evaluator.get_best_model(results)

            if best_model_result:
                new_best_model_id = best_model_result["model_id"]
                new_metrics = best_model_result["metrics"]

                # Update best model flag
                # First, unset all previous best models
                db.query(ModelEvaluation).filter(
                    ModelEvaluation.dataset_id == dataset.id
                ).update({"is_best_model": False})

                # Set new best model
                db.query(ModelEvaluation).filter(
                    ModelEvaluation.model_id == new_best_model_id
                ).update({"is_best_model": True})

                db.commit()

                # Calculate improvement
                improvement = 0
                if current_best:
                    old_mae = current_best.mae
                    new_mae = new_metrics["mae"]
                    improvement = ((old_mae - new_mae) / old_mae) * 100 if old_mae > 0 else 0

                # Log retraining
                log = RetrainingLog(
                    dataset_id=dataset.id,
                    trigger_reason=reason,
                    old_best_model_id=current_best.model_id if current_best else None,
                    new_best_model_id=new_best_model_id,
                    old_mae=current_best.mae if current_best else None,
                    new_mae=new_metrics["mae"],
                    improvement_percentage=improvement,
                    details=f"Trained {len(results)} models. Best: {best_model_result['model_type']}"
                )
                db.add(log)
                db.commit()

                # Create success notification
                if improvement > 0:
                    message = (
                        f"Retraining completed for '{dataset.name}'. "
                        f"New best model: {best_model_result['model_type']}. "
                        f"Performance improved by {improvement:.2f}% "
                        f"(MAE: {current_best.mae:.2f} → {new_metrics['mae']:.2f})"
                    )
                    notification_type = "success"
                else:
                    message = (
                        f"Retraining completed for '{dataset.name}'. "
                        f"New best model: {best_model_result['model_type']} "
                        f"(MAE: {new_metrics['mae']:.2f})"
                    )
                    notification_type = "info"

                self._create_notification(
                    db,
                    notification_type,
                    "Retraining Completed",
                    message,
                    dataset_id=dataset.id,
                    model_id=new_best_model_id
                )

                print(f"✓ Retraining completed. Best model: {best_model_result['model_type']}")

            else:
                self._create_notification(
                    db,
                    "warning",
                    "Retraining Completed with Issues",
                    f"Retraining for '{dataset.name}' completed but no successful models were generated.",
                    dataset_id=dataset.id
                )

        except Exception as e:
            print(f"Error retraining dataset {dataset.name}: {e}")
            self._create_notification(
                db,
                "error",
                "Retraining Failed",
                f"Failed to retrain models for '{dataset.name}': {str(e)}",
                dataset_id=dataset.id
            )

    def _create_notification(
        self,
        db: Session,
        notification_type: str,
        title: str,
        message: str,
        dataset_id: Optional[int] = None,
        model_id: Optional[int] = None
    ):
        """Create a notification in the database"""
        notification = Notification(
            notification_type=notification_type,
            title=title,
            message=message,
            related_dataset_id=dataset_id,
            related_model_id=model_id
        )
        db.add(notification)
        db.commit()

    def trigger_immediate_retrain(self, dataset_id: int, reason: str = "manual"):
        """Trigger immediate retraining for a specific dataset"""
        db = SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

            if not dataset:
                return {"error": "Dataset not found"}

            self._retrain_dataset(dataset, db, reason=reason)

            return {"success": True, "message": f"Retraining triggered for {dataset.name}"}

        finally:
            db.close()

    def check_performance_degradation(self, dataset_id: int) -> bool:
        """Check if model performance has degraded and needs retraining"""
        db = SessionLocal()
        try:
            # Get performance threshold
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == "performance_threshold"
            ).first()
            threshold = float(config.config_value) if config else 0.10

            # Get recent evaluations
            evaluations = db.query(ModelEvaluation).filter(
                ModelEvaluation.dataset_id == dataset_id
            ).order_by(ModelEvaluation.evaluation_date.desc()).limit(2).all()

            if len(evaluations) < 2:
                return False

            current = evaluations[0]
            previous = evaluations[1]

            # Check if MAE has increased beyond threshold
            degradation = (current.mae - previous.mae) / previous.mae if previous.mae > 0 else 0

            if degradation > threshold:
                dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
                if dataset:
                    self._create_notification(
                        db,
                        "warning",
                        "Performance Degradation Detected",
                        f"Model performance for '{dataset.name}' has degraded by {degradation*100:.1f}%. "
                        f"Automatic retraining recommended.",
                        dataset_id=dataset_id
                    )
                return True

            return False

        finally:
            db.close()


# Global auto-trainer instance
_auto_trainer_instance = None


def get_auto_trainer() -> AutoTrainer:
    """Get or create the global auto-trainer instance"""
    global _auto_trainer_instance
    if _auto_trainer_instance is None:
        _auto_trainer_instance = AutoTrainer()
    return _auto_trainer_instance


if __name__ == "__main__":
    # Test auto-trainer
    from dotenv import load_dotenv
    load_dotenv()

    trainer = AutoTrainer()
    trainer.initialize_code_generator(os.getenv("ANTHROPIC_API_KEY"))

    print("Auto-trainer initialized")
    print("Testing notification system...")

    db = SessionLocal()
    trainer._create_notification(
        db,
        "info",
        "Test Notification",
        "This is a test notification from the auto-trainer"
    )
    db.close()

    print("✓ Notification created successfully")
