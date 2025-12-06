#!/usr/bin/env python3
"""
Multi-Modal Fault Detection on REAL Datasets
Combines:
1. Machine Failure Data (3,000 sensor readings from industrial machines)
2. Incident Event Log (141,712 IT incident events from ServiceNow)

This demonstrates multi-modal fusion with:
- Telemetry: Temperature, pressure, vibration, humidity, power
- Events: Incident management process logs
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Paths
MACHINE_DATA_PATH = "/Users/maanalghamdi/Downloads/machine_failure_data.csv"
INCIDENT_DATA_PATH = "/Users/maanalghamdi/Downloads/incident_event_log.csv"
OUTPUT_DIR = Path("models/real_datasets")
PLOTS_DIR = Path("output/plots/real_datasets")
RANDOM_STATE = 42

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("MULTI-MODAL FAULT DETECTION - REAL DATASETS")
print("="*80)
print(f"\nDataset 1: Machine Failure Data (Industrial Sensors)")
print(f"Dataset 2: Incident Event Log (IT Service Management)")
print()


class MachineTelemetryProcessor:
    """Process machine sensor telemetry data."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.machine_encoder = LabelEncoder()

    def load_and_process(self, file_path):
        """Load and process machine failure data."""
        print("[1/2] Loading Machine Failure Data...")
        df = pd.read_csv(file_path)

        print(f"  ✓ Loaded {len(df):,} sensor readings")
        print(f"  ✓ Machines: {df['Machine_ID'].nunique()}")
        print(f"  ✓ Time range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")

        # Label distribution
        failure_count = df['Failure_Status'].sum()
        normal_count = len(df) - failure_count
        print(f"  ✓ Normal: {normal_count:,} ({normal_count/len(df)*100:.1f}%)")
        print(f"  ✓ Failures: {failure_count:,} ({failure_count/len(df)*100:.1f}%)")

        # Convert timestamp
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values(['Machine_ID', 'Timestamp']).reset_index(drop=True)

        # Encode machine ID
        df['Machine_ID_encoded'] = self.machine_encoder.fit_transform(df['Machine_ID'])

        return df

    def extract_features(self, df):
        """Extract features from machine telemetry."""
        print("\n  Extracting telemetry features...")

        features_list = []

        for machine_id in df['Machine_ID'].unique():
            df_machine = df[df['Machine_ID'] == machine_id].reset_index(drop=True)

            for idx in range(len(df_machine)):
                row = df_machine.iloc[idx]

                # Current values
                feat = {
                    'machine_id': row['Machine_ID_encoded'],
                    'temperature': row['Temperature'],
                    'pressure': row['Pressure'],
                    'vibration': row['Vibration_Level'],
                    'humidity': row['Humidity'],
                    'power': row['Power_Consumption']
                }

                # Sliding window features (last 5, 10 readings)
                for window_size in [5, 10]:
                    start_idx = max(0, idx - window_size)
                    window = df_machine.iloc[start_idx:idx+1]

                    if len(window) > 1:
                        feat[f'temp_mean_{window_size}'] = window['Temperature'].mean()
                        feat[f'temp_std_{window_size}'] = window['Temperature'].std()
                        feat[f'temp_trend_{window_size}'] = window['Temperature'].diff().mean()

                        feat[f'pressure_mean_{window_size}'] = window['Pressure'].mean()
                        feat[f'pressure_max_{window_size}'] = window['Pressure'].max()

                        feat[f'vibration_mean_{window_size}'] = window['Vibration_Level'].mean()
                        feat[f'vibration_max_{window_size}'] = window['Vibration_Level'].max()
                        feat[f'vibration_std_{window_size}'] = window['Vibration_Level'].std()

                        feat[f'humidity_mean_{window_size}'] = window['Humidity'].mean()
                        feat[f'power_mean_{window_size}'] = window['Power_Consumption'].mean()
                        feat[f'power_std_{window_size}'] = window['Power_Consumption'].std()
                    else:
                        # Use current values
                        for metric in ['temp', 'pressure', 'vibration', 'humidity', 'power']:
                            feat[f'{metric}_mean_{window_size}'] = feat.get(metric.replace('_', ''), 0)
                            feat[f'{metric}_std_{window_size}'] = 0
                            feat[f'{metric}_max_{window_size}'] = feat.get(metric.replace('_', ''), 0)

                # Label
                feat['failure_status'] = row['Failure_Status']

                features_list.append(feat)

        df_features = pd.DataFrame(features_list)
        print(f"  ✓ Extracted {len(df_features):,} feature vectors with {df_features.shape[1]-1} features")

        return df_features


