#!/usr/bin/env python3
"""
Multi-Modal Fault Detection System
Combines Telemetry-based and Log-based detection for comprehensive fault prediction

Features:
- Telemetry features: sliding windows, statistical aggregations
- Log features: event patterns, error indicators
- Fusion strategies: weighted average, voting, stacking
- Early detection analysis with lead time measurement
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_fscore_support
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Paths
DATA_DIR = Path("datasets/multimodal")
OUTPUT_DIR = Path("models/multimodal")
PLOTS_DIR = Path("output/plots/multimodal")
RANDOM_STATE = 42

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


class TelemetryFeatureExtractor:
    """Extract features from telemetry data."""

    def __init__(self):
        self.scaler = StandardScaler()

    def extract_features(self, df_telemetry):
        """Extract telemetry features with sliding windows."""
        print("Extracting telemetry features...")

        features_list = []

        # Group by host
        for host_id in df_telemetry['host_id'].unique():
            df_host = df_telemetry[df_telemetry['host_id'] == host_id].sort_values('timestamp')

            for idx in range(len(df_host)):
                row = df_host.iloc[idx]

                # Current values
                feat = {
                    'host_id': row['host_id'],
                    'timestamp': row['timestamp'],
                    'cpu_current': row['cpu_percent'],
                    'memory_current': row['memory_percent'],
                    'disk_io_current': row['disk_io_percent'],
                    'temperature_current': row['temperature_celsius'],
                    'power_current': row['power_watts'],
                    'network_latency_current': row['network_latency_ms'],
                    'packet_loss_current': row['packet_loss_percent'],
                    'error_count_current': row['error_count']
                }

                # Sliding windows (last 5, 10, 20 samples)
                for window_size, window_name in [(5, '5'), (10, '10'), (20, '20')]:
                    start_idx = max(0, idx - window_size)
                    window_data = df_host.iloc[start_idx:idx+1]

                    if len(window_data) > 0:
                        feat[f'cpu_mean_{window_name}'] = window_data['cpu_percent'].mean()
                        feat[f'cpu_std_{window_name}'] = window_data['cpu_percent'].std()
                        feat[f'cpu_max_{window_name}'] = window_data['cpu_percent'].max()

                        feat[f'memory_mean_{window_name}'] = window_data['memory_percent'].mean()
                        feat[f'memory_trend_{window_name}'] = window_data['memory_percent'].diff().mean()

                        feat[f'disk_io_mean_{window_name}'] = window_data['disk_io_percent'].mean()
                        feat[f'disk_io_max_{window_name}'] = window_data['disk_io_percent'].max()

                        feat[f'temp_mean_{window_name}'] = window_data['temperature_celsius'].mean()
                        feat[f'temp_increase_{window_name}'] = window_data['temperature_celsius'].iloc[-1] - window_data['temperature_celsius'].iloc[0] if len(window_data) > 1 else 0

                        feat[f'power_mean_{window_name}'] = window_data['power_watts'].mean()

                        feat[f'latency_mean_{window_name}'] = window_data['network_latency_ms'].mean()
                        feat[f'latency_p95_{window_name}'] = window_data['network_latency_ms'].quantile(0.95) if len(window_data) > 1 else window_data['network_latency_ms'].iloc[0]

                        feat[f'packet_loss_sum_{window_name}'] = window_data['packet_loss_percent'].sum()
                        feat[f'error_sum_{window_name}'] = window_data['error_count'].sum()
                    else:
                        # Fill with current values
                        for metric in ['cpu', 'memory', 'disk_io', 'temp', 'power', 'latency', 'packet_loss', 'error']:
                            feat[f'{metric}_mean_{window_name}'] = feat[f'{metric.replace("_", "")}_current'] if f'{metric.replace("_", "")}_current' in feat else 0

                # Labels
                feat['label'] = 1 if (row['early_warning'] or row['fault_active']) else 0
                feat['fault_type'] = row['fault_type']

                features_list.append(feat)

        return pd.DataFrame(features_list)


class LogFeatureExtractor:
    """Extract features from log sequences (similar to HDFS processor)."""

    def __init__(self):
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

    def fit_vocabulary(self, df_logs):
        """Build event vocabulary."""
        all_events = set()
        for seq in df_logs['event_sequence']:
            events = [e.strip() for e in seq.split(',')]
            all_events.update(events)
        self.vocabulary = sorted(all_events)
        return self

    def extract_features(self, df_logs):
        """Extract log features."""
        print("Extracting log features...")

        features_list = []

        for idx, row in df_logs.iterrows():
            sequence = row['event_sequence']
            events = [e.strip() for e in sequence.split(',')]

            feat = {
                'host_id': row['host_id'],
                'timestamp': row['timestamp'],
                'seq_length': len(events),
                'error_count': sum(1 for e in events if any(err in e for err in self.error_events)),
                'has_io_error': int('ERROR_IO_EXCEPTION' in events),
                'has_checksum_error': int('ERROR_CHECKSUM_MISMATCH' in events),
                'has_disk_error': int('ERROR_DISK_FAILURE' in events),
                'has_network_error': int('ERROR_NETWORK_TIMEOUT' in events),
                'has_restart': int('RESTART' in events),
                'has_recover': int('RECOVERBLOCK' in events),
                'retry_count': events.count('RETRY'),
                'has_normal_completion': int('REPLICATION_COMPLETED' in events),
                'event_diversity': len(set(events)) / len(events),
                'label': 1 if row['label'] == 'Anomaly' else 0,
                'fault_type': row['fault_type']
            }

            features_list.append(feat)

        return pd.DataFrame(features_list)


class MultiModalFusionDetector:
    """Combine telemetry and log-based detection."""

    def __init__(self):
        self.telemetry_model = None
        self.log_model = None
        self.fusion_model = None
        self.telemetry_scaler = StandardScaler()
        self.log_scaler = StandardScaler()

    def train(self, X_telemetry_train, X_log_train, y_train):
        """Train individual models and fusion model."""
        print("\n" + "="*80)
        print("TRAINING MULTI-MODAL DETECTION SYSTEM")
        print("="*80)

        # Train telemetry model
        print("\n[1/3] Training Telemetry Model (Random Forest)...")
        self.telemetry_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            class_weight='balanced',
            random_state=RANDOM_STATE,
            n_jobs=-1
        )

        X_telemetry_scaled = self.telemetry_scaler.fit_transform(X_telemetry_train)
        self.telemetry_model.fit(X_telemetry_scaled, y_train)
        print("✓ Telemetry model trained")

        # Train log model
        print("\n[2/3] Training Log Model (Gradient Boosting)...")
        self.log_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=RANDOM_STATE
        )

        X_log_scaled = self.log_scaler.fit_transform(X_log_train)
        self.log_model.fit(X_log_scaled, y_train)
        print("✓ Log model trained")

        # Train fusion model (stacking)
        print("\n[3/3] Training Fusion Model (Stacking)...")
        telemetry_pred = self.telemetry_model.predict_proba(X_telemetry_scaled)[:, 1]
        log_pred = self.log_model.predict_proba(X_log_scaled)[:, 1]

        X_fusion = np.column_stack([telemetry_pred, log_pred])

        self.fusion_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        self.fusion_model.fit(X_fusion, y_train)
        print("✓ Fusion model trained")

    def predict(self, X_telemetry, X_log):
        """Predict using fusion of both modalities."""
        X_telemetry_scaled = self.telemetry_scaler.transform(X_telemetry)
        X_log_scaled = self.log_scaler.transform(X_log)

        telemetry_pred = self.telemetry_model.predict_proba(X_telemetry_scaled)[:, 1]
        log_pred = self.log_model.predict_proba(X_log_scaled)[:, 1]

        X_fusion = np.column_stack([telemetry_pred, log_pred])
        fusion_pred = self.fusion_model.predict(X_fusion)
        fusion_proba = self.fusion_model.predict_proba(X_fusion)[:, 1]

        return {
            'telemetry_proba': telemetry_pred,
            'log_proba': log_pred,
            'fusion_pred': fusion_pred,
            'fusion_proba': fusion_proba
        }


def analyze_early_detection(df_telemetry, df_faults, predictions, fusion_proba):
    """Analyze early detection capability."""
    print("\n" + "="*80)
    print("EARLY DETECTION ANALYSIS")
    print("="*80)

    early_detections = []

    for idx, fault in df_faults.iterrows():
        host_id = fault['host_id']
        fault_start = fault['start_time']
        early_warning_start = fault['early_warning_start']
        fault_type = fault['fault_type']

        # Find telemetry in early warning period
        mask = (
            (df_telemetry['host_id'] == host_id) &
            (df_telemetry['timestamp'] >= early_warning_start) &
            (df_telemetry['timestamp'] < fault_start)
        )

        early_window = df_telemetry[mask]

        if len(early_window) == 0:
            continue

        # Find first detection in early warning window
        first_detection_time = None
        for i, row in early_window.iterrows():
            idx_in_df = df_telemetry.index.get_loc(i)
            if predictions[idx_in_df] == 1:
                first_detection_time = row['timestamp']
                break

        if first_detection_time is not None:
            lead_time = fault_start - first_detection_time
            early_detections.append({
                'host_id': host_id,
                'fault_type': fault_type,
                'fault_start_time': fault_start,
                'first_detection_time': first_detection_time,
                'lead_time_seconds': lead_time,
                'early_warning_duration': fault_start - early_warning_start
            })

    if len(early_detections) > 0:
        df_early = pd.DataFrame(early_detections)

        print(f"\n✓ Early detections achieved: {len(df_early)} out of {len(df_faults)} faults")
        print(f"\nLead Time Statistics:")
        print(f"  Average: {df_early['lead_time_seconds'].mean():.1f} seconds ({df_early['lead_time_seconds'].mean()/60:.1f} minutes)")
        print(f"  Median: {df_early['lead_time_seconds'].median():.1f} seconds")
        print(f"  Best (max): {df_early['lead_time_seconds'].max():.1f} seconds ({df_early['lead_time_seconds'].max()/60:.1f} minutes)")
        print(f"  Worst (min): {df_early['lead_time_seconds'].min():.1f} seconds")

        print(f"\nEarly Detection by Fault Type:")
        for fault_type in df_early['fault_type'].unique():
            subset = df_early[df_early['fault_type'] == fault_type]
            print(f"  {fault_type}:")
            print(f"    Count: {len(subset)}")
            print(f"    Avg lead time: {subset['lead_time_seconds'].mean():.1f}s ({subset['lead_time_seconds'].mean()/60:.1f}min)")

        return df_early
    else:
        print("\n⚠️  No early detections achieved")
        return pd.DataFrame()


def plot_results(results, df_early_detection):
    """Generate comprehensive visualizations."""
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)

    # 1. Model comparison
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    models = ['Telemetry Only', 'Log Only', 'Multi-Modal Fusion']
    accuracies = [results['telemetry']['accuracy'], results['log']['accuracy'], results['fusion']['accuracy']]
    f1_scores = [results['telemetry']['f1'], results['log']['f1'], results['fusion']['f1']]
    recalls = [results['telemetry']['recall'], results['log']['recall'], results['fusion']['recall']]

    x = np.arange(len(models))
    width = 0.25

    axes[0].bar(x - width, accuracies, width, label='Accuracy', color='skyblue')
    axes[0].bar(x, f1_scores, width, label='F1-Score', color='lightcoral')
    axes[0].bar(x + width, recalls, width, label='Recall', color='lightgreen')
    axes[0].set_ylabel('Score')
    axes[0].set_title('Model Performance Comparison')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models, rotation=15, ha='right')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)

    # 2. Confusion matrix for fusion model
    cm = results['fusion']['confusion_matrix']
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[1],
               xticklabels=['Normal', 'Fault'],
               yticklabels=['Normal', 'Fault'])
    axes[1].set_title('Multi-Modal Fusion\nConfusion Matrix')
    axes[1].set_ylabel('True Label')
    axes[1].set_xlabel('Predicted Label')

    # 3. Early detection lead times
    if len(df_early_detection) > 0:
        lead_times = df_early_detection['lead_time_seconds'] / 60  # Convert to minutes
        axes[2].hist(lead_times, bins=15, color='green', alpha=0.7, edgecolor='black')
        axes[2].axvline(lead_times.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {lead_times.mean():.1f}min')
        axes[2].set_xlabel('Lead Time (minutes)')
        axes[2].set_ylabel('Frequency')
        axes[2].set_title('Early Detection Lead Times')
        axes[2].legend()
        axes[2].grid(axis='y', alpha=0.3)
    else:
        axes[2].text(0.5, 0.5, 'No Early Detections', ha='center', va='center', fontsize=14)
        axes[2].set_title('Early Detection Lead Times')

    plt.tight_layout()
    plot_path = PLOTS_DIR / 'multimodal_results.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"✓ Results plot saved: {plot_path}")
    plt.close()

    # 4. Early detection by fault type
    if len(df_early_detection) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))

        fault_types = df_early_detection.groupby('fault_type')['lead_time_seconds'].agg(['mean', 'count'])
        fault_types = fault_types.sort_values('mean', ascending=False)

        colors = plt.cm.viridis(np.linspace(0, 1, len(fault_types)))
        bars = ax.barh(range(len(fault_types)), fault_types['mean'] / 60, color=colors)

        ax.set_yticks(range(len(fault_types)))
        ax.set_yticklabels(fault_types.index)
        ax.set_xlabel('Average Lead Time (minutes)')
        ax.set_title('Early Detection Lead Time by Fault Type')
        ax.grid(axis='x', alpha=0.3)

        # Add count labels
        for i, (idx, row) in enumerate(fault_types.iterrows()):
            ax.text(row['mean']/60 + 0.1, i, f"n={int(row['count'])}", va='center')

        plt.tight_layout()
        plot_path = PLOTS_DIR / 'early_detection_by_fault_type.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"✓ Fault type analysis saved: {plot_path}")
        plt.close()


def main():
    """Main training and evaluation pipeline."""
    print("="*80)
    print("MULTI-MODAL FAULT DETECTION SYSTEM")
    print("="*80)

    # Load datasets
    print("\nLoading datasets...")
    df_telemetry = pd.read_csv(DATA_DIR / 'telemetry_multimodal.csv')
    df_logs = pd.read_csv(DATA_DIR / 'logs_multimodal.csv')
    with open(DATA_DIR / 'fault_events_multimodal.json', 'r') as f:
        df_faults = pd.DataFrame(json.load(f))

    print(f"✓ Loaded {len(df_telemetry):,} telemetry samples")
    print(f"✓ Loaded {len(df_logs):,} log sequences")
    print(f"✓ Loaded {len(df_faults)} fault events")

    # Extract features
    telemetry_extractor = TelemetryFeatureExtractor()
    df_telemetry_features = telemetry_extractor.extract_features(df_telemetry)

    log_extractor = LogFeatureExtractor()
    log_extractor.fit_vocabulary(df_logs)
    df_log_features = log_extractor.extract_features(df_logs)

    print(f"\n✓ Extracted telemetry features: {df_telemetry_features.shape}")
    print(f"✓ Extracted log features: {df_log_features.shape}")

    # Merge features by host_id and timestamp (approximate matching for logs)
    # For each telemetry sample, find nearest log entry
    df_telemetry_features['log_idx'] = -1
    for idx, row in df_telemetry_features.iterrows():
        host_id = row['host_id']
        timestamp = row['timestamp']

        # Find logs for this host
        host_logs = df_log_features[df_log_features['host_id'] == host_id]

        if len(host_logs) > 0:
            # Find closest log by timestamp
            time_diffs = np.abs(host_logs['timestamp'] - timestamp)
            closest_log_idx = host_logs.iloc[time_diffs.argmin()].name
            df_telemetry_features.at[idx, 'log_idx'] = closest_log_idx

    # Prepare training data
    telemetry_feature_cols = [c for c in df_telemetry_features.columns
                              if c not in ['host_id', 'timestamp', 'label', 'fault_type', 'log_idx']]
    log_feature_cols = [c for c in df_log_features.columns
                        if c not in ['host_id', 'timestamp', 'label', 'fault_type']]

    X_telemetry = df_telemetry_features[telemetry_feature_cols].fillna(0)
    X_log_matched = []

    for idx, row in df_telemetry_features.iterrows():
        log_idx = row['log_idx']
        if log_idx >= 0 and log_idx in df_log_features.index:
            X_log_matched.append(df_log_features.loc[log_idx, log_feature_cols].values)
        else:
            # Use default (all zeros for no log)
            X_log_matched.append(np.zeros(len(log_feature_cols)))

    X_log = pd.DataFrame(X_log_matched, columns=log_feature_cols).fillna(0)
    y = df_telemetry_features['label'].values

    print(f"\n✓ Prepared training data:")
    print(f"  Telemetry features: {X_telemetry.shape}")
    print(f"  Log features: {X_log.shape}")
    print(f"  Labels: {y.shape}, positive: {y.sum()} ({y.sum()/len(y)*100:.1f}%)")

    # Train/test split
    X_telemetry_train, X_telemetry_test, X_log_train, X_log_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X_telemetry, X_log, y, df_telemetry_features.index,
        test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    print(f"\nTrain/test split:")
    print(f"  Training: {len(y_train):,} samples")
    print(f"  Testing: {len(y_test):,} samples")

    # Train multi-modal detector
    detector = MultiModalFusionDetector()
    detector.train(X_telemetry_train, X_log_train, y_train)

    # Evaluate
    print("\n" + "="*80)
    print("EVALUATION")
    print("="*80)

    predictions = detector.predict(X_telemetry_test, X_log_test)

    # Telemetry-only performance
    y_pred_telemetry = (predictions['telemetry_proba'] > 0.5).astype(int)
    precision_t, recall_t, f1_t, _ = precision_recall_fscore_support(y_test, y_pred_telemetry, average='binary')

    print("\n[Telemetry Only]")
    print(classification_report(y_test, y_pred_telemetry, target_names=['Normal', 'Fault']))

    # Log-only performance
    y_pred_log = (predictions['log_proba'] > 0.5).astype(int)
    precision_l, recall_l, f1_l, _ = precision_recall_fscore_support(y_test, y_pred_log, average='binary')

    print("\n[Log Only]")
    print(classification_report(y_test, y_pred_log, target_names=['Normal', 'Fault']))

    # Fusion performance
    y_pred_fusion = predictions['fusion_pred']
    precision_f, recall_f, f1_f, _ = precision_recall_fscore_support(y_test, y_pred_fusion, average='binary')

    print("\n[Multi-Modal Fusion]")
    print(classification_report(y_test, y_pred_fusion, target_names=['Normal', 'Fault']))

    # Store results
    results = {
        'telemetry': {
            'accuracy': (y_pred_telemetry == y_test).mean(),
            'precision': precision_t,
            'recall': recall_t,
            'f1': f1_t
        },
        'log': {
            'accuracy': (y_pred_log == y_test).mean(),
            'precision': precision_l,
            'recall': recall_l,
            'f1': f1_l
        },
        'fusion': {
            'accuracy': (y_pred_fusion == y_test).mean(),
            'precision': precision_f,
            'recall': recall_f,
            'f1': f1_f,
            'confusion_matrix': confusion_matrix(y_test, y_pred_fusion)
        }
    }

    # Early detection analysis
    full_predictions = detector.predict(X_telemetry, X_log)
    df_early_detection = analyze_early_detection(
        df_telemetry_features,
        df_faults,
        full_predictions['fusion_pred'],
        full_predictions['fusion_proba']
    )

    # Plot results
    plot_results(results, df_early_detection)

    # Save models
    print("\n" + "="*80)
    print("SAVING MODELS")
    print("="*80)

    with open(OUTPUT_DIR / 'multimodal_detector.pkl', 'wb') as f:
        pickle.dump(detector, f)
    print(f"✓ Multi-modal detector saved")

    with open(OUTPUT_DIR / 'telemetry_extractor.pkl', 'wb') as f:
        pickle.dump(telemetry_extractor, f)
    print(f"✓ Telemetry extractor saved")

    with open(OUTPUT_DIR / 'log_extractor.pkl', 'wb') as f:
        pickle.dump(log_extractor, f)
    print(f"✓ Log extractor saved")

    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'dataset_stats': {
            'total_telemetry_samples': len(df_telemetry),
            'total_log_sequences': len(df_logs),
            'total_fault_events': len(df_faults),
            'positive_samples': int(y.sum()),
            'negative_samples': int((y == 0).sum())
        },
        'model_performance': {
            'telemetry_only': {k: float(v) if not isinstance(v, np.ndarray) else v.tolist()
                               for k, v in results['telemetry'].items()},
            'log_only': {k: float(v) if not isinstance(v, np.ndarray) else v.tolist()
                        for k, v in results['log'].items()},
            'fusion': {k: float(v) if not isinstance(v, np.ndarray) else v.tolist()
                      for k, v in results['fusion'].items()}
        },
        'early_detection': {
            'total_detections': len(df_early_detection),
            'avg_lead_time_seconds': float(df_early_detection['lead_time_seconds'].mean()) if len(df_early_detection) > 0 else 0,
            'max_lead_time_seconds': float(df_early_detection['lead_time_seconds'].max()) if len(df_early_detection) > 0 else 0,
            'min_lead_time_seconds': float(df_early_detection['lead_time_seconds'].min()) if len(df_early_detection) > 0 else 0
        }
    }

    with open(OUTPUT_DIR / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Summary saved")

    # Save early detection details
    if len(df_early_detection) > 0:
        df_early_detection.to_csv(OUTPUT_DIR / 'early_detection_results.csv', index=False)
        print(f"✓ Early detection results saved")

    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE")
    print("="*80)
    print(f"\nModels saved in: {OUTPUT_DIR.absolute()}")
    print(f"Plots saved in: {PLOTS_DIR.absolute()}")

    print(f"\nFinal Results:")
    print(f"  Telemetry Only: {results['telemetry']['f1']*100:.1f}% F1-score")
    print(f"  Log Only: {results['log']['f1']*100:.1f}% F1-score")
    print(f"  Multi-Modal Fusion: {results['fusion']['f1']*100:.1f}% F1-score")

    if len(df_early_detection) > 0:
        print(f"\nEarly Detection:")
        print(f"  Average lead time: {df_early_detection['lead_time_seconds'].mean()/60:.1f} minutes")
        print(f"  Best lead time: {df_early_detection['lead_time_seconds'].max()/60:.1f} minutes")


if __name__ == '__main__':
    main()
