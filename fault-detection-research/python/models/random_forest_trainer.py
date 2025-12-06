"""Random Forest classifier for fault detection."""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, precision_recall_fscore_support
import joblib


def train_random_forest(X_train, y_train, X_test, y_test, output_path):
    """
    Train a Random Forest classifier for fault detection.

    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        output_path: Path to save the trained model

    Returns:
        Path to the saved model
    """
    print("  Initializing Random Forest...")

    # Create model with balanced class weights
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
        verbose=0
    )

    print("  Training...")
    model.fit(X_train, y_train)

    print("  Evaluating...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # Calculate metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average='binary', zero_division=0
    )

    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1-Score:  {f1:.3f}")

    # Feature importance
    feature_importance = model.feature_importances_
    print(f"  Top feature importance: {feature_importance.max():.3f}")

    # Save model
    joblib.dump(model, output_path)

    return output_path
