#!/usr/bin/env python3
"""
Generate sample telemetry data for fault detection research.
Simulates a datacenter with hosts and injected faults.
"""

import numpy as np
import pandas as pd
from datetime import datetime

# Simulation parameters
DURATION = 600  # 10 minutes
INTERVAL = 1.0  # 1 second
FAULT_START = 300  # Faults start at 5 minutes
NUM_HOSTS = 5

# Create timestamps
timestamps = np.arange(0, DURATION, INTERVAL)

# Initialize data
data = []

print("Generating sample telemetry data...")
print(f"Duration: {DURATION}s, Hosts: {NUM_HOSTS}, Interval: {INTERVAL}s")

for t in timestamps:
    for host_id in range(NUM_HOSTS):
        # Determine if this host has a fault at this time
        fault_active = False
        fault_type = "NONE"

        # Inject faults at different times for different hosts
        if host_id == 0 and t >= FAULT_START and t < FAULT_START + 150:
            fault_active = True
            fault_type = "FAN_FAILURE"
        elif host_id == 2 and t >= FAULT_START + 50 and t < FAULT_START + 200:
            fault_active = True
            fault_type = "THERMAL_ISSUE"
        elif host_id == 3 and t >= FAULT_START + 100 and t < FAULT_START + 180:
            fault_active = True
            fault_type = "POWER_SUPPLY_DEGRADATION"

        # Base metrics (with some sinusoidal variation)
        base_cpu = 0.4 + 0.2 * np.sin(t / 60) + np.random.normal(0, 0.05)
        base_cpu = max(0.1, min(0.95, base_cpu))

        # Apply fault effects
        if fault_active:
            if fault_type == "FAN_FAILURE":
                # Fan failure causes temperature to rise, CPU might throttle
                temp_increase = 20
                cpu_modifier = 1.2
                power_modifier = 1.15
                vibration_modifier = 0.7  # Fan not spinning
            elif fault_type == "THERMAL_ISSUE":
                temp_increase = 25
                cpu_modifier = 1.15
                power_modifier = 1.1
                vibration_modifier = 1.3
            elif fault_type == "POWER_SUPPLY_DEGRADATION":
                temp_increase = 10
                cpu_modifier = 1.05
                power_modifier = 1.25
                vibration_modifier = 1.1
            else:
                temp_increase = 0
                cpu_modifier = 1.0
                power_modifier = 1.0
                vibration_modifier = 1.0
        else:
            temp_increase = 0
            cpu_modifier = 1.0
            power_modifier = 1.0
            vibration_modifier = 1.0

        # Calculate metrics
        cpu_util = min(0.99, base_cpu * cpu_modifier)
        cpu_allocated_mips = cpu_util * 8000  # 8000 MIPS per host
        cpu_available_mips = 8000 - cpu_allocated_mips

        base_power = 200 + cpu_util * 200  # 200W base + up to 200W for CPU
        power_watts = base_power * power_modifier + np.random.normal(0, 5)

        base_temp = 35 + cpu_util * 30  # 35°C base + up to 30°C for CPU load
        temp_celsius = base_temp + temp_increase + np.random.normal(0, 2)
        temp_cpu_sensor = temp_celsius + np.random.normal(0, 1)
        temp_ambient = 25 + np.random.normal(0, 0.5)

        base_vibration = 0.5 + cpu_util * 0.3
        vibration_magnitude = base_vibration * vibration_modifier + np.random.normal(0, 0.1)
        vibration_frequency = 50 + cpu_util * 30 + np.random.normal(0, 2)

        ram_util = 0.5 + np.random.normal(0, 0.1)
        ram_util = max(0.2, min(0.9, ram_util))
        ram_available_mb = 32000 * (1 - ram_util)

        storage_util = 0.3 + np.random.normal(0, 0.05)
        storage_util = max(0.1, min(0.8, storage_util))
        storage_available_mb = 1000000 * (1 - storage_util)

        # Create record
        record = {
            'timestamp': t,
            'component_id': host_id,
            'component_type': 'HOST',
            'cpu_utilization': cpu_util,
            'cpu_allocated_mips': cpu_allocated_mips,
            'cpu_available_mips': cpu_available_mips,
            'power_consumption_watts': power_watts,
            'temperature_celsius': temp_celsius,
            'temperature_cpu_sensor': temp_cpu_sensor,
            'temperature_ambient': temp_ambient,
            'vibration_magnitude': vibration_magnitude,
            'vibration_frequency_hz': vibration_frequency,
            'ram_utilization': ram_util,
            'ram_available_mb': ram_available_mb,
            'storage_utilization': storage_util,
            'storage_available_mb': storage_available_mb,
            'bw_utilization': 0.0,
            'status': 'ACTIVE',
            'failed': 'true' if fault_active else 'false',
            'host_id': host_id,
            'vms_count': 10,
            'cloudlets_count': 0,
            'fault_type': fault_type
        }

        data.append(record)

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
output_path = 'output/telemetry/telemetry.csv'
df.to_csv(output_path, index=False)

print(f"\n✓ Generated {len(df)} telemetry records")
print(f"✓ Time range: {df['timestamp'].min():.1f}s to {df['timestamp'].max():.1f}s")
print(f"✓ Hosts: {df['component_id'].nunique()}")
print(f"✓ Fault records: {df[df['failed'] == 'true'].shape[0]} ({100*df[df['failed'] == 'true'].shape[0]/len(df):.1f}%)")
print(f"✓ Saved to: {output_path}")

# Print fault summary
print("\nFault Summary:")
fault_df = df[df['failed'] == 'true']
if len(fault_df) > 0:
    for fault_type in fault_df['fault_type'].unique():
        if fault_type != 'NONE':
            count = len(fault_df[fault_df['fault_type'] == fault_type])
            hosts = fault_df[fault_df['fault_type'] == fault_type]['host_id'].unique()
            print(f"  - {fault_type}: {count} records on hosts {list(hosts)}")
