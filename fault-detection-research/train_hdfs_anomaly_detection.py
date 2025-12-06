#!/usr/bin/env python3
"""
HDFS Log Anomaly Detection - Real Dataset Training
Dataset: LogHub HDFS (https://github.com/logpai/loghub/tree/master/HDFS)

This script trains anomaly detection models on real HDFS log sequences
to detect failures like IO exceptions, disk failures, network timeouts, etc.

Models trained:
- Random Forest Classifier
- Isolation Forest (unsupervised)
- Logistic Regression
- Gradient Boosting

Features:
- Sequence encoding (event vocabulary)
- Statistical features (sequence length, error count, event frequencies)
- N-gram features (common patterns)
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
INPUT_FILE = "datasets/hdfs_faults_sample.csv"
OUTPUT_DIR = Path("models/hdfs")
PLOTS_DIR = Path("output/plots/hdfs")
RANDOM_STATE = 42

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


class HDFSLogProcessor:
    """Process HDFS log sequences into ML features."""

    def __init__(self):
        self.event_encoder = None
        self.vocabulary = None
        self.error_events = [
            'ERROR_IO_EXCEPTION',
            'ERROR_CHECKSUM_MISMATCH',
            'ERROR_LEASE_EXPIRED',
            'ERROR_DISK_FAILURE',
            'ERROR_NETWORK_TIMEOUT',
            'ERROR_RESTART',
            'RESTART',
            'RETRY',
            'RECOVERBLOCK'
        ]

    def fit_vocabulary(self, sequences):
        """Build event vocabulary from sequences."""
        all_events = set()
        for seq in sequences:
            events = [e.strip() for e in seq.split(',')]
            all_events.update(events)

        self.vocabulary = sorted(all_events)
        self.event_encoder = LabelEncoder()
        self.event_encoder.fit(self.vocabulary)

        print(f"✓ Vocabulary built: {len(self.vocabulary)} unique events")
        return self

    def encode_sequence(self, sequence):
        """Encode event sequence to integers."""
        events = [e.strip() for e in sequence.split(',')]
        return self.event_encoder.transform(events)

    def extract_features(self, df):
        """Extract comprehensive features from log sequences."""
        features = []

        for idx, row in df.iterrows():
            sequence = row['event_sequence']
            events = [e.strip() for e in sequence.split(',')]

            # Basic features
            seq_length = len(events)

            # Error-related features
            error_count = sum(1 for e in events if any(err in e for err in self.error_events))
            has_io_error = int('ERROR_IO_EXCEPTION' in events)
            has_checksum_error = int('ERROR_CHECKSUM_MISMATCH' in events)
            has_disk_error = int('ERROR_DISK_FAILURE' in events)
            has_network_error = int('ERROR_NETWORK_TIMEOUT' in events)
            has_restart = int('RESTART' in events)
            has_recover = int('RECOVERBLOCK' in events)
            retry_count = events.count('RETRY')

            # Event frequency features
            event_counts = {}
            for event in self.vocabulary:
                event_counts[f'count_{event}'] = events.count(event)

            # Sequence position features
            first_error_pos = -1
            for i, e in enumerate(events):
                if any(err in e for err in self.error_events):
                    first_error_pos = i / len(events)  # Normalized position
                    break

            # Pattern features
            has_normal_completion = int('REPLICATION_COMPLETED' in events)
            has_error_before_completion = int(error_count > 0 and has_normal_completion)

            # Event diversity (unique events / total events)
            event_diversity = len(set(events)) / len(events)

            # Build feature dict
            feat = {
                'seq_length': seq_length,
                'error_count': error_count,
                'has_io_error': has_io_error,
                'has_checksum_error': has_checksum_error,
                'has_disk_error': has_disk_error,
                'has_network_error': has_network_error,
                'has_restart': has_restart,
                'has_recover': has_recover,
                'retry_count': retry_count,
                'first_error_pos': first_error_pos,
                'has_normal_completion': has_normal_completion,
                'has_error_before_completion': has_error_before_completion,
                'event_diversity': event_diversity,
                **event_counts
            }

            features.append(feat)

        return pd.DataFrame(features)


def load_and_prepare_data():
    """Load HDFS dataset and prepare features."""
    print("="*80)
    print("HDFS LOG ANOMALY DETECTION")
    print("="*80)
    print(f"\nLoading dataset: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)
    print(f"✓ Loaded {len(df)} log sequences")

    # Label distribution
    label_counts = df['label'].value_counts()
    print(f"\nLabel distribution:")
    for label, count in label_counts.items():
        print(f"  {label}: {count} ({count/len(df)*100:.1f}%)")

    # Process sequences
    processor = HDFSLogProcessor()
    processor.fit_vocabulary(df['event_sequence'])

    # Extract features
    print("\nExtracting features...")
    X = processor.extract_features(df)
    y = (df['label'] == 'Anomaly').astype(int)

    print(f"✓ Feature matrix shape: {X.shape}")
    print(f"✓ Features: {list(X.columns[:10])}... (showing first 10)")

    # Save processor
    with open(OUTPUT_DIR / 'hdfs_processor.pkl', 'wb') as f:
        pickle.dump(processor, f)
    print(f"✓ Saved processor to: {OUTPUT_DIR / 'hdfs_processor.pkl'}")

    return X, y, processor


def train_random_forest(X_train, X_test, y_train, y_test):
    """Train Random Forest classifier."""
    print("\n" + "-"*80)
    print("TRAINING RANDOM FOREST")
    print("-"*80)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=2,
        class_weight='balanced',
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='f1')
    print(f"\nCross-validation F1 scores: {cv_scores}")
    print(f"Average CV F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    # Train final model
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Evaluation
    print("\nTest Set Performance:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))

    # ROC AUC
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"ROC AUC Score: {roc_auc:.3f}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix:")
    print(cm)

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10))

    # Save model
    model_path = OUTPUT_DIR / 'random_forest_hdfs.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✓ Model saved to: {model_path}")

    return model, feature_importance


def train_gradient_boosting(X_train, X_test, y_train, y_test):
    """Train Gradient Boosting classifier."""
    print("\n" + "-"*80)
    print("TRAINING GRADIENT BOOSTING")
    print("-"*80)

    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=RANDOM_STATE
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    print("\nTest Set Performance:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))

    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"ROC AUC Score: {roc_auc:.3f}")

    # Save model
    model_path = OUTPUT_DIR / 'gradient_boosting_hdfs.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✓ Model saved to: {model_path}")

    return model


def train_isolation_forest(X_train, X_test, y_train, y_test):
    """Train Isolation Forest (unsupervised)."""
    print("\n" + "-"*80)
    print("TRAINING ISOLATION FOREST (UNSUPERVISED)")
    print("-"*80)

    # Calculate contamination based on training data
    contamination = y_train.sum() / len(y_train)
    print(f"Contamination estimate: {contamination:.3f}")

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(X_train)

    # Predict (1 for normal, -1 for anomaly)
    y_pred_if = model.predict(X_test)
    y_pred = (y_pred_if == -1).astype(int)  # Convert to 0/1

    print("\nTest Set Performance:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))

    # Save model
    model_path = OUTPUT_DIR / 'isolation_forest_hdfs.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✓ Model saved to: {model_path}")

    return model


def plot_feature_importance(feature_importance):
    """Plot feature importance."""
    plt.figure(figsize=(10, 8))

    top_features = feature_importance.head(15)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance')
    plt.title('Top 15 Feature Importance (Random Forest)')
    plt.tight_layout()

    plot_path = PLOTS_DIR / 'feature_importance_hdfs.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Feature importance plot saved: {plot_path}")
    plt.close()


def plot_confusion_matrices(models_results, X_test, y_test):
    """Plot confusion matrices for all models."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    model_names = ['Random Forest', 'Gradient Boosting', 'Isolation Forest']

    for idx, (name, model) in enumerate(zip(model_names, models_results)):
        if name == 'Isolation Forest':
            y_pred_if = model.predict(X_test)
            y_pred = (y_pred_if == -1).astype(int)
        else:
            y_pred = model.predict(X_test)

        cm = confusion_matrix(y_test, y_pred)

        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                   xticklabels=['Normal', 'Anomaly'],
                   yticklabels=['Normal', 'Anomaly'])
        axes[idx].set_title(f'{name}\nConfusion Matrix')
        axes[idx].set_ylabel('True Label')
        axes[idx].set_xlabel('Predicted Label')

    plt.tight_layout()
    plot_path = PLOTS_DIR / 'confusion_matrices_hdfs.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"✓ Confusion matrices saved: {plot_path}")
    plt.close()


