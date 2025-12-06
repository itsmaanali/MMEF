#!/usr/bin/env python3
"""
Train fault detection ML models (Random Forest & Isolation Forest).
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, precision_recall_fscore_support, confusion_matrix
import joblib
import os

print("="*80)
print("FAULT DETECTION ML MODEL TRAINING")
print("="*80)

# Load data
print("\n[1/4] Loading telemetry data...")
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
y = df_hosts['failed'].astype(int).values  # Boolean True/False to 1/0

print(f"  ✓ Features: {X.shape}")
print(f"  ✓ Positive samples (faults): {y.sum()} ({100*y.mean():.1f}%)")
print(f"  ✓ Negative samples (normal): {len(y)-y.sum()} ({100*(1-y.mean()):.1f}%)")

# Split data
print("\n[2/4] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
print(f"  ✓ Train: {len(X_train)} samples ({y_train.sum()} faults)")
print(f"  ✓ Test:  {len(X_test)} samples ({y_test.sum()} faults)")

# Normalize
print("\n[3/4] Normalizing features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Save scaler
os.makedirs('models', exist_ok=True)
joblib.dump(scaler, 'models/scaler.pkl')
print("  ✓ Scaler fitted and saved")

# Train models
print("\n[4/4] Training ML models...\n")

# Random Forest
print("  [Model 1/2] Random Forest Classifier (Supervised)")
print("  " + "-"*60)
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=10,
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
print(f"      Precision: {prec_rf:.3f} (How many detected faults were real)")
print(f"      Recall:    {rec_rf:.3f} (How many real faults were detected)")
print(f"      F1-Score:  {f1_rf:.3f} (Harmonic mean of precision & recall)")
print("      ✓ Model saved to models/random_forest.pkl\n")

# Isolation Forest (Unsupervised)
print("  [Model 2/2] Isolation Forest (Unsupervised Anomaly Detection)")
print("  " + "-"*60)
iso_forest = IsolationForest(
    n_estimators=100,
    contamination=0.13,  # Expected proportion of anomalies
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
print("      ✓ Model saved to models/isolation_forest.pkl\n")

# Ensemble - Combine predictions
print("  [Ensemble] Combining both models...")
print("  " + "-"*60)
# If either model predicts fault, consider it a fault
y_pred_ensemble = ((y_pred_rf == 1) | (y_pred_iso_binary == 1)).astype(int)
prec_ens, rec_ens, f1_ens, _ = precision_recall_fscore_support(
    y_test, y_pred_ensemble, average='binary', zero_division=0
)
print(f"      Precision: {prec_ens:.3f}")
print(f"      Recall:    {rec_ens:.3f}")
print(f"      F1-Score:  {f1_ens:.3f}")

# Results Summary
print("\n" + "="*80)
print("EVALUATION RESULTS")
print("="*80)

print("\n┌──────────────────────────┬───────────┬─────────┬──────────┐")
print("│ Model                    │ Precision │  Recall │ F1-Score │")
print("├──────────────────────────┼───────────┼─────────┼──────────┤")
print(f"│ Random Forest            │   {prec_rf:.3f}   │  {rec_rf:.3f}  │  {f1_rf:.3f}   │")
print(f"│ Isolation Forest         │   {prec_iso:.3f}   │  {rec_iso:.3f}  │  {f1_iso:.3f}   │")
print(f"│ Ensemble (RF + ISO)      │   {prec_ens:.3f}   │  {rec_ens:.3f}  │  {f1_ens:.3f}   │")
print("└──────────────────────────┴───────────┴─────────┴──────────┘")

# Best model
best_model = max(
    [('Random Forest', f1_rf), ('Isolation Forest', f1_iso), ('Ensemble', f1_ens)],
    key=lambda x: x[1]
)
print(f"\n🏆 Best Performing Model: {best_model[0]} (F1={best_model[1]:.3f})")

# Confusion Matrix for Random Forest
cm = confusion_matrix(y_test, y_pred_rf)
tn, fp, fn, tp = cm.ravel()

print(f"\nConfusion Matrix (Random Forest):")
print("┌─────────────────┬──────────────────────┐")
print("│                 │    Predicted         │")
print("├─────────────────┼──────────┬───────────┤")
print("│                 │  Fault   │  Normal   │")
print("├─────────────────┼──────────┼───────────┤")
print(f"│ Actual Fault    │   {tp:4d}   │   {fn:4d}    │ ← Recall: {tp/(tp+fn):.1%}")
print(f"│ Actual Normal   │   {fp:4d}   │   {tn:4d}    │")
print("└─────────────────┴──────────┴───────────┘")
print(f"                      ↑")
print(f"                 Precision: {tp/(tp+fp):.1%}")

accuracy = (tp + tn) / (tp + tn + fp + fn)
print(f"\n📊 Model Performance Metrics:")
print(f"   • Accuracy:        {accuracy:.1%} (Overall correctness)")
print(f"   • True Positives:  {tp} (Correctly detected faults)")
print(f"   • False Positives: {fp} (False alarms)")
print(f"   • False Negatives: {fn} (Missed faults)")
print(f"   • True Negatives:  {tn} (Correctly identified normal)")

# Early detection capability
print(f"\n⏱️  Early Detection Analysis:")
fault_data = df_hosts[df_hosts['failed'] == True].copy()
if len(fault_data) > 0:
    fault_types = fault_data['fault_type'].unique()
    for ft in fault_types:
        if ft != 'NONE':
            ft_data = fault_data[fault_data['fault_type'] == ft]
            first_occurrence = ft_data['timestamp'].min()
            print(f"   • {ft}:")
            print(f"       First occurrence: t={first_occurrence:.0f}s")
            print(f"       Duration: {ft_data['timestamp'].max() - first_occurrence:.0f}s")

print("\n" + "="*80)
print("✅ TRAINING COMPLETE!")
print("="*80)
print(f"\n📦 Models saved to: models/")
print("   • random_forest.pkl      (Supervised classifier)")
print("   • isolation_forest.pkl   (Unsupervised anomaly detector)")
print("   • scaler.pkl             (Feature normalizer)")
print("\n💡 Next Steps:")
print("   1. Use these models for real-time fault detection")
print("   2. Integrate with datacenter monitoring systems")
print("   3. Fine-tune thresholds based on production data")
print("   4. Implement automated alerting based on predictions")
