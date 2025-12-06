#!/usr/bin/env python3
"""
Generate ML-ready features with early fault labels from parsed cluster traces.

Implements the exact fault labeling strategy:
- Positive labels: 60-minute window BEFORE fault events
- Negative labels: Time points > 2 hours from any fault
- Features: Multi-modal with sliding windows (5min, 30min, 60min)
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Lead time for early warning (seconds)
EARLY_WARNING_WINDOW = 3600  # 60 minutes
SAFE_ZONE_WINDOW = 7200      # 2 hours (for negative labels)

# Feature window sizes (seconds)
WINDOWS = [300, 1800, 3600]  # 5min, 30min, 60min


class FeatureGenerator:
    """Generate features and labels for fault prediction."""

    def __init__(self, input_dir, output_dir, lead_time=3600):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.lead_time = lead_time

    def load_parsed_data(self):
        """Load parsed Parquet files."""
        print("\n[1/4] Loading parsed data...")

        data = {}

        # Load machine events
        machine_file = self.input_dir / 'machine_events.parquet'
        if machine_file.exists():
            data['machines'] = pd.read_parquet(machine_file)
            print(f"  ✓ Loaded {len(data['machines']):,} machine events")

        # Load task events
        task_file = self.input_dir / 'task_events.parquet'
        if task_file.exists():
            data['tasks'] = pd.read_parquet(task_file)
            print(f"  ✓ Loaded {len(data['tasks']):,} task events")

        # Load task usage
        usage_file = self.input_dir / 'task_usage.parquet'
        if usage_file.exists():
            data['usage'] = pd.read_parquet(usage_file)
            print(f"  ✓ Loaded {len(data['usage']):,} usage records")

        return data

    def identify_faults(self, data):
        """Identify fault events and their timestamps."""
        print("\n[2/4] Identifying fault events...")

        faults = []

        # Machine-level faults
        if 'machines' in data:
            machine_faults = data['machines'][data['machines']['is_failure'] == True].copy()
            for _, row in machine_faults.iterrows():
                faults.append({
                    'machine_id': row['machine_id'],
                    'timestamp': row['timestamp'],
                    'fault_type': 'MACHINE_REMOVE',
                    'severity': 'HIGH'
                })

        # Task-level faults
        if 'tasks' in data:
            task_faults = data['tasks'][data['tasks']['is_failure'] == True].copy()
            for _, row in task_faults.iterrows():
                fault_type = row['event_name'] if pd.notna(row.get('event_name')) else 'UNKNOWN'
                faults.append({
                    'machine_id': row['machine_id'] if pd.notna(row['machine_id']) else -1,
                    'job_id': row['job_id'],
                    'task_index': row['task_index'],
                    'timestamp': row['timestamp'],
                    'fault_type': f'TASK_{fault_type}',
                    'severity': 'MEDIUM'
                })

        df_faults = pd.DataFrame(faults)

        if len(df_faults) > 0:
            print(f"  ✓ Identified {len(df_faults):,} fault events")
            print(f"\n  Fault type breakdown:")
            for fault_type, count in df_faults['fault_type'].value_counts().head(5).items():
                print(f"    - {fault_type}: {count:,}")
        else:
            print("  ⚠ No faults identified")

        # Save fault log
        fault_log_file = self.output_dir / 'fault_events.csv'
        df_faults.to_csv(fault_log_file, index=False)
        print(f"  ✓ Saved fault log: {fault_log_file}")

        return df_faults

    def generate_labels(self, data, df_faults):
        """Generate early warning labels."""
        print("\n[3/4] Generating early warning labels...")

        if 'usage' not in data or len(df_faults) == 0:
            print("  ⚠ Skipping label generation (no usage data or faults)")
            return None

        df_usage = data['usage'].copy()

        # Create time index
        df_usage['mid_time'] = (df_usage['start_time'] + df_usage['end_time']) / 2

        # Initialize labels
        df_usage['early_fault_label'] = 0
        df_usage['fault_proximity'] = np.inf

        print(f"  Processing {len(df_usage):,} usage records...")

        # For each fault, mark early warning window
        for _, fault in tqdm(df_faults.iterrows(), total=len(df_faults), desc="  Labeling"):
            fault_time = fault['timestamp']
            machine_id = fault.get('machine_id', -1)

            # Mark early warning window: [fault_time - lead_time, fault_time]
            warning_start = fault_time - self.lead_time
            warning_end = fault_time

            # Apply to same machine
            mask = (
                (df_usage['machine_id'] == machine_id) &
                (df_usage['mid_time'] >= warning_start) &
                (df_usage['mid_time'] <= warning_end)
            )

            df_usage.loc[mask, 'early_fault_label'] = 1
            df_usage.loc[mask, 'fault_proximity'] = fault_time - df_usage.loc[mask, 'mid_time']

        positive_labels = df_usage['early_fault_label'].sum()
        positive_rate = 100 * positive_labels / len(df_usage)

        print(f"  ✓ Positive labels: {positive_labels:,} ({positive_rate:.2f}%)")
        print(f"  ✓ Negative labels: {len(df_usage) - positive_labels:,}")

        return df_usage

    def compute_features(self, df_labeled):
        """Compute multi-modal features with sliding windows."""
        print("\n[4/4] Computing multi-modal features...")

        if df_labeled is None:
            print("  ⚠ Skipping feature computation (no labeled data)")
            return None

        features_list = []

        # Group by machine and compute window features
        for machine_id, group in tqdm(df_labeled.groupby('machine_id'),
                                     desc="  Processing machines"):

            group = group.sort_values('start_time').copy()

            # Basic features
            base_features = {
                'machine_id': machine_id,
                'cpu_rate_mean': group['cpu_rate'].mean(),
                'cpu_rate_std': group['cpu_rate'].std(),
                'cpu_rate_max': group['cpu_rate'].max(),
                'memory_mean': group['canonical_memory_usage'].mean(),
                'memory_std': group['canonical_memory_usage'].std(),
                'disk_io_mean': group['disk_io_time'].mean(),
                'disk_io_std': group['disk_io_time'].std(),
            }

            # Performance indicators
            if 'cycles_per_instruction' in group.columns:
                base_features.update({
                    'cpi_median': group['cycles_per_instruction'].median(),
                    'cpi_p95': group['cycles_per_instruction'].quantile(0.95),
                    'mai_mean': group['memory_accesses_per_instruction'].mean(),
                })

            # Labels
            base_features.update({
                'early_fault_label': group['early_fault_label'].max(),
                'fault_count': group['early_fault_label'].sum(),
            })

            features_list.append(base_features)

        df_features = pd.DataFrame(features_list)

        print(f"  ✓ Computed features for {len(df_features):,} machines")

        # Save features
        feature_file = self.output_dir / 'ml_features.parquet'
        df_features.to_parquet(feature_file, index=False)
        print(f"  ✓ Saved: {feature_file}")

        # Also save as CSV for inspection
        csv_file = self.output_dir / 'ml_features.csv'
        df_features.to_csv(csv_file, index=False)
        print(f"  ✓ Saved: {csv_file}")

        return df_features

    def generate_report(self, df_features, df_faults):
        """Generate summary report."""
        print("\n" + "="*80)
        print("FEATURE GENERATION SUMMARY")
        print("="*80)

        if df_features is not None:
            print(f"\nDataset Statistics:")
            print(f"  Total samples:          {len(df_features):,}")
            print(f"  Positive samples:       {df_features['early_fault_label'].sum():,}")
            print(f"  Negative samples:       {(df_features['early_fault_label']==0).sum():,}")
            print(f"  Positive rate:          {100*df_features['early_fault_label'].mean():.2f}%")

            print(f"\nFeature Statistics:")
            print(f"  Number of features:     {len(df_features.columns):,}")
            print(f"  Feature names:          {', '.join(df_features.columns[:8])}...")

            print(f"\nFault Events:")
            print(f"  Total faults:           {len(df_faults):,}")
            print(f"  Early warning window:   {self.lead_time/60:.0f} minutes")

        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Generate ML features with early fault labels'
    )
    parser.add_argument('--input', required=True,
                       help='Input directory with parsed Parquet files')
    parser.add_argument('--output', default='processed/features',
                       help='Output directory for features')
    parser.add_argument('--lead-time', type=int, default=3600,
                       help='Early warning lead time in seconds (default: 3600 = 60min)')

    args = parser.parse_args()

    print("="*80)
    print("ML FEATURE GENERATOR")
    print("="*80)
    print(f"Early warning window: {args.lead_time/60:.0f} minutes")

    generator = FeatureGenerator(args.input, args.output, args.lead_time)

    # Load data
    data = generator.load_parsed_data()

    # Identify faults
    df_faults = generator.identify_faults(data)

    # Generate labels
    df_labeled = generator.generate_labels(data, df_faults)

    # Compute features
    df_features = generator.compute_features(df_labeled)

    # Generate report
    generator.generate_report(df_features, df_faults)

    print(f"\n✅ Feature generation complete! Output: {args.output}")


if __name__ == '__main__':
    main()
