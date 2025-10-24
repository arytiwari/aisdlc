"""
Database models and setup for the Automated Sales Forecasting System
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database setup
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'aisdlc.db')
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Dataset(Base):
    """Stores uploaded sales datasets"""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    row_count = Column(Integer)
    date_column = Column(String)
    sales_column = Column(String)
    date_range_start = Column(String)
    date_range_end = Column(String)
    is_active = Column(Boolean, default=True)


class GeneratedModel(Base):
    """Stores information about generated forecasting models"""
    __tablename__ = "generated_models"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False)
    model_type = Column(String, nullable=False)  # arima, prophet, lstm, xgboost, etc.
    model_name = Column(String, nullable=False)
    code_path = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    generation_prompt = Column(Text)
    hyperparameters = Column(JSON)
    is_trained = Column(Boolean, default=False)


class ModelEvaluation(Base):
    """Stores model performance metrics"""
    __tablename__ = "model_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, nullable=False)
    dataset_id = Column(Integer, nullable=False)
    evaluation_date = Column(DateTime, default=datetime.utcnow)

    # Metrics
    mae = Column(Float)  # Mean Absolute Error
    rmse = Column(Float)  # Root Mean Squared Error
    mape = Column(Float)  # Mean Absolute Percentage Error
    r2_score = Column(Float)

    # Training info
    train_size = Column(Integer)
    test_size = Column(Integer)
    training_time_seconds = Column(Float)

    # Best model flag
    is_best_model = Column(Boolean, default=False)


class Forecast(Base):
    """Stores generated forecasts"""
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, nullable=False)
    dataset_id = Column(Integer, nullable=False)
    forecast_date = Column(DateTime, default=datetime.utcnow)
    forecast_horizon = Column(Integer)  # Number of days forecasted
    forecast_data = Column(JSON)  # Array of {date, predicted_value, confidence_interval}


class RetrainingLog(Base):
    """Logs automatic retraining events"""
    __tablename__ = "retraining_logs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False)
    retrain_date = Column(DateTime, default=datetime.utcnow)
    trigger_reason = Column(String)  # scheduled, performance_degradation, new_data
    old_best_model_id = Column(Integer)
    new_best_model_id = Column(Integer)
    old_mae = Column(Float)
    new_mae = Column(Float)
    improvement_percentage = Column(Float)
    details = Column(Text)


class Notification(Base):
    """User notifications for system events"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    notification_type = Column(String)  # info, success, warning, error
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    related_model_id = Column(Integer)
    related_dataset_id = Column(Integer)


class SystemConfig(Base):
    """System configuration settings"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, nullable=False)
    config_value = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)

    # Set default configurations
    db = SessionLocal()
    try:
        # Check if auto_retrain config exists
        config = db.query(SystemConfig).filter(SystemConfig.config_key == "auto_retrain_enabled").first()
        if not config:
            db.add(SystemConfig(config_key="auto_retrain_enabled", config_value="true"))

        config = db.query(SystemConfig).filter(SystemConfig.config_key == "retrain_schedule_hours").first()
        if not config:
            db.add(SystemConfig(config_key="retrain_schedule_hours", config_value="24"))

        config = db.query(SystemConfig).filter(SystemConfig.config_key == "performance_threshold").first()
        if not config:
            db.add(SystemConfig(config_key="performance_threshold", config_value="0.10"))  # 10% degradation

        db.commit()
    except Exception as e:
        print(f"Error initializing config: {e}")
        db.rollback()
    finally:
        db.close()


def get_db():
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")