class IncidentLogProcessor:
    """Process incident event log data."""

    def __init__(self):
        self.categorical_encoders = {}

    def load_and_process(self, file_path, sample_size=10000):
        """Load and process incident event log."""
        print("\n[2/2] Loading Incident Event Log...")
        df = pd.read_csv(file_path, nrows=sample_size)  # Sample for speed

        print(f"  ✓ Loaded {len(df):,} incident events (sampled)")
        print(f"  ✓ Unique incidents: {df['number'].nunique()}")

        # Parse timestamps
        date_columns = ['opened_at', 'sys_created_at', 'sys_updated_at', 'resolved_at', 'closed_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y %H:%M', errors='coerce')

        # Calculate incident metrics
        df['resolution_time'] = (df['resolved_at'] - df['opened_at']).dt.total_seconds() / 60  # minutes
        df['update_frequency'] = df['sys_mod_count'] / ((df['sys_updated_at'] - df['sys_created_at']).dt.total_seconds() / 3600 + 1)  # updates per hour

        # Binary label: SLA missed or high priority issues = "failure"
        df['incident_severity'] = ((df['made_sla'] == 'false') |
                                   (df['priority'].str.contains('1|2', na=False)) |
                                   (df['impact'].str.contains('1', na=False))).astype(int)

        print(f"  ✓ Normal incidents: {(df['incident_severity'] == 0).sum():,}")
        print(f"  ✓ Severe incidents: {(df['incident_severity'] == 1).sum():,}")

        return df

    def extract_features(self, df):
        """Extract features from incident log."""
        print("\n  Extracting incident log features...")

        # Encode categorical variables
        categorical_cols = ['incident_state', 'contact_type', 'category', 'impact', 'urgency', 'priority']

        for col in categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                df[f'{col}_encoded'] = le.fit_transform(df[col].fillna('Unknown').astype(str))
                self.categorical_encoders[col] = le

        # Select numerical and encoded features
        feature_cols = [
            'reassignment_count',
            'reopen_count',
            'sys_mod_count',
            'resolution_time',
            'update_frequency',
            'incident_state_encoded',
            'contact_type_encoded',
            'category_encoded',
            'impact_encoded',
            'urgency_encoded',
            'priority_encoded'
        ]

        df_features = df[feature_cols + ['incident_severity']].copy()
        df_features = df_features.fillna(0)

        print(f"  ✓ Extracted {len(df_features):,} incident feature vectors with {len(feature_cols)} features")

        return df_features


