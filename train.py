import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import mlflow
import mlflow.tensorflow

# --- CONFIGURATION ---
DB_URL = os.environ.get("DATABASE_URL")
# Example: s3://my-ml-bucket/mlflow
ARTIFACT_URL = os.environ.get("MLFLOW_S3_ROOT") 

SEQ_LENGTH = 10
TARGET_COL = 'TSM_Close'

def load_data():
    print("🔌 Connecting to Database...")
    engine = create_engine(DB_URL)
    query = "SELECT * FROM processed_training_data ORDER BY merge_date ASC"
    df = pd.read_sql(query, engine)
    if 'merge_date' in df.columns:
        df['merge_date'] = pd.to_datetime(df['merge_date'])
        df = df.set_index('merge_date')
    return df

def create_sequences(data, target, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        x = data[i:(i + seq_length)]
        y = target[i + seq_length]
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)

def train():
    mlflow.set_tracking_uri(DB_URL)
    
    # --- CRITICAL: Set Experiment with S3 Location ---
    experiment_name = "Taiwan_Stock_Prediction_Production"
    
    try:
        # Create experiment with S3 bucket if it doesn't exist
        mlflow.create_experiment(experiment_name, artifact_location=ARTIFACT_URL)
    except:
        pass # Experiment already exists
        
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run():
        # 1. Load & Process
        df = load_data()
        feature_cols = [c for c in df.columns if 'Close' in c or 'magnitude' in c]
        print(f"Features: {feature_cols}")
        
        data_values = df[feature_cols].values
        target_values = df[[TARGET_COL]].values
        
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data_values)
        
        target_scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_target = target_scaler.fit_transform(target_values)

        X, y = create_sequences(scaled_data, scaled_target, SEQ_LENGTH)

        # 2. Train
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        model.fit(X, y, batch_size=32, epochs=5, validation_split=0.1)
        
        # 3. Upload to Spaces
        print(f"🚀 Uploading model to: {ARTIFACT_URL}")
        mlflow.tensorflow.log_model(model, "model")
        print("🎉 Training & Upload Complete!")

if __name__ == "__main__":
    train()
