#!/usr/bin/env python3
"""
Train fault detection ML models on generated telemetry data.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, precision_recall_fscore_support, confusion_matrix
import xgboost as xgb
import joblib
import os

print("="*80)
print("FAULT DETECTION ML MODEL TRAINING")
print("="*80)

# Load data
print("\n[1/5] Loading telemetry data...")
df = pd.read_csv('output/telemetry/telemetry.csv')
print(f"  ✓ Loaded {len(df)} records")

# Filter to HOST data only
df_hosts = df[df['component_type'] == 'HOST'].copy()
print(f"  ✓ Filtered to {len(df_hosts)} host records")

# Select features
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

X = df_hosts[feature_cols].fillna(0).values
y = (df_hosts['failed'] == 'true').astype(int).values

print(f"  ✓ Features: {X.shape}")
print(f"  ✓ Positive samples: {y.sum()} ({100*y.mean():.1f}%)")

# Split data
print("\n[2/5] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
print(f"  ✓ Train: {len(X_train)} samples")
print(f"  ✓ Test:  {len(X_test)} samples")

# Normalize
print("\n[3/5] Normalizing features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Save scaler
os.makedirs('models', exist_ok=True)
joblib.dump(scaler, 'models/scaler.pkl')
print("  ✓ Scaler saved to models/scaler.pkl")

# Train models
print("\n[4/5] Training ML models...")

# Random Forest
print("\n  [a] Random Forest Classifier...")
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
rf.fit(X_train_scaled, y_train)
joblib.dump(rf, 'models/random_forest.pkl')

y_pred_rf = rf.predict(X_test_scaled)
prec_rf, rec_rf, f1_rf, _ = precision_recall_fscore_support(
    y_test, y_pred_rf, average='binary', zero_division=0
)
print(f"      Precision: {prec_rf:.3f}")
print(f"      Recall:    {rec_rf:.3f}")
print(f"      F1-Score:  {f1_rf:.3f}")
print("      ✓ Saved to models/random_forest.pkl")

# XGBoost
print("\n  [b] XGBoost Classifier...")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    n_jobs=-1,
    verbosity=0
)
xgb_model.fit(X_train_scaled, y_train)
joblib.dump(xgb_model, 'models/xgboost.pkl')

y_pred_xgb = xgb_model.predict(X_test_scaled)
prec_xgb, rec_xgb, f1_xgb, _ = precision_recall_fscore_support(
    y_test, y_pred_xgb, average='binary', zero_division=0
)
print(f"      Precision: {prec_xgb:.3f}")
print(f"      Recall:    {rec_xgb:.3f}")
print(f"      F1-Score:  {f1_xgb:.3f}")
print("      ✓ Saved to models/xgboost.pkl")

# Isolation Forest (Unsupervised)
print("\n  [c] Isolation Forest (Unsupervised)...")
iso_forest = IsolationForest(
    n_estimators=100,
    contamination=0.15,
    random_state=42,
    n_jobs=-1
)
iso_forest.fit(X_train_scaled)
joblib.dump(iso_forest, 'models/isolation_forest.pkl')

y_pred_iso = iso_forest.predict(X_test_scaled)
y_pred_iso_binary = (y_pred_iso == -1).astype(int)  # -1 = anomaly = fault
prec_iso, rec_iso, f1_iso, _ = precision_recall_fscore_support(
    y_test, y_pred_iso_binary, average='binary', zero_division=0
)
print(f"      Precision: {prec_iso:.3f}")
print(f"      Recall:    {rec_iso:.3f}")
print(f"      F1-Score:  {f1_iso:.3f}")
print("      ✓ Saved to models/isolation_forest.pkl")

# Evaluation
print("\n[5/5] Model Evaluation Summary...")
print("\n" + "="*80)
print("RESULTS")
print("="*80)

print("\n┌─────────────────────┬───────────┬─────────┬──────────┐")
print("│ Model               │ Precision │  Recall │ F1-Score │")
print("├─────────────────────┼───────────┼─────────┼──────────┤")
print(f"│ Random Forest       │   {prec_rf:.3f}   │  {rec_rf:.3f}  │  {f1_rf:.3f}   │")
print(f"│ XGBoost             │   {prec_xgb:.3f}   │  {rec_xgb:.3f}  │  {f1_xgb:.3f}   │")
print(f"│ Isolation Forest    │   {prec_iso:.3f}   │  {rec_iso:.3f}  │  {f1_iso:.3f}   │")
print("└─────────────────────┴───────────┴─────────┴──────────┘")

# Best model
best_model = max(
    [('Random Forest', f1_rf), ('XGBoost', f1_xgb), ('Isolation Forest', f1_iso)],
    key=lambda x: x[1]
)
print(f"\n🏆 Best Model: {best_model[0]} (F1={best_model[1]:.3f})")

# Confusion Matrix for best supervised model (RF or XGB)
if f1_rf >= f1_xgb:
    y_pred_best = y_pred_rf
    best_name = "Random Forest"
else:
    y_pred_best = y_pred_xgb
    best_name = "XGBoost"

cm = confusion_matrix(y_test, y_pred_best)
tn, fp, fn, tp = cm.ravel()

print(f"\nConfusion Matrix ({best_name}):")
print("┌────────────────┬───────────────────┐")
print("│                │    Predicted      │")
print("├────────────────┼─────────┬─────────┤")
print("│                │  Fault  │ Normal  │")
print("├────────────────┼─────────┼─────────┤")
print(f"│ Actual Fault   │  {tp:4d}   │  {fn:4d}   │")
print(f"│ Actual Normal  │  {fp:4d}   │  {tn:4d}   │")
print("└────────────────┴─────────┴─────────┘")

accuracy = (tp + tn) / (tp + tn + fp + fn)
print(f"\n✓ Accuracy: {accuracy:.3f}")
print(f"✓ True Positives:  {tp}")
print(f"✓ False Positives: {fp}")
print(f"✓ False Negatives: {fn}")
print(f"✓ True Negatives:  {tn}")

print("\n" + "="*80)
print("TRAINING COMPLETE!")
print("="*80)
print(f"\nModels saved to: models/")
print("  - random_forest.pkl")
print("  - xgboost.pkl")
print("  - isolation_forest.pkl")
print("  - scaler.pkl")
