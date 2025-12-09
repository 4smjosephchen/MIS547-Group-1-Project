## 📄 README.md: Taiwan Stock Prediction MLOps Project

This repository contains the full, version-controlled code for the **Taiwan Stock Price Prediction MLOps Pipeline**, deployed across several services on **DigitalOcean**.

Each top-level directory corresponds to a specific service or Droplet in our production infrastructure.

---

## 🚀 Project Architecture Overview

This project is a time-series forecasting pipeline using a TensorFlow LSTM model. The infrastructure consists of three main services (Droplets) and shared cloud services for storage and tracking:

* **Services:** Web API, ML Model Trainer, Data Collector.
* **Database:** DigitalOcean Managed PostgreSQL (for MLflow Tracking and feature storage).
* **Model Registry:** DigitalOcean Spaces (S3-compatible) for storing model artifacts.

---

## 📦 Repository Structure

| Folder | Service / Droplet | Description |
| :--- | :--- | :--- |
| **`web-api-droplet`** | **Web API (Public)** | Contains the Flask/Gunicorn application that serves predictions. It connects to the database to fetch the latest features and loads the trained model from DigitalOcean Spaces on startup. |
| **`ml-model-trainer`** | **ML Trainer (Private)** | Contains the Python script (`train.py`) responsible for training the TensorFlow LSTM model, logging metrics, and pushing the final model artifact to DigitalOcean Spaces via MLflow. |
| **`data-collector-droplet`** | **Data Collector (Private)** | Contains the scripts (`collect_data.py`, `process_data.py`) and cron jobs that scrape data (stock/earthquake), merge it, and populate the PostgreSQL feature table. |

---