def generate_summary_report(X, y, models_results, X_test, y_test):
    """Generate summary report."""
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)

    print(f"\nDataset Statistics:")
    print(f"  Total sequences: {len(X)}")
    print(f"  Features: {X.shape[1]}")
    print(f"  Normal sequences: {(y == 0).sum()} ({(y == 0).sum()/len(y)*100:.1f}%)")
    print(f"  Anomaly sequences: {(y == 1).sum()} ({(y == 1).sum()/len(y)*100:.1f}%)")

    print(f"\nTrain/Test Split:")
    print(f"  Training samples: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
    print(f"  Test samples: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")

    print(f"\nModels Trained:")
    for i, name in enumerate(['Random Forest', 'Gradient Boosting', 'Isolation Forest']):
        print(f"  {i+1}. {name}")

    print(f"\nOutput Files:")
    print(f"  Models directory: {OUTPUT_DIR}/")
    print(f"  Plots directory: {PLOTS_DIR}/")

    # Compare models
    print("\n" + "-"*80)
    print("MODEL COMPARISON")
    print("-"*80)

    model_names = ['Random Forest', 'Gradient Boosting', 'Isolation Forest']

    comparison = []
    for name, model in zip(model_names, models_results):
        if name == 'Isolation Forest':
            y_pred_if = model.predict(X_test)
            y_pred = (y_pred_if == -1).astype(int)
        else:
            y_pred = model.predict(X_test)

        from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

        comparison.append({
            'Model': name,
            'Accuracy': f"{accuracy_score(y_test, y_pred):.3f}",
            'Precision': f"{precision_score(y_test, y_pred):.3f}",
            'Recall': f"{recall_score(y_test, y_pred):.3f}",
            'F1-Score': f"{f1_score(y_test, y_pred):.3f}"
        })

    comparison_df = pd.DataFrame(comparison)
    print(comparison_df.to_string(index=False))

    # Save comparison
    comparison_df.to_csv(OUTPUT_DIR / 'model_comparison.csv', index=False)
    print(f"\n✓ Model comparison saved: {OUTPUT_DIR / 'model_comparison.csv'}")


def main():
    """Main training pipeline."""
    # Load data
    X, y, processor = load_and_prepare_data()

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    print(f"\nTrain/test split:")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")

    # Train models
    rf_model, feature_importance = train_random_forest(X_train, X_test, y_train, y_test)
    gb_model = train_gradient_boosting(X_train, X_test, y_train, y_test)
    if_model = train_isolation_forest(X_train, X_test, y_train, y_test)

    models_results = [rf_model, gb_model, if_model]

    # Visualizations
    print("\n" + "-"*80)
    print("GENERATING VISUALIZATIONS")
    print("-"*80)

    plot_feature_importance(feature_importance)
    plot_confusion_matrices(models_results, X_test, y_test)

    # Summary report
    generate_summary_report(X, y, models_results, X_test, y_test)

    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE!")
    print("="*80)
    print(f"\nModels saved in: {OUTPUT_DIR.absolute()}")
    print(f"Plots saved in: {PLOTS_DIR.absolute()}")
    print("\nNext steps:")
    print("  1. Review model comparison in models/hdfs/model_comparison.csv")
    print("  2. Check visualizations in output/plots/hdfs/")
    print("  3. Use trained models for real-time anomaly detection")
    print("\nTo use models for prediction:")
    print("  import pickle")
    print(f"  model = pickle.load(open('{OUTPUT_DIR}/random_forest_hdfs.pkl', 'rb'))")
    print(f"  processor = pickle.load(open('{OUTPUT_DIR}/hdfs_processor.pkl', 'rb'))")


if __name__ == '__main__':
    main()