class MultiModalRealDetector:
    """Multi-modal detector for real datasets."""

    def __init__(self):
        self.telemetry_model = None
        self.incident_model = None
        self.fusion_model = None
        self.telemetry_scaler = StandardScaler()
        self.incident_scaler = StandardScaler()

    def train(self, X_telemetry, y_telemetry, X_incident, y_incident):
        """Train all models."""
        print("\n" + "="*80)
        print("TRAINING MULTI-MODAL SYSTEM")
        print("="*80)

        # Split data
        X_tel_train, X_tel_test, y_tel_train, y_tel_test = train_test_split(
            X_telemetry, y_telemetry, test_size=0.2, random_state=RANDOM_STATE, stratify=y_telemetry
        )

        X_inc_train, X_inc_test, y_inc_train, y_inc_test = train_test_split(
            X_incident, y_incident, test_size=0.2, random_state=RANDOM_STATE, stratify=y_incident
        )

        # Scale features
        X_tel_train_scaled = self.telemetry_scaler.fit_transform(X_tel_train)
        X_tel_test_scaled = self.telemetry_scaler.transform(X_tel_test)

        X_inc_train_scaled = self.incident_scaler.fit_transform(X_inc_train)
        X_inc_test_scaled = self.incident_scaler.transform(X_inc_test)

        # Train telemetry model
        print("\n[1/3] Training Telemetry Model (Machine Sensors)...")
        self.telemetry_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            class_weight='balanced',
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        self.telemetry_model.fit(X_tel_train_scaled, y_tel_train)

        y_tel_pred = self.telemetry_model.predict(X_tel_test_scaled)
        print("\n  Telemetry Model Performance:")
        print(classification_report(y_tel_test, y_tel_pred, target_names=['Normal', 'Failure']))

        # Train incident model
        print("\n[2/3] Training Incident Model (Event Log)...")
        self.incident_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=RANDOM_STATE
        )
        self.incident_model.fit(X_inc_train_scaled, y_inc_train)

        y_inc_pred = self.incident_model.predict(X_inc_test_scaled)
        print("\n  Incident Model Performance:")
        print(classification_report(y_inc_test, y_inc_pred, target_names=['Normal', 'Severe']))

        # Fusion model (train on combined predictions)
        print("\n[3/3] Training Fusion Model...")

        # For fusion, we need same-sized samples - use minimum size
        min_size = min(len(X_tel_train_scaled), len(X_inc_train_scaled))

        tel_pred_train = self.telemetry_model.predict_proba(X_tel_train_scaled[:min_size])[:, 1]
        inc_pred_train = self.incident_model.predict_proba(X_inc_train_scaled[:min_size])[:, 1]

        # Combine predictions
        X_fusion_train = np.column_stack([tel_pred_train, inc_pred_train])
        y_fusion_train = np.maximum(y_tel_train[:min_size], y_inc_train[:min_size])  # Union of failures

        self.fusion_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        self.fusion_model.fit(X_fusion_train, y_fusion_train)

        # Test fusion
        min_test_size = min(len(X_tel_test_scaled), len(X_inc_test_scaled))
        tel_pred_test = self.telemetry_model.predict_proba(X_tel_test_scaled[:min_test_size])[:, 1]
        inc_pred_test = self.incident_model.predict_proba(X_inc_test_scaled[:min_test_size])[:, 1]

        X_fusion_test = np.column_stack([tel_pred_test, inc_pred_test])
        y_fusion_test = np.maximum(y_tel_test[:min_test_size], y_inc_test[:min_test_size])

        y_fusion_pred = self.fusion_model.predict(X_fusion_test)

        print("\n  Fusion Model Performance:")
        print(classification_report(y_fusion_test, y_fusion_pred, target_names=['Normal', 'Failure']))

        return {
            'telemetry': (X_tel_test_scaled, y_tel_test, y_tel_pred),
            'incident': (X_inc_test_scaled, y_inc_test, y_inc_pred),
            'fusion': (X_fusion_test, y_fusion_test, y_fusion_pred)
        }


def analyze_machine_failures(df_machine):
    """Analyze failure patterns in machine data."""
    print("\n" + "="*80)
    print("MACHINE FAILURE ANALYSIS")
    print("="*80)

    df_failures = df_machine[df_machine['Failure_Status'] == 1]

    if len(df_failures) > 0:
        print(f"\nFailure Statistics:")
        print(f"  Total failures: {len(df_failures)}")
        print(f"  Affected machines: {df_failures['Machine_ID'].nunique()}")

        print(f"\n  Average conditions at failure:")
        print(f"    Temperature: {df_failures['Temperature'].mean():.1f}°C")
        print(f"    Pressure: {df_failures['Pressure'].mean():.1f} kPa")
        print(f"    Vibration: {df_failures['Vibration_Level'].mean():.2f} m/s²")
        print(f"    Humidity: {df_failures['Humidity'].mean():.1f}%")
        print(f"    Power: {df_failures['Power_Consumption'].mean():.1f} kW")

        # Compare with normal conditions
        df_normal = df_machine[df_machine['Failure_Status'] == 0]
        print(f"\n  Comparison (Failure vs Normal):")
        print(f"    Temperature: {df_failures['Temperature'].mean():.1f}°C vs {df_normal['Temperature'].mean():.1f}°C")
        print(f"    Vibration: {df_failures['Vibration_Level'].mean():.2f} vs {df_normal['Vibration_Level'].mean():.2f} m/s²")
        print(f"    Power: {df_failures['Power_Consumption'].mean():.1f} vs {df_normal['Power_Consumption'].mean():.1f} kW")


