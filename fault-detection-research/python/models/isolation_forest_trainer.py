"""Isolation Forest for anomaly-based fault detection."""

import numpy as np
from sklearn.ensemble import IsolationForest
import joblib


def train_isolation_forest(X_train, output_path):
    """
    Train an Isolation Forest for unsupervised anomaly detection.

    Args:
        X_train: Training features
        output_path: Path to save the trained model

    Returns:
        Path to the saved model
    """
    print("  Initializing Isolation Forest...")

    # Create model
    # contamination is the expected proportion of anomalies
    model = IsolationForest(
        n_estimators=100,
        contamination=0.15,  # Expect 15% anomalies
        max_samples='auto',
        random_state=42,
        n_jobs=-1,
        verbose=0
    )

    print("  Training...")
    model.fit(X_train)

    print("  Evaluating...")
    # Predict on training data
    predictions = model.predict(X_train)
    anomaly_score = model.decision_function(X_train)

    # -1 = anomaly, 1 = normal
    n_anomalies = (predictions == -1).sum()
    anomaly_rate = n_anomalies / len(X_train)

    print(f"  Detected anomalies: {n_anomalies} ({100*anomaly_rate:.2f}%)")
    print(f"  Average anomaly score: {anomaly_score.mean():.3f}")

    # Save model
    joblib.dump(model, output_path)

    return output_path
