import os
import boto3
import tensorflow as tf
import pandas as pd
import numpy as np
from flask import Flask, jsonify
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from urllib.parse import urlparse
import shutil
import mlflow

app = Flask(__name__)

# --- CONFIGURATION ---
DB_URL = os.environ.get("DATABASE_URL")
EXPERIMENT_NAME = "Taiwan_Stock_Prediction_Production"
SEQ_LENGTH = 10
model = None

def get_s3_client():
    return boto3.client('s3',
        endpoint_url=os.environ.get('MLFLOW_S3_ENDPOINT_URL'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )

def find_newest_model_in_s3():
    print("🔎 Scanning S3 for newest model...")
    s3 = get_s3_client()
    bucket_name = "group-1-model-registry"

    try:
        paginator = s3.get_paginator('list_objects_v2')
        candidates = []
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('saved_model.pb'):
                        candidates.append(obj)

        if not candidates:
            print("❌ No 'saved_model.pb' found in bucket.")
            return None, None

        newest = sorted(candidates, key=lambda x: x['LastModified'], reverse=True)[0]
        print(f"✅ Found newest model: {newest['Key']} (Last Modified: {newest['LastModified']})")

        model_folder_key = newest['Key'].replace('/saved_model.pb', '')
        return bucket_name, model_folder_key

    except Exception as e:
        print(f"❌ S3 Search Error: {e}")
        return None, None

def download_s3_folder(bucket_name, s3_folder, local_dir):
    s3 = get_s3_client()
    paginator = s3.get_paginator('list_objects_v2')

    print(f"📥 Downloading from s3://{bucket_name}/{s3_folder} to {local_dir}...")

    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
    os.makedirs(local_dir)

    for page in paginator.paginate(Bucket=bucket_name, Prefix=s3_folder):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                rel_path = key.replace(s3_folder, '').lstrip('/')
                if not rel_path: continue

                local_file_path = os.path.join(local_dir, rel_path)
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                s3.download_file(bucket_name, key, local_file_path)

def load_latest_model():
    global model
    mlflow.set_tracking_uri(DB_URL)

    bucket, model_prefix = find_newest_model_in_s3()

    if not bucket or not model_prefix:
        print("❌ Could not find any model in S3.")
        return

    try:
        local_model_dir = "/app/model_cache"
        download_s3_folder(bucket, model_prefix, local_model_dir)

        print(f"📥 Loading SavedModel from: {local_model_dir}...")
        model = tf.saved_model.load(local_model_dir)
        print("✅ Model loaded successfully (Native TensorFlow)!")

    except Exception as e:
        print(f"❌ Error loading model: {e}")


# --- STABLE HEALTH CHECK ENDPOINT (FIX FOR 500 ERROR) ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

def get_recent_data():
    engine = create_engine(DB_URL)
    query = f"SELECT * FROM processed_training_data ORDER BY merge_date DESC LIMIT {SEQ_LENGTH + 5}"
    df = pd.read_sql(query, engine)
    df = df.sort_values('merge_date', ascending=True)
    feature_cols = [c for c in df.columns if 'Close' in c or 'magnitude' in c]
    return df[feature_cols].values[-SEQ_LENGTH:]

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        raw_data = get_recent_data()
        if len(raw_data) < SEQ_LENGTH:
            return jsonify({"error": "Not enough data"}), 400

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(raw_data)
        input_tensor = np.array([scaled_data], dtype=np.float32)

        try:
            prediction_scaled = model(input_tensor)
        except:
            infer = model.signatures["serving_default"]
            prediction_scaled = infer(tf.constant(input_tensor))['dense_1']

        prediction_val = prediction_scaled.numpy()[0][0]

        prediction_price = scaler.inverse_transform(
            np.tile([[prediction_val]], (1, raw_data.shape[1]))
        )[0][0]

        return jsonify({
            "ticker": "TSM",
            "prediction": float(prediction_price),
            "status": "success"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