def plot_results(results):
    """Generate visualizations."""
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Performance comparison
    models = ['Telemetry\n(Machines)', 'Incident\n(Events)', 'Multi-Modal\nFusion']

    _, y_tel_test, y_tel_pred = results['telemetry']
    _, y_inc_test, y_inc_pred = results['incident']
    _, y_fus_test, y_fus_pred = results['fusion']

    accuracies = [
        (y_tel_pred == y_tel_test).mean(),
        (y_inc_pred == y_inc_test).mean(),
        (y_fus_pred == y_fus_test).mean()
    ]

    f1_scores = [
        precision_recall_fscore_support(y_tel_test, y_tel_pred, average='binary')[2],
        precision_recall_fscore_support(y_inc_test, y_inc_pred, average='binary')[2],
        precision_recall_fscore_support(y_fus_test, y_fus_pred, average='binary')[2]
    ]

    x = np.arange(len(models))
    width = 0.35

    axes[0, 0].bar(x - width/2, accuracies, width, label='Accuracy', color='skyblue')
    axes[0, 0].bar(x + width/2, f1_scores, width, label='F1-Score', color='lightcoral')
    axes[0, 0].set_ylabel('Score')
    axes[0, 0].set_title('Model Performance Comparison')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(models)
    axes[0, 0].legend()
    axes[0, 0].grid(axis='y', alpha=0.3)

    # Confusion matrices
    cms = [
        confusion_matrix(y_tel_test, y_tel_pred),
        confusion_matrix(y_inc_test, y_inc_pred),
        confusion_matrix(y_fus_test, y_fus_pred)
    ]

    for idx, (cm, title) in enumerate(zip(cms, models)):
        row, col = (idx // 3) + 1, idx % 3
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[row, col],
                   xticklabels=['Normal', 'Failure'],
                   yticklabels=['Normal', 'Failure'])
        axes[row, col].set_title(f'{title}\nConfusion Matrix')
        axes[row, col].set_ylabel('True')
        axes[row, col].set_xlabel('Predicted')

    plt.tight_layout()
    plot_path = PLOTS_DIR / 'real_datasets_results.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"✓ Results plot saved: {plot_path}")
    plt.close()


def main():
    """Main execution pipeline."""

    # Process machine telemetry
    machine_processor = MachineTelemetryProcessor()
    df_machine = machine_processor.load_and_process(MACHINE_DATA_PATH)
    df_machine_features = machine_processor.extract_features(df_machine)

    # Analyze failures
    analyze_machine_failures(df_machine)

    # Process incident log
    incident_processor = IncidentLogProcessor()
    df_incident = incident_processor.load_and_process(INCIDENT_DATA_PATH, sample_size=10000)
    df_incident_features = incident_processor.extract_features(df_incident)

    # Prepare training data
    X_telemetry = df_machine_features.drop(['failure_status'], axis=1)
    y_telemetry = df_machine_features['failure_status'].values

    X_incident = df_incident_features.drop(['incident_severity'], axis=1)
    y_incident = df_incident_features['incident_severity'].values

    print(f"\n✓ Prepared datasets:")
    print(f"  Machine telemetry: {X_telemetry.shape}")
    print(f"  Incident log: {X_incident.shape}")

    # Train multi-modal detector
    detector = MultiModalRealDetector()
    results = detector.train(X_telemetry, y_telemetry, X_incident, y_incident)

    # Plot results
    plot_results(results)

    # Save models
    print("\n" + "="*80)
    print("SAVING MODELS")
    print("="*80)

    with open(OUTPUT_DIR / 'real_multimodal_detector.pkl', 'wb') as f:
        pickle.dump(detector, f)
    print(f"✓ Multi-modal detector saved")

    # Save summary
    _, y_tel_test, y_tel_pred = results['telemetry']
    _, y_inc_test, y_inc_pred = results['incident']
    _, y_fus_test, y_fus_pred = results['fusion']

    summary = {
        'timestamp': datetime.now().isoformat(),
        'datasets': {
            'machine_telemetry': {
                'samples': len(df_machine),
                'machines': int(df_machine['Machine_ID'].nunique()),
                'failures': int(df_machine['Failure_Status'].sum())
            },
            'incident_log': {
                'samples': len(df_incident),
                'incidents': int(df_incident['number'].nunique()),
                'severe': int(df_incident['incident_severity'].sum())
            }
        },
        'performance': {
            'telemetry': {
                'accuracy': float((y_tel_pred == y_tel_test).mean()),
                'f1_score': float(precision_recall_fscore_support(y_tel_test, y_tel_pred, average='binary')[2])
            },
            'incident': {
                'accuracy': float((y_inc_pred == y_inc_test).mean()),
                'f1_score': float(precision_recall_fscore_support(y_inc_test, y_inc_pred, average='binary')[2])
            },
            'fusion': {
                'accuracy': float((y_fus_pred == y_fus_test).mean()),
                'f1_score': float(precision_recall_fscore_support(y_fus_test, y_fus_pred, average='binary')[2])
            }
        }
    }

    with open(OUTPUT_DIR / 'real_datasets_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Summary saved")

    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE")
    print("="*80)
    print(f"\nModels saved in: {OUTPUT_DIR.absolute()}")
    print(f"Plots saved in: {PLOTS_DIR.absolute()}")


if __name__ == '__main__':
    main()
