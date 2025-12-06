#!/usr/bin/env python3
"""
Train all fault detection ML models:
- Random Forest
- XGBoost
- LSTM Autoencoder
- Isolation Forest

Usage:
    python train_all_models.py --data ../output/telemetry/telemetry.csv --output ../models
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# Import individual model trainers
from models.random_forest_trainer import train_random_forest
from models.xgboost_trainer import train_xgboost
from models.lstm_autoencoder_trainer import train_lstm_autoencoder
from models.isolation_forest_trainer import train_isolation_forest


def load_telemetry_data(data_path):
    """Load and preprocess telemetry data."""
    print(f"Loading telemetry data from: {data_path}")

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records with {df.shape[1]} columns")

    # Select features (exclude metadata columns)
    feature_cols = [
        'cpu_utilization',
        'cpu_allocated_mips',
        'cpu_available_mips',
        'power_consumption_watts',
        'temperature_celsius',
        'temperature_cpu_sensor',
        'temperature_ambient',
        'vibration_magnitude',
        'vibration_frequency_hz',
        'ram_utilization',
        'storage_utilization'
    ]

    # Filter to only HOST data for hardware fault detection
    df_hosts = df[df['component_type'] == 'HOST'].copy()

    # Create labels from 'failed' column if it exists
    # Otherwise, use synthetic labels based on thresholds
    if 'failed' in df_hosts.columns:
        y = (df_hosts['failed'] == 'true').astype(int).values
    else:
        # Create synthetic labels based on anomalous conditions
        y = ((df_hosts['temperature_celsius'] > 75) |
             (df_hosts['cpu_utilization'] > 0.95) |
             (df_hosts['power_consumption_watts'] > 450)).astype(int).values

    X = df_hosts[feature_cols].fillna(0).values

    print(f"Features shape: {X.shape}")
    print(f"Positive samples: {y.sum()} ({100*y.mean():.2f}%)")

    return X, y, feature_cols


def main():
    parser = argparse.ArgumentParser(description='Train fault detection ML models')
    parser.add_argument('--data', type=str, required=True,
                       help='Path to telemetry CSV file')
    parser.add_argument('--output', type=str, default='../models',
                       help='Output directory for trained models')
    parser.add_argument('--models', type=str, nargs='+',
                       default=['rf', 'xgb', 'lstm', 'isoforest'],
                       help='Models to train: rf, xgb, lstm, isoforest')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    X, y, feature_names = load_telemetry_data(args.data)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    # Normalize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save scaler
    scaler_path = output_dir / 'scaler.pkl'
    joblib.dump(scaler, scaler_path)
    print(f"Saved scaler to: {scaler_path}")

    print("\n" + "="*80)
    print("TRAINING FAULT DETECTION MODELS")
    print("="*80)

    # Train Random Forest
    if 'rf' in args.models:
        print("\n[1/4] Training Random Forest...")
        rf_path = train_random_forest(
            X_train_scaled, y_train,
            X_test_scaled, y_test,
            output_dir / 'random_forest.pkl'
        )
        print(f"✓ Random Forest saved to: {rf_path}")

    # Train XGBoost
    if 'xgb' in args.models:
        print("\n[2/4] Training XGBoost...")
        xgb_path = train_xgboost(
            X_train_scaled, y_train,
            X_test_scaled, y_test,
            output_dir / 'xgboost.pkl'
        )
        print(f"✓ XGBoost saved to: {xgb_path}")

    # Train LSTM Autoencoder
    if 'lstm' in args.models:
        print("\n[3/4] Training LSTM Autoencoder...")
        lstm_path = train_lstm_autoencoder(
            X_train_scaled, y_train,
            X_test_scaled, y_test,
            output_dir / 'lstm_autoencoder.h5'
        )
        print(f"✓ LSTM Autoencoder saved to: {lstm_path}")

    # Train Isolation Forest
    if 'isoforest' in args.models:
        print("\n[4/4] Training Isolation Forest...")
        iso_path = train_isolation_forest(
            X_train_scaled,
            output_dir / 'isolation_forest.pkl'
        )
        print(f"✓ Isolation Forest saved to: {iso_path}")

    print("\n" + "="*80)
    print("ALL MODELS TRAINED SUCCESSFULLY!")
    print("="*80)
    print(f"\nModels saved to: {output_dir.absolute()}")


if __name__ == '__main__':
    main()
