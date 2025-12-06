"""XGBoost classifier for fault detection."""

import numpy as np
import xgboost as xgb
from sklearn.metrics import precision_recall_fscore_support
import joblib


def train_xgboost(X_train, y_train, X_test, y_test, output_path):
    """
    Train an XGBoost classifier for fault detection.

    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        output_path: Path to save the trained model

    Returns:
        Path to the saved model
    """
    print("  Initializing XGBoost...")

    # Calculate scale_pos_weight for imbalanced data
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    # Create model
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )

    print("  Training...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

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

    # Save model
    joblib.dump(model, output_path)

    return output_path
