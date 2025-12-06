#!/usr/bin/env python3
"""
Generate Multi-Modal Dataset: Telemetry + Logs
Creates 1000+ samples with synchronized telemetry metrics and HDFS-style log sequences

This dataset simulates realistic scenarios where both telemetry signals and
system logs are available for fault detection.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime, timedelta

# Configuration
NUM_HOSTS = 20
DURATION = 3600  # 1 hour in seconds
SAMPLE_INTERVAL = 5  # Sample every 5 seconds
OUTPUT_DIR = Path("datasets/multimodal")
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

# Fault scenarios with telemetry signatures and log patterns
FAULT_SCENARIOS = {
    'DISK_FAILURE': {
        'probability': 0.15,
        'telemetry': {
            'disk_io_increase': 0.8,  # 80% increase
            'temperature_increase': 15,  # +15°C
            'cpu_increase': 0.3
        },
        'log_sequence': [
            'SERVICESTART', 'DATANODE_REGISTER', 'BLOCKRECEIVED',
            'TRANSFER', 'ERROR_DISK_FAILURE', 'RECOVERBLOCK', 'RESTART'
        ],
        'early_warning_time': 300,  # 5 minutes before failure
        'duration': 120
    },
    'IO_EXCEPTION': {
        'probability': 0.12,
        'telemetry': {
            'disk_io_increase': 0.5,
            'temperature_increase': 8,
            'cpu_increase': 0.2
        },
        'log_sequence': [
            'SERVICESTART', 'DATANODE_REGISTER', 'BLOCKRECEIVED',
            'TRANSFER', 'ERROR_IO_EXCEPTION', 'RESTART', 'RECOVERBLOCK'
        ],
        'early_warning_time': 240,
        'duration': 90
    },
    'NETWORK_TIMEOUT': {
        'probability': 0.10,
        'telemetry': {
            'network_latency_increase': 10.0,  # 10x increase
            'cpu_increase': 0.15,
            'packet_loss': 0.25
        },
        'log_sequence': [
            'SERVICESTART', 'DATANODE_REGISTER', 'BLOCKRECEIVED',
            'TRANSFER', 'ERROR_NETWORK_TIMEOUT', 'RETRY', 'RETRY', 'REPLICATION_COMPLETED'
        ],
        'early_warning_time': 180,
        'duration': 60
    },
    'MEMORY_LEAK': {
        'probability': 0.08,
        'telemetry': {
            'memory_increase_rate': 0.05,  # 5% per minute
            'cpu_increase': 0.1,
            'temperature_increase': 10
        },
        'log_sequence': [
            'SERVICESTART', 'DATANODE_REGISTER', 'BLOCKRECEIVED',
            'TRANSFER', 'ERROR_LEASE_EXPIRED', 'RECOVERBLOCK', 'ERROR_RESTART', 'RESTART'
        ],
        'early_warning_time': 420,  # 7 minutes (memory leaks are slow)
        'duration': 180
    },
    'CHECKSUM_ERROR': {
        'probability': 0.10,
        'telemetry': {
            'disk_io_increase': 0.4,
            'cpu_increase': 0.25,
            'error_rate_increase': 10.0
        },
        'log_sequence': [
            'SERVICESTART', 'DATANODE_REGISTER', 'BLOCKRECEIVED',
            'TRANSFER', 'ERROR_CHECKSUM_MISMATCH', 'RECOVERBLOCK', 'REPLICATION_COMPLETED'
        ],
        'early_warning_time': 150,
        'duration': 75
    }
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_baseline_telemetry(host_id, timestamp):
    """Generate normal baseline telemetry."""
    # Vary baseline by host to simulate heterogeneity
    host_factor = 1.0 + (host_id % 5) * 0.1

    return {
        'timestamp': timestamp,
        'host_id': host_id,
        'cpu_percent': np.clip(np.random.normal(40 * host_factor, 10), 5, 95),
        'memory_percent': np.clip(np.random.normal(60 * host_factor, 8), 10, 90),
        'disk_io_percent': np.clip(np.random.normal(30, 15), 0, 100),
        'network_in_mbps': np.clip(np.random.normal(50, 20), 0, 1000),
        'network_out_mbps': np.clip(np.random.normal(45, 18), 0, 1000),
        'temperature_celsius': np.clip(np.random.normal(55 + host_id % 3, 5), 30, 85),
        'power_watts': np.clip(np.random.normal(200 + host_id * 5, 20), 50, 500),
        'network_latency_ms': np.clip(np.random.exponential(5), 0.1, 100),
        'packet_loss_percent': np.clip(np.random.exponential(0.5), 0, 10),
        'error_count': np.random.poisson(0.5)
    }


def apply_fault_telemetry(baseline, fault_type, progress):
    """Apply fault signature to telemetry (progress: 0.0 to 1.0)."""
    telemetry = baseline.copy()
    signature = FAULT_SCENARIOS[fault_type]['telemetry']

    # Gradual degradation
    factor = progress ** 0.5  # Square root for gradual onset

    if 'disk_io_increase' in signature:
        telemetry['disk_io_percent'] *= (1 + signature['disk_io_increase'] * factor)
        telemetry['disk_io_percent'] = np.clip(telemetry['disk_io_percent'], 0, 100)

    if 'temperature_increase' in signature:
        telemetry['temperature_celsius'] += signature['temperature_increase'] * factor
        telemetry['temperature_celsius'] = np.clip(telemetry['temperature_celsius'], 30, 95)

    if 'cpu_increase' in signature:
        telemetry['cpu_percent'] += signature['cpu_increase'] * 100 * factor
        telemetry['cpu_percent'] = np.clip(telemetry['cpu_percent'], 0, 100)

    if 'memory_increase_rate' in signature:
        # Memory leak: linear increase over time
        telemetry['memory_percent'] += signature['memory_increase_rate'] * 100 * progress * 10
        telemetry['memory_percent'] = np.clip(telemetry['memory_percent'], 0, 100)

    if 'network_latency_increase' in signature:
        telemetry['network_latency_ms'] *= (1 + signature['network_latency_increase'] * factor)

    if 'packet_loss' in signature:
        telemetry['packet_loss_percent'] += signature['packet_loss'] * 100 * factor
        telemetry['packet_loss_percent'] = np.clip(telemetry['packet_loss_percent'], 0, 100)

    if 'error_rate_increase' in signature:
        telemetry['error_count'] += int(signature['error_rate_increase'] * factor * np.random.poisson(2))

    return telemetry


def generate_log_sequence(fault_type=None):
    """Generate log sequence (normal or with fault)."""
    if fault_type is None:
        # Normal sequence
        sequences = [
            'SERVICESTART, DATANODE_REGISTER, BLOCKRECEIVED, TRANSFER, BLOCKREPORT, REPLICATION_COMPLETED',
            'SERVICESTART, DATANODE_REGISTER, BLOCKRECEIVED, TRANSFER, BLOCKRECEIVED, TRANSFER, REPLICATION_COMPLETED',
            'SERVICESTART, DATANODE_REGISTER, BLOCKRECEIVED, TRANSFER, BLOCKREPORT, BLOCKREPORT, REPLICATION_COMPLETED'
        ]
        return np.random.choice(sequences)
    else:
        # Fault sequence
        return ', '.join(FAULT_SCENARIOS[fault_type]['log_sequence'])


def generate_multimodal_dataset():
    """Generate complete multi-modal dataset."""
    print("="*80)
    print("MULTI-MODAL DATASET GENERATION")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Hosts: {NUM_HOSTS}")
    print(f"  Duration: {DURATION}s ({DURATION/60:.1f} minutes)")
    print(f"  Sample interval: {SAMPLE_INTERVAL}s")
    print(f"  Expected samples: {NUM_HOSTS * (DURATION // SAMPLE_INTERVAL)}")

    # Track faults for each host
    host_faults = {}
    for host_id in range(NUM_HOSTS):
        host_faults[host_id] = []

        # Randomly inject faults
        for fault_type, config in FAULT_SCENARIOS.items():
            if np.random.random() < config['probability']:
                # Random start time (leaving room for early warning)
                start_time = np.random.randint(
                    config['early_warning_time'] + 60,
                    DURATION - config['duration'] - 60
                )
                host_faults[host_id].append({
                    'type': fault_type,
                    'start_time': start_time,
                    'end_time': start_time + config['duration'],
                    'early_warning_start': start_time - config['early_warning_time']
                })

    # Generate telemetry data
    telemetry_records = []
    log_sequences = []
    fault_events = []

    print("\nGenerating telemetry and logs...")

    for host_id in range(NUM_HOSTS):
        for t in range(0, DURATION, SAMPLE_INTERVAL):
            # Check if in fault period
            active_fault = None
            fault_progress = 0.0
            in_early_warning = False

            for fault in host_faults[host_id]:
                if fault['early_warning_start'] <= t <= fault['end_time']:
                    active_fault = fault['type']

                    if t < fault['start_time']:
                        # Early warning period
                        in_early_warning = True
                        warning_duration = fault['start_time'] - fault['early_warning_start']
                        fault_progress = (t - fault['early_warning_start']) / warning_duration * 0.5
                    else:
                        # Actual fault period
                        in_early_warning = False
                        fault_duration = fault['end_time'] - fault['start_time']
                        fault_progress = 0.5 + (t - fault['start_time']) / fault_duration * 0.5
                    break

            # Generate telemetry
            baseline = generate_baseline_telemetry(host_id, t)

            if active_fault:
                telemetry = apply_fault_telemetry(baseline, active_fault, fault_progress)
                telemetry['fault_active'] = not in_early_warning
                telemetry['fault_type'] = active_fault
                telemetry['early_warning'] = in_early_warning
            else:
                telemetry = baseline
                telemetry['fault_active'] = False
                telemetry['fault_type'] = 'NONE'
                telemetry['early_warning'] = False

            telemetry_records.append(telemetry)

        # Generate log sequences for this host
        for fault in host_faults[host_id]:
            log_sequences.append({
                'host_id': host_id,
                'timestamp': fault['start_time'],
                'event_sequence': generate_log_sequence(fault['type']),
                'label': 'Anomaly',
                'fault_type': fault['type']
            })

            fault_events.append({
                'host_id': host_id,
                'fault_type': fault['type'],
                'start_time': fault['start_time'],
                'end_time': fault['end_time'],
                'early_warning_start': fault['early_warning_start'],
                'early_warning_duration': fault['start_time'] - fault['early_warning_start']
            })

        # Add normal log sequences (10-20 per host)
        num_normal_logs = np.random.randint(10, 21)
        for _ in range(num_normal_logs):
            normal_time = np.random.randint(0, DURATION)
            # Make sure it's not during a fault
            is_fault_time = any(
                f['start_time'] <= normal_time <= f['end_time']
                for f in host_faults[host_id]
            )
            if not is_fault_time:
                log_sequences.append({
                    'host_id': host_id,
                    'timestamp': normal_time,
                    'event_sequence': generate_log_sequence(None),
                    'label': 'Normal',
                    'fault_type': 'NONE'
                })

    # Create DataFrames
    df_telemetry = pd.DataFrame(telemetry_records)
    df_logs = pd.DataFrame(log_sequences)
    df_faults = pd.DataFrame(fault_events)

    # Statistics
    total_samples = len(df_telemetry)
    fault_samples = df_telemetry['fault_active'].sum()
    early_warning_samples = df_telemetry['early_warning'].sum()
    normal_samples = total_samples - fault_samples - early_warning_samples

    print(f"\n✓ Generated {total_samples:,} telemetry samples")
    print(f"  Normal: {normal_samples:,} ({normal_samples/total_samples*100:.1f}%)")
    print(f"  Early warning: {early_warning_samples:,} ({early_warning_samples/total_samples*100:.1f}%)")
    print(f"  Fault active: {fault_samples:,} ({fault_samples/total_samples*100:.1f}%)")

    print(f"\n✓ Generated {len(df_logs):,} log sequences")
    print(f"  Normal: {(df_logs['label'] == 'Normal').sum():,}")
    print(f"  Anomaly: {(df_logs['label'] == 'Anomaly').sum():,}")

    print(f"\n✓ Injected {len(df_faults)} fault events")
    fault_type_counts = df_faults['fault_type'].value_counts()
    for fault_type, count in fault_type_counts.items():
        print(f"  {fault_type}: {count}")

    # Save datasets
    telemetry_file = OUTPUT_DIR / 'telemetry_multimodal.csv'
    logs_file = OUTPUT_DIR / 'logs_multimodal.csv'
    faults_file = OUTPUT_DIR / 'fault_events_multimodal.json'

    df_telemetry.to_csv(telemetry_file, index=False)
    df_logs.to_csv(logs_file, index=False)
    df_faults.to_json(faults_file, orient='records', indent=2)

    print(f"\n✓ Saved telemetry to: {telemetry_file}")
    print(f"✓ Saved logs to: {logs_file}")
    print(f"✓ Saved fault events to: {faults_file}")

    # Generate metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'configuration': {
            'num_hosts': NUM_HOSTS,
            'duration_seconds': DURATION,
            'sample_interval': SAMPLE_INTERVAL,
            'random_seed': RANDOM_SEED
        },
        'statistics': {
            'total_telemetry_samples': int(total_samples),
            'normal_samples': int(normal_samples),
            'early_warning_samples': int(early_warning_samples),
            'fault_samples': int(fault_samples),
            'total_log_sequences': int(len(df_logs)),
            'normal_logs': int((df_logs['label'] == 'Normal').sum()),
            'anomaly_logs': int((df_logs['label'] == 'Anomaly').sum()),
            'fault_events': int(len(df_faults))
        },
        'fault_scenarios': {
            k: {
                'probability': v['probability'],
                'early_warning_time': v['early_warning_time'],
                'duration': v['duration']
            }
            for k, v in FAULT_SCENARIOS.items()
        }
    }

    metadata_file = OUTPUT_DIR / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Saved metadata to: {metadata_file}")

    print("\n" + "="*80)
    print("✅ DATASET GENERATION COMPLETE")
    print("="*80)

    return df_telemetry, df_logs, df_faults


if __name__ == '__main__':
    generate_multimodal_dataset()
